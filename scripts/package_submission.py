"""Assemble the final submission zip per Submission_Guide.docx's exact format.

Usage:
    python scripts/package_submission.py --name FirstnameLastname \
        --video path/to/video.mp4 --report path/to/report.pdf

Run this LAST -- after the video is recorded and the report is a finished PDF. This script
does not generate either; it only assembles what you point it at into the required structure:

    FirstnameLastname_Capstone_Submission.zip
        01_Video/FirstnameLastname_Capstone_Video.mp4
        02_Report/FirstnameLastname_Capstone_Report.pdf
        03_Workbooks/  (all 5 stage workbooks + effort log)
        04_Source_Code/  (the whole repo, minus .venv/storage/__pycache__/.git)

Before running, work through the Submission Guide's own 15-item final checklist by hand --
this script assembles the folder structure, it does not verify content quality, length, or
whether the video/report actually meet the stated requirements.
"""
from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

WORKBOOK_FILES = [
    "02_Stage_Workbooks/Stage_1_Discovery_Workbook_FILLED.md",
    "02_Stage_Workbooks/Stage_2_PRD_v1.md",
    "prompts/README.md",  # the prompt library / register
    "02_Stage_Workbooks/Stage_4_Sprint_Plan_v1.md",
    "02_Stage_Workbooks/Stage_5_PRD_Revision_Log_v1.md",
    "04_Submission/Effort_Log_v1.md",
]

# Directories/files never copied into 04_Source_Code
SOURCE_EXCLUDES = {".venv", "storage", "__pycache__", ".git", ".pytest_cache", "node_modules"}


def _copy_source_tree(dest: Path) -> None:
    def ignore(dir_path: str, names: list[str]) -> set[str]:
        return {n for n in names if n in SOURCE_EXCLUDES or n.endswith(".pyc")}

    shutil.copytree(ROOT, dest, ignore=ignore, dirs_exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="FirstnameLastname, no spaces, exactly as on your enrolment")
    parser.add_argument("--video", required=True, type=Path, help="Path to the finished .mp4")
    parser.add_argument("--report", required=True, type=Path, help="Path to the finished report .pdf")
    parser.add_argument("--out-dir", default=ROOT / "_submission_build", type=Path)
    args = parser.parse_args()

    if not args.video.exists():
        raise SystemExit(f"Video not found: {args.video}")
    if not args.report.exists():
        raise SystemExit(f"Report PDF not found: {args.report}")
    missing_workbooks = [w for w in WORKBOOK_FILES if not (ROOT / w).exists()]
    if missing_workbooks:
        raise SystemExit(f"Missing workbook file(s), fix before packaging: {missing_workbooks}")

    build = args.out_dir
    if build.exists():
        shutil.rmtree(build)
    build.mkdir(parents=True)

    (build / "01_Video").mkdir()
    shutil.copy2(args.video, build / "01_Video" / f"{args.name}_Capstone_Video.mp4")

    (build / "02_Report").mkdir()
    shutil.copy2(args.report, build / "02_Report" / f"{args.name}_Capstone_Report.pdf")

    workbooks_dir = build / "03_Workbooks"
    workbooks_dir.mkdir()
    for w in WORKBOOK_FILES:
        shutil.copy2(ROOT / w, workbooks_dir / Path(w).name)

    print("Copying source tree (this can take a moment)...")
    _copy_source_tree(build / "04_Source_Code")

    zip_path = ROOT / f"{args.name}_Capstone_Submission.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in build.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(build))

    print(f"\nBuilt: {zip_path}")
    print(f"Build directory (unzipped, for inspection): {build}")
    print("\nBefore you submit, work through the Submission Guide's 15-item final checklist by hand.")


if __name__ == "__main__":
    main()
