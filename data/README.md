# Data

Copies of the provided datasets, placed here to match the Submission Guide's required
repository structure (`data/` — "small sample data only"; all four files here are 40-450KB).

The working system and all documentation reference the original path, `05_Datasets/`, which
mirrors the capstone pack's own folder numbering and is kept as the canonical location — this
folder is a copy for structural compliance, not a second source of truth. If the two ever
diverge, `05_Datasets/` is correct.

None of these are the hidden grading set. `evaluation/harness.py` takes `--input`/`--output` as
CLI arguments and never hardcodes a dataset path, exactly so it can be pointed at a file it has
never seen, per the Build Specification.
