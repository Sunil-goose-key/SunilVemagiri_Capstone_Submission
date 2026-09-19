from evaluation.ground_truth_check import judge, summarize


def test_judge_returns_empty_when_nothing_to_check():
    result = judge("some answer", [], [])
    assert result == {"mentions_covered": [], "mentions_missed": [], "claims_violated": [], "notes": "nothing to check"}


def test_judge_degrades_on_provider_failure(monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr("evaluation.ground_truth_check.chat", boom)
    result = judge("some answer", ["point a"], ["claim b"])
    assert result["judge_error"] is True
    # Failure must not silently count as "covered" or "cleared" -- degrade toward the more
    # conservative (worse-looking, not better-looking) outcome
    assert result["mentions_missed"] == ["point a"]
    assert result["claims_violated"] == []


def test_summarize_computes_violation_rate_and_coverage():
    results = [
        {
            "ticket_id": "T-1", "can_answer": True, "expected_doc_ids": ["DOC-1"],
            "cited_doc_ids": ["DOC-1"], "citation_hit": True,
            "mentions_covered": ["a"], "mentions_missed": [], "claims_violated": [],
        },
        {
            "ticket_id": "T-2", "can_answer": True, "expected_doc_ids": ["DOC-2"],
            "cited_doc_ids": ["DOC-3"], "citation_hit": False,
            "mentions_covered": [], "mentions_missed": ["b"], "claims_violated": ["refund"],
        },
        {
            "ticket_id": "T-3", "can_answer": False, "expected_doc_ids": [],
            "cited_doc_ids": [], "citation_hit": None,
            "mentions_covered": [], "mentions_missed": [], "claims_violated": [],
        },
    ]
    summary = summarize(results)

    assert summary["volume"]["processed"] == 3
    assert summary["volume"]["answered"] == 2
    assert summary["must_mention_coverage"]["total_points"] == 2  # "a" + "b"
    assert summary["must_mention_coverage"]["covered"] == 1
    assert summary["must_mention_coverage"]["coverage_pct"] == 50.0
    assert summary["must_not_claim_safety"]["tickets_with_at_least_one_violation"] == 1
    assert summary["must_not_claim_safety"]["violation_rate_pct"] == 50.0  # 1 of 2 judged tickets
    assert summary["citation_accuracy_proxy"]["tickets_with_expected_doc_ids"] == 2
    assert summary["citation_accuracy_proxy"]["citation_hits"] == 1
    assert summary["citation_accuracy_proxy"]["hit_rate_pct"] == 50.0


def test_summarize_handles_zero_denominators_without_crashing():
    results = [
        {
            "ticket_id": "T-1", "can_answer": False, "expected_doc_ids": [],
            "cited_doc_ids": [], "citation_hit": None,
            "mentions_covered": [], "mentions_missed": [], "claims_violated": [],
        },
    ]
    summary = summarize(results)
    assert summary["must_mention_coverage"]["coverage_pct"] is None
    assert summary["must_not_claim_safety"]["violation_rate_pct"] is None
    assert summary["citation_accuracy_proxy"]["hit_rate_pct"] is None
