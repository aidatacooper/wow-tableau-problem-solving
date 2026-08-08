"""Create one iteration and extract data without copying the author workbook."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
import urllib.parse
import urllib.request
import zipfile
from datetime import date
from pathlib import Path


LAB_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = LAB_ROOT / "iterations" / "_template"
DATA_SUFFIXES = {
    ".hyper",
    ".tde",
    ".csv",
    ".txt",
    ".xls",
    ".xlsx",
    ".json",
    ".geojson",
    ".shp",
    ".shx",
    ".dbf",
    ".prj",
}
TABLEAU_URL_PATTERNS = (
    r"/app/profile/[^/]+/viz/([^/?#]+)/",
    r"/(?:views|vizhome)/([^/?#]+)/",
    r"#!/vizhome/([^/?#]+)/",
)
USER_AGENT = "Mozilla/5.0 (compatible; WoWTableauLab/1.0)"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tableau_workbook_name(url: str) -> str:
    for pattern in TABLEAU_URL_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return urllib.parse.unquote(match.group(1))
    raise ValueError(f"Unsupported Tableau Public workbook URL: {url}")


def download_workbook(url: str, target: Path) -> None:
    workbook = tableau_workbook_name(url)
    download_url = (
        "https://public.tableau.com/workbooks/"
        + urllib.parse.quote(workbook, safe="")
        + ".twb"
    )
    request = urllib.request.Request(download_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as output:
        shutil.copyfileobj(response, output)
    if not zipfile.is_zipfile(target):
        raise ValueError(f"Tableau Public did not return a packaged workbook: {url}")


def extract_data(source: Path, inputs: Path) -> list[dict[str, object]]:
    if not zipfile.is_zipfile(source):
        raise ValueError(f"Not a valid TWBX/ZIP archive: {source}")

    extracted: list[dict[str, object]] = []
    with zipfile.ZipFile(source) as archive:
        members = [
            item
            for item in archive.infolist()
            if not item.is_dir() and Path(item.filename).suffix.lower() in DATA_SUFFIXES
        ]
        if not members:
            raise ValueError(f"No packaged data file found in {source}")

        names = [Path(item.filename).name for item in members]
        if len(names) != len(set(names)):
            raise ValueError("The source contains duplicate data basenames")

        inputs.mkdir(parents=True, exist_ok=True)
        for member, name in zip(members, names):
            target = inputs / name
            with archive.open(member) as reader, target.open("wb") as writer:
                shutil.copyfileobj(reader, writer)
            extracted.append(
                {
                    "archive_path": member.filename,
                    "file": f"inputs/{name}",
                    "bytes": target.stat().st_size,
                    "sha256": sha256(target),
                }
            )
    return extracted


def replace_tokens(path: Path, values: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    for token, value in values.items():
        text = text.replace(token, value)
    path.write_text(text, encoding="utf-8")


def prepare_case(
    source: Path,
    iteration_id: str,
    case_id: str,
    post: str,
    iterations_root: Path | None = None,
    source_url: str | None = None,
) -> Path:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    root = iterations_root or LAB_ROOT / "iterations"
    target = root / iteration_id
    if target.exists():
        raise FileExistsError(f"Iteration already exists: {target}")

    shutil.copytree(TEMPLATE, target)
    try:
        values = {
            "__CASE_ID__": case_id,
            "__ITERATION_ID__": iteration_id,
            "__POST__": post,
        }
        replace_tokens(target / "case.yaml", values)
        replace_tokens(target / "analysis.md", values)

        data = extract_data(source, target / "inputs")
        lock = {
            "schema_version": "1.0.0",
            "prepared_on": date.today().isoformat(),
            "source_workbook": {
                "filename": source.name,
                "bytes": source.stat().st_size,
                "sha256": sha256(source),
                "url": source_url,
            },
            "extracted_data": data,
            "source_workbook_used_by_builder": False,
        }
        (target / "inputs" / "source-lock.json").write_text(
            json.dumps(lock, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        case_path = target / "case.yaml"
        case_text = case_path.read_text(encoding="utf-8")
        data_lines = "\n".join(f"    - {item['file']}" for item in data)
        case_text = case_text.replace("  data_files: []", f"  data_files:\n{data_lines}")
        case_path.write_text(case_text, encoding="utf-8")
    except Exception:
        shutil.rmtree(target)
        raise
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--source", type=Path)
    source_group.add_argument("--workbook-url")
    parser.add_argument("--iteration-id", required=True)
    parser.add_argument("--case-id", required=True)
    post_group = parser.add_mutually_exclusive_group(required=True)
    post_group.add_argument("--post")
    post_group.add_argument("--post-url")
    args = parser.parse_args()
    post = args.post or args.post_url
    if args.source:
        print(prepare_case(args.source, args.iteration_id, args.case_id, post))
        return
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / f"{tableau_workbook_name(args.workbook_url)}.twbx"
        download_workbook(args.workbook_url, source)
        print(
            prepare_case(
                source,
                args.iteration_id,
                args.case_id,
                post,
                source_url=args.workbook_url,
            )
        )


if __name__ == "__main__":
    main()
