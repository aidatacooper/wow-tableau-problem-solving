"""Generate/check the active catalogue from case.yaml, without building workbooks.

Source locks and historical evidence are immutable. Only case.yaml is editable;
usage/case-index.json and consumed-cases.json are deterministic derived views.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

LAB_ROOT = Path(__file__).resolve().parents[1]
FOLDER = re.compile(r"^(\d{4}-\d{2}-\d{2})-ww(\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)$")
PRIMARY = "outputs/replicated-workbook.twbx"
# These are the only grandfathered identity-only contracts. New cases use v1.1.
LEGACY_ITERATIONS = frozenset({
    "2019-07-18-ww29-high-orders", "2019-07-25-ww30-navigation-kpi",
    "2019-08-04-ww31-hub-spoke-map", "2019-08-09-ww32-step-area-chart",
    "2019-08-14-ww33-table-formatting", "2019-09-02-ww34-top-n-single-worksheet",
    "2026-02-02-ww04-dynamic-moving-average", "2026-02-09-ww05-kpi-period-comparison",
    "2026-02-15-ww06-null-safe-averages",
})
SUMMARY_FIELDS = (
    "case_id", "legacy_case_ids", "iteration_id", "article_date", "challenge_year",
    "challenge_week", "challenge_date", "date_evidence", "source",
    "functional_status", "visual_status", "verification_status", "cwtwb_result",
    "artifacts", "artifact_aliases", "historical_artifacts", "evidence", "notes",
)


def iso_date(value: object, field: str, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise AssertionError(f"Invalid {field}: {value!r}")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise AssertionError(f"Invalid {field}: {value!r}") from exc
    return value


def folder_identity(name: str) -> tuple[str, int, str]:
    match = FOLDER.fullmatch(name)
    if not match:
        raise AssertionError(f"Invalid iteration folder: {name}")
    article_date, week, slug = match.groups()
    iso_date(article_date, "folder article date")
    if not 1 <= int(week) <= 53:
        raise AssertionError(f"Invalid challenge_week in folder: {name}")
    return article_date, int(week), slug


def canonical_id(name: str, challenge_year: int) -> str:
    _, week, slug = folder_identity(name)
    if type(challenge_year) is not int or not 1 <= challenge_year <= 9999:
        raise AssertionError("Invalid challenge_year")
    return f"wow-{challenge_year:04d}-ww{week:02d}-{slug}"


def normalize_url(value: str) -> str:
    parts = urlsplit(value)
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        raise AssertionError(f"Invalid source URL: {value}")
    # Protocol, query, trailing slash and fragments do not identify an article.
    return parts.netloc.lower() + unquote(parts.path).rstrip("/")


def workbook_identity(value: str) -> str:
    if value.startswith(("http://", "https://")):
        parts = urlsplit(value)
        if parts.hostname == "public.tableau.com":
            match = re.search(r"/(?:viz|views|vizhome|workbooks)/([^/?#]+)", unquote(value))
            if match:
                return "tableau-public:" + re.sub(r"\.(?:twb|twbx)$", "", match[1])
        return normalize_url(value)
    path = Path(value)
    if path.parts and path.parts[0] == "dashboards":
        return "tableau-public:" + path.stem
    return path.as_posix()


def article_map(root: Path) -> dict[str, str]:
    path = root / "index.json"
    if not path.is_file():
        return {}
    return {
        "posts/" + item["file"]: normalize_url(item["link"])
        for item in json.loads(path.read_text(encoding="utf-8")).get("posts", [])
    }


def article_identity(value: str, mapping: dict[str, str]) -> str:
    if value.startswith(("http://", "https://")):
        return normalize_url(value)
    return mapping.get(Path(value).as_posix(), Path(value).as_posix())


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def relative_file(base: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise AssertionError(f"Invalid artifact/evidence path: {value!r}")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or str(path) != value:
        raise AssertionError(f"Unsafe artifact/evidence path: {value}")
    result = base / path
    if not result.is_file():
        raise AssertionError(f"Missing artifact/evidence: {result}")
    return result


def source_locks(case_dir: Path) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in (
        case_dir / "inputs/source-lock.json", case_dir / "evidence/source-lock.json"
    ) if p.is_file()]


def locked_workbook(lock: dict) -> dict:
    return (lock.get("source_workbook") or lock.get("source_twbx")
            or lock.get("workbook", {}).get("source_twbx") or {})


def validate_identity(case_dir: Path, case: dict, root: Path = LAB_ROOT) -> None:
    contract = case.get("schema_version")
    if contract == "legacy-summary-1.0":
        if case_dir.name not in LEGACY_ITERATIONS:
            raise AssertionError("Legacy contract is restricted to grandfathered iterations")
    elif contract not in {"1.0.0", "1.1.0"}:
        raise AssertionError("Unsupported case schema_version")
    article_date, week, _ = folder_identity(case_dir.name)
    if case.get("iteration_id") != case_dir.name:
        raise AssertionError("iteration_id must match the folder")
    if case.get("article_date") != article_date:
        raise AssertionError("article_date must match the folder publication date")
    iso_date(case.get("article_date"), "article_date")
    if "source_workbook_date" in case or "source_workbook_date" in case.get("date_evidence", {}):
        raise AssertionError("source_workbook_date is retired; use the two-date contract")
    if "challenge_date" not in case:
        raise AssertionError("challenge_date is required (null when unverified)")
    challenge_date = iso_date(case["challenge_date"], "challenge_date", nullable=True)
    if challenge_date is not None:
        challenge_url = case.get("source", {}).get("challenge", {}).get("url")
        if not challenge_url or not case.get("date_evidence", {}).get("challenge_date"):
            raise AssertionError("Known challenge_date needs official source URL and date evidence")
        normalize_url(challenge_url)
        evidence_path = root / "docs/protocols/challenge-date-sources.json"
        if evidence_path.is_file():
            rows = json.loads(evidence_path.read_text(encoding="utf-8"))["challenges"]
            matches = [row for row in rows if row["challenge_year"] == case.get("challenge_year")
                       and row["challenge_week"] == case.get("challenge_week")]
            if matches and (len(matches) != 1 or matches[0]["challenge_date"] != challenge_date
                            or normalize_url(matches[0]["url"]) != normalize_url(challenge_url)):
                raise AssertionError("challenge_date/source differs from official date evidence")
    if type(case.get("challenge_week")) is not int or case["challenge_week"] != week:
        raise AssertionError("challenge_week must match the folder (01-53)")
    expected = canonical_id(case_dir.name, case.get("challenge_year"))
    if case.get("case_id") != expected:
        raise AssertionError(f"Expected canonical case_id {expected}")
    aliases = case.get("legacy_case_ids")
    if not isinstance(aliases, dict) or any(
        not isinstance(k, str) or not k or k.strip() != k or k == expected or v != expected
        for k, v in aliases.items()
    ):
        raise AssertionError("legacy_case_ids must map old IDs to this canonical ID")
    if case.get("functional_status") not in {"partial", "replicated", "blocked"}:
        raise AssertionError("Invalid functional_status")
    if case.get("visual_status") not in {"not_evaluated", "acceptable_delta", "matched"}:
        raise AssertionError("Invalid visual_status")
    if case.get("verification_status") not in {"pending", "historical", "verified"}:
        raise AssertionError("Invalid verification_status")
    if case.get("cwtwb_result") not in {None, "pass", "workaround", "blocked"}:
        raise AssertionError("Invalid cwtwb_result")
    if not isinstance(case.get("cwtwb"), dict) or "tested_version" not in case["cwtwb"]:
        raise AssertionError("tested SDK version (or explicit null) is required")
    source = case.get("source", {})
    mapping = article_map(root)
    article = source.get("article", {})
    if not (article.get("url") or article.get("path")):
        raise AssertionError("Missing article identity")
    if article.get("url") and article.get("path") in mapping:
        if article_identity(article["url"], mapping) != article_identity(article["path"], mapping):
            raise AssertionError("Article URL/path identity mismatch")
    post = case.get("post") or case.get("inputs", {}).get("article")
    if post and article_identity(post, mapping) not in {
        article_identity(v, mapping) for v in (article.get("url"), article.get("path")) if v
    }:
        raise AssertionError("post differs from source article identity")
    archive_index = root / "index.json"
    if archive_index.exists():
        for item in json.loads(archive_index.read_text(encoding="utf-8")).get("posts", []):
            if normalize_url(item["link"]) == article_identity(article.get("url") or article["path"], mapping):
                if item["date"] != article_date:
                    raise AssertionError("article_date differs from archived article metadata")
    workbook = source.get("workbook", {})
    if not (workbook.get("url") or workbook.get("path") or workbook.get("filename")):
        raise AssertionError("Missing original workbook identity")
    wb_tokens = {workbook_identity(workbook[k]) for k in ("url", "path") if workbook.get(k)}
    if len(wb_tokens) > 1:
        raise AssertionError("Original workbook URL/path identity mismatch")
    for entity in (article, workbook):
        sha = entity.get("sha256")
        if sha is not None and (not isinstance(sha, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", sha)):
            raise AssertionError("Invalid original source hash")
    filename = workbook.get("filename") or Path(workbook.get("path") or "").name
    for lock in source_locks(case_dir):
        original = locked_workbook(lock)
        if original.get("sha256") and (original["sha256"].lower() != (workbook.get("sha256") or "").lower()):
            raise AssertionError("Original workbook hash differs from source lock")
        if original.get("filename") and original["filename"] != filename:
            raise AssertionError("Original workbook filename differs from source lock")
        if original.get("path") and workbook_identity(original["path"]) not in wb_tokens:
            raise AssertionError("Original workbook path differs from source lock")
        original_article = lock.get("article", {})
        if original_article.get("sha256") and original_article["sha256"].lower() != (article.get("sha256") or "").lower():
            raise AssertionError("Article hash differs from source lock")
        old_id = lock.get("case_id")
        if old_id and old_id != expected and old_id not in aliases:
            raise AssertionError("Historical source-lock ID lacks an alias")
    artifacts = case.get("artifacts", {})
    if artifacts.get("primary_workbook") != PRIMARY:
        raise AssertionError(f"Primary workbook must be {PRIMARY}")
    for key, value in artifacts.items():
        if value is not None:
            relative_file(case_dir, value)
        if key in {"cloud_author", "cloud_replica"} and value not in {None, f"outputs/{key.replace('_', '-')}.png"}:
            raise AssertionError(f"Noncanonical screenshot: {key}")
    for old, new in case.get("artifact_aliases", {}).items():
        if not isinstance(old, str) or Path(old).is_absolute() or ".." in Path(old).parts or old == new:
            raise AssertionError("Invalid artifact alias")
        relative_file(case_dir, new)
        if (case_dir / old).exists():
            raise AssertionError(f"Stale alias path still exists: {old}")
    for record in case.get("historical_artifacts", []):
        relative_file(case_dir, record["path"])
        if not record.get("role") or not record.get("note"):
            raise AssertionError("Historical/probe artifacts need role and explanation")
    for evidence in case.get("evidence", []):
        relative_file(case_dir, evidence)
    for filename in ("build_replication.py", "verify_replication.py"):
        path = case_dir / filename
        if path.exists():
            text = path.read_text(encoding="utf-8")
            for old in case.get("artifact_aliases", {}):
                if old in text or (old.startswith("outputs/") and Path(old).name in text):
                    raise AssertionError(f"Stale output reference in {filename}: {old}")


def active_cases(root: Path = LAB_ROOT) -> list[tuple[Path, dict]]:
    result = []
    for directory in sorted((root / "iterations").iterdir()):
        if not directory.is_dir() or directory.name == "_template":
            continue
        folder_identity(directory.name)  # Do not silently skip malformed or unindexed cases.
        path = directory / "case.yaml"
        if not path.is_file():
            raise AssertionError(f"Missing case metadata: {directory.name}")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        validate_identity(directory, document, root)
        result.append((directory, document))
    return result


def validate_unique(cases: list[tuple[Path, dict]], root: Path = LAB_ROOT) -> None:
    ids: dict[str, str] = {}
    sources: dict[tuple[str, str], str] = {}
    mapping = article_map(root)
    for directory, case in cases:
        for value in [case["case_id"], *case["legacy_case_ids"]]:
            if value in ids:
                raise AssertionError(f"ID/alias collision: {value} ({ids[value]}, {directory.name})")
            ids[value] = directory.name
        article, workbook = case["source"]["article"], case["source"]["workbook"]
        tokens = {("article", article_identity(v, mapping)) for v in (article.get("url"), article.get("path")) if v}
        tokens.update(("workbook", workbook_identity(workbook[k])) for k in ("url", "path") if workbook.get(k))
        if workbook.get("sha256"):
            tokens.add(("original-workbook-sha256", workbook["sha256"].lower()))
        for token in tokens:
            if token in sources:
                raise AssertionError(f"Duplicate source identity: {token} ({sources[token]}, {directory.name})")
            sources[token] = directory.name


def catalogue(root: Path = LAB_ROOT) -> dict:
    cases = active_cases(root)
    validate_unique(cases, root)
    records = []
    aliases = {}
    for directory, case in cases:
        record = {key: case.get(key) for key in SUMMARY_FIELDS}
        record["metadata"] = f"iterations/{directory.name}/case.yaml"
        record["metadata_contract"] = case["schema_version"]
        record["tested_sdk_version"] = case["cwtwb"]["tested_version"]
        records.append(record)
        aliases.update(case["legacy_case_ids"])
    return {"schema_version": "1.0.0", "generated_from": "iterations/*/case.yaml",
            "active_case_count": len(records), "legacy_case_ids": aliases, "cases": records}


def compatibility_view(index: dict) -> dict:
    # One canonical entry per active case. Consumers resolve archival donna IDs
    # through legacy_case_ids; aliases must not inflate case counts.
    records = []
    for case in index["cases"]:
        wb_id = case["source"]["workbook"].get("workbook_id")
        records.append({
            "case_id": case["case_id"], "legacy_case_ids": case["legacy_case_ids"],
            "workbook_ids": [wb_id] if wb_id else [], "iteration": case["iteration_id"],
            "status": "consumed", "replication_status": case["functional_status"],
            "verification_status": case["verification_status"],
            "cwtwb_version": case["tested_sdk_version"],
            "reason": "Derived from case metadata; consumed means claimed, not verified completed.",
        })
    return {"schema_version": "2.0.0", "generated_from": "usage/case-index.json",
            "selection_policy": "exclude_consumed_cases_from_future_feature_iterations",
            "legacy_case_ids": index["legacy_case_ids"], "consumed_cases": records}


def check_catalogue(root: Path = LAB_ROOT) -> dict:
    index = catalogue(root)
    for name, expected in (("case-index.json", index), ("consumed-cases.json", compatibility_view(index))):
        path = root / "usage" / name
        if not path.is_file() or json.loads(path.read_text(encoding="utf-8")) != expected:
            raise AssertionError(f"Catalogue differs from source metadata: usage/{name}; regenerate")
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Regenerate both derived views")
    args = parser.parse_args()
    if args.write:
        index = catalogue()
        for name, value in (("case-index.json", index), ("consumed-cases.json", compatibility_view(index))):
            (LAB_ROOT / "usage" / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index = check_catalogue()
    print(f"PASS: catalogue ({index['active_case_count']} active cases)")


if __name__ == "__main__":
    main()
