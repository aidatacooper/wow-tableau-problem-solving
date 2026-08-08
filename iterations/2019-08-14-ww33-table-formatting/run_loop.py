"""Validate -> upload -> screenshot loop for the WW33 replication.

Run with system Python that has tableauserverclient / tableauhyperapi / requests.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ITERATION_DIR = Path(__file__).resolve().parent
REPO_ROOT = ITERATION_DIR.parents[4]
SRC = REPO_ROOT / "src"
sys.path.insert(0, str(SRC))

from cwtwb.validate.uploader import TableauUploader  # noqa: E402

ENV_PATH = REPO_ROOT / ".env"
TWB_PATH = ITERATION_DIR / "outputs" / "replicated-workbook.twb"
SUMMARY_HYPER = ITERATION_DIR / "inputs" / "Orders (Sample - Superstore).hyper"
EVIDENCE_DIR = ITERATION_DIR / "evidence"
import datetime as _dt
WORKBOOK_NAME = f"WW33_TableFormatting_FRESH_{_dt.datetime.now().strftime('%H%M%S%f')}"


def main() -> None:
    EVIDENCE_DIR.mkdir(exist_ok=True)
    up = TableauUploader(env_path=str(ENV_PATH))

    # 1) Validate (skip if endpoint missing)
    print("== VALIDATE ==")
    try:
        vr = up.validate(TWB_PATH, validation_level="semantic")
        (EVIDENCE_DIR / "validation.json").write_text(
            json.dumps(vr.__dict__, indent=2, default=str), encoding="utf-8")
        print(json.dumps(vr.__dict__, indent=2, default=str))
        if not vr.valid:
            print("VALIDATION FAILED -> continue anyway (just upload+screenshot)")
    except Exception as e:
        print(f"VALIDATE exception (continuing): {e}")

    # 2) Upload (package the summary hyper)
    print("== UPLOAD ==")
    ur = up.upload(TWB_PATH, data_path=str(SUMMARY_HYPER), name=WORKBOOK_NAME, overwrite=True)
    (EVIDENCE_DIR / "upload_result.json").write_text(
        json.dumps(ur.__dict__, indent=2, default=str), encoding="utf-8")
    print(json.dumps(ur.__dict__, indent=2, default=str))
    if not ur.success or not ur.workbook_id:
        print("UPLOAD FAILED -> stop")
        return

    # 3) Wait for Cloud render + screenshot the dashboard view
    print("== WAIT FOR RENDER ==")
    time.sleep(90)
    print("== SCREENSHOT ==")
    sr = up.screenshot(ur.workbook_id, output_dir=str(EVIDENCE_DIR),
                       view_index=0, view_name=None)
    (EVIDENCE_DIR / "screenshot_result.json").write_text(
        json.dumps(sr.__dict__, indent=2, default=str), encoding="utf-8")
    print(json.dumps(sr.__dict__, indent=2, default=str))
    if sr.success and sr.path:
        stamp = "iteration_latest_20260803o.png"
        shutil.copy(sr.path, EVIDENCE_DIR / stamp)
        print("COPIED ->", stamp)


if __name__ == "__main__":
    main()
