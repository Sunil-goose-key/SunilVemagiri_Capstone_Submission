"""Retrieval over the documentation corpus (A4, FR-05).

Returns ranked passages with resolvable doc_ids, applies a relevance floor, and returns
nothing rather than something irrelevant.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src import config
from src.models import RetrievedPassage

logger = logging.getLogger(__name__)

# The installed posthog (7.x) removed the old positional capture(distinct_id, event, props)
# signature chromadb 0.4.24 still calls internally for its own anonymous usage-analytics ping,
# so that call raises TypeError every time and chromadb logs it as an error ("Failed to send
# telemetry event..."). This is unrelated to retrieval correctness -- passing
# client_settings=Settings(anonymized_telemetry=False) does NOT prevent it (the crash happens
# at argument-binding time, before chromadb's own "should I even try" check runs), and was
# tried and reverted here because it also has a side effect: langchain's Chroma wrapper only
# sets is_persistent=True on its auto-built Settings when no client_settings is passed, so
# supplying our own silently downgraded the store to in-memory and made every query return
# nothing. Raising this specific chromadb logger's level is what actually and safely silences
# the warning; it touches only this one chromadb-internal logger, not this module's own
# `logger`, so a real retrieval failure (logged via `logger.exception(...)` in `retrieve()`
# below) still surfaces normally.
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)

_embeddings = None


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
    return _embeddings


def build_store(
    documentation_path: str = "05_Datasets/documentation.json",
    persist_directory: str | None = None,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> Chroma:
    """Embed the documentation corpus into Chroma. Chunk size/overlap are a recorded design
    decision (see docs/architecture.md), not a default left unexamined.
    """
    persist_directory = persist_directory or config.CHROMA_PATH
    with open(documentation_path, "r", encoding="utf-8") as f:
        documents = json.load(f)

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    texts, metadatas = [], []
    for doc in documents:
        for chunk in splitter.split_text(doc.get("content", "")):
            texts.append(chunk)
            metadatas.append(
                {
                    "doc_id": doc.get("doc_id", ""),
                    "title": doc.get("title", ""),
                    "last_reviewed_days_ago": doc.get("last_reviewed_days_ago", -1),
                }
            )

    Path(persist_directory).mkdir(parents=True, exist_ok=True)
    store = Chroma.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=_get_embeddings(),
        persist_directory=persist_directory,
    )
    # chromadb >=0.4.x auto-persists; an explicit .persist() call is deprecated noise here.
    logger.info("stored %s passages from %s articles", len(texts), len(documents))
    return store


def load_store(persist_directory: str | None = None) -> Chroma:
    persist_directory = persist_directory or config.CHROMA_PATH
    return Chroma(persist_directory=persist_directory, embedding_function=_get_embeddings())


def retrieve(
    query: str,
    store: Chroma | None = None,
    top_k: int | None = None,
    relevance_floor: float | None = None,
) -> list[RetrievedPassage]:
    """Return ranked passages, or an empty list if nothing clears the relevance floor.

    Returning nothing is a valid, expected outcome (Build Spec: "return nothing rather than
    something irrelevant") -- callers must treat an empty list as "not answerable from docs",
    not as an error.
    """
    store = store or load_store()
    top_k = top_k or config.RETRIEVAL_TOP_K
    floor = relevance_floor if relevance_floor is not None else config.RETRIEVAL_RELEVANCE_FLOOR

    try:
        results = store.similarity_search_with_relevance_scores(query, k=top_k)
    except Exception:
        logger.exception("retrieval failed; degrading to empty result set (A11)")
        return []

    passages = []
    for doc, score in results:
        if score < floor:
            continue
        passages.append(
            RetrievedPassage(
                doc_id=doc.metadata.get("doc_id", ""),
                title=doc.metadata.get("title", ""),
                text=doc.page_content,
                score=float(score),
                last_reviewed_days_ago=doc.metadata.get("last_reviewed_days_ago"),
            )
        )
    return passages


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build_store()
    else:
        # Day 2 checkpoint: query a known question, confirm the right passage returns
        q = sys.argv[1] if len(sys.argv) > 1 else "how do I resolve invalid credential errors on login"
        for p in retrieve(q):
            print(f"{p.score:.3f}  {p.doc_id}  {p.title}")
