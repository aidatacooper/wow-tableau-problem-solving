#!/usr/bin/env python3
"""Build a normalized, verifiable dataset from the crawler outputs.

The crawler outputs remain immutable source artifacts. This script creates a
derived dataset with stable IDs, hashes, TWBX integrity checks, extracted TWB
files, conservative link roles, and machine/human-readable quality reports.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import struct
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree

PROJECT = Path(__file__).resolve().parent
SCHEMA_VERSION = "1.0.0"
DATASET_VERSION = "1"
DONNA_OWNERS = {"donna.coles", "donnacoles"}

TAG_RE = re.compile(r"<[^>]+>")
ANCHOR_RE = re.compile(
    r"<a\b[^>]*\bhref=(['\"])(.*?)\1[^>]*>(.*?)</a>",
    re.I | re.S,
)
IMAGE_RE = re.compile(r"<img\b([^>]*)>", re.I | re.S)
ATTR_RE = re.compile(r"\b([A-Za-z_:][-A-Za-z0-9_:.]*)=(['\"])(.*?)\2", re.S)
PROFILE_RE = re.compile(r"/(?:app/)?profile/([^/#!?]+)", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_case_id(url: str, date: str) -> str:
    return f"donna-{date}-{hashlib.sha256(url.encode('utf-8')).hexdigest()[:12]}"


def stable_workbook_id(workbook: str) -> str:
    return f"tableau-{hashlib.sha256(workbook.encode('utf-8')).hexdigest()[:16]}"


def relative_to_project(path: Path) -> str:
    return path.resolve().relative_to(PROJECT).as_posix()


def load_json(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def case_id_aliases(usage_registry: dict) -> dict[str, str]:
    """Validate direct aliases against canonical records before using them."""
    records = usage_registry.get("consumed_cases", [])
    canonical = {item["case_id"] for item in records}
    aliases: dict[str, str] = {}
    declared_aliases: dict[str, str] = {}
    mappings = [usage_registry.get("legacy_case_ids", {})]
    for item in records:
        mapping = item.get("legacy_case_ids", {})
        if not isinstance(mapping, dict) or any(v != item["case_id"] for v in mapping.values()):
            raise ValueError("Record aliases must target their own canonical case_id")
        mappings.append(mapping)
        declared_aliases.update(mapping)
    for mapping in mappings:
        if not isinstance(mapping, dict):
            raise ValueError("legacy_case_ids must be a mapping")
        for alias, target in mapping.items():
            if (not isinstance(alias, str) or not alias or alias.strip() != alias
                    or not isinstance(target, str) or target not in canonical
                    or alias in canonical or (alias in aliases and aliases[alias] != target)):
                raise ValueError(f"Invalid or conflicting case alias: {alias!r}")
            aliases[alias] = target
    if usage_registry.get("schema_version") == "2.0.0" and (
            usage_registry.get("legacy_case_ids", {}) != declared_aliases):
        raise ValueError("Registry aliases must match canonical record aliases")
    return aliases


def canonical_consumed_case_ids(usage_registry: dict) -> set[str]:
    """Count canonical records, never their compatibility aliases."""
    case_id_aliases(usage_registry)
    return {item["case_id"] for item in usage_registry.get("consumed_cases", [])
            if item.get("status") == "consumed"}


def consumed_case_ids(usage_registry: dict) -> set[str]:
    """Return canonical IDs and validated aliases excluded from selection."""
    canonical = canonical_consumed_case_ids(usage_registry)
    return canonical | {alias for alias, target in case_id_aliases(usage_registry).items()
                        if target in canonical}


def eligible_cases(cases: list[dict], usage_registry: dict) -> list[dict]:
    """Filter out cases already consumed by an earlier cwtwb iteration."""
    excluded = consumed_case_ids(usage_registry)
    return [case for case in cases if case.get("case_id") not in excluded]


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            stream.write("\n")


def strip_html(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", value))).strip()


def normalize_url(value: str) -> str:
    return html.unescape(value).rstrip(").,;").strip()


def anchor_index(article_html: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for match in ANCHOR_RE.finditer(article_html):
        url = normalize_url(match.group(2))
        label = strip_html(match.group(3))
        if label and label not in result[url]:
            result[url].append(label)
    return dict(result)


def extract_resources(article_html: str) -> list[dict]:
    resources: list[dict] = []
    seen: set[str] = set()
    for match in ANCHOR_RE.finditer(article_html):
        url = normalize_url(match.group(2))
        if not url or url.startswith(("#", "mailto:", "javascript:")) or url in seen:
            continue
        seen.add(url)
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        suffix = Path(parsed.path).suffix.lower()
        if "workout-wednesday.com" in host:
            resource_type = "challenge"
        elif "public.tableau.com" in host:
            resource_type = "tableau_public"
        elif suffix in {".csv", ".xls", ".xlsx", ".zip", ".twb", ".twbx", ".hyper"}:
            resource_type = "downloadable_attachment"
        else:
            resource_type = "external_reference"
        resources.append(
            {
                "url": url,
                "anchor_text": strip_html(match.group(3)),
                "host": host,
                "type": resource_type,
            }
        )
    return resources


def extract_embedded_images(article_html: str) -> list[dict]:
    images: list[dict] = []
    seen: set[str] = set()
    for match in IMAGE_RE.finditer(article_html):
        attrs = {
            key.lower(): html.unescape(value)
            for key, _, value in ATTR_RE.findall(match.group(1))
        }
        url = normalize_url(attrs.get("src", ""))
        if not url or url.startswith("data:") or url in seen:
            continue
        seen.add(url)
        images.append(
            {
                "url": url,
                "alt": attrs.get("alt", ""),
                "width": attrs.get("width", ""),
                "height": attrs.get("height", ""),
                "download_status": "not_collected",
            }
        )
    return images


def tableau_owner(url: str) -> str:
    match = PROFILE_RE.search(url)
    return unquote(match.group(1)).lower() if match else ""


def classify_link(raw_url: str) -> tuple[str, float, str]:
    """Return a deliberately conservative role classification."""
    owner = tableau_owner(raw_url)
    if owner in DONNA_OWNERS:
        return "candidate_author_solution", 0.90, "Tableau profile belongs to Donna Coles"
    if owner:
        return "external_reference", 0.90, f"Tableau profile belongs to {owner}"
    return (
        "candidate_author_solution",
        0.55,
        "Workbook owner is absent from this URL format; manual review is recommended",
    )


def png_dimensions(path: Path) -> tuple[int | None, int | None]:
    try:
        with path.open("rb") as stream:
            header = stream.read(24)
        if header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR":
            return struct.unpack(">II", header[16:24])
    except OSError:
        pass
    return None, None


def inspect_twb_xml(xml_bytes: bytes) -> dict:
    root = ElementTree.fromstring(xml_bytes)

    def count(path: str) -> int:
        return len(root.findall(path))

    parameter_columns = 0
    calculated_fields = 0
    for column in root.findall(".//column"):
        if column.get("param-domain-type") or column.get("role") == "parameter":
            parameter_columns += 1
        if column.find("calculation") is not None:
            calculated_fields += 1

    return {
        "root_tag": root.tag,
        "tableau_version": root.get("version", ""),
        "source_build": root.get("source-build", ""),
        "datasource_count": count(".//datasources/datasource"),
        "worksheet_count": count(".//worksheets/worksheet"),
        "dashboard_count": count(".//dashboards/dashboard"),
        "action_count": count(".//actions/action"),
        "parameter_count": parameter_columns,
        "calculated_field_count": calculated_fields,
    }


def inspect_workbook(
    workbook: str,
    source_path: Path,
    extracted_root: Path,
) -> dict:
    record = {
        "workbook_id": stable_workbook_id(workbook),
        "tableau_workbook_name": workbook,
        "source": {
            "download_url": f"https://public.tableau.com/workbooks/{workbook}.twb",
            "path": relative_to_project(source_path),
        },
        "status": "missing",
        "integrity": {},
        "twb": None,
    }
    if not source_path.exists():
        record["integrity"] = {"valid": False, "errors": ["TWBX file is missing"]}
        return record

    record["source"].update(
        {
            "size_bytes": source_path.stat().st_size,
            "sha256": sha256_file(source_path),
        }
    )
    errors: list[str] = []
    try:
        with zipfile.ZipFile(source_path) as archive:
            corrupt_member = archive.testzip()
            if corrupt_member:
                errors.append(f"Corrupt ZIP member: {corrupt_member}")
            twb_members = sorted(
                name for name in archive.namelist() if name.lower().endswith(".twb")
            )
            if len(twb_members) != 1:
                errors.append(f"Expected exactly one TWB member, found {len(twb_members)}")
            if twb_members:
                member = twb_members[0]
                xml_bytes = archive.read(member)
                features = inspect_twb_xml(xml_bytes)
                target_dir = extracted_root / record["workbook_id"]
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / "workbook.twb"
                target.write_bytes(xml_bytes)
                record["twb"] = {
                    "archive_member": member,
                    "path": relative_to_project(target),
                    "size_bytes": len(xml_bytes),
                    "sha256": hashlib.sha256(xml_bytes).hexdigest(),
                    "features": features,
                }
    except (zipfile.BadZipFile, ElementTree.ParseError, OSError) as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    record["integrity"] = {
        "valid": not errors,
        "errors": errors,
    }
    record["status"] = "available" if not errors else "invalid"
    return record


def find_source_twbx(dashboards: Path, workbook: str) -> Path:
    direct = dashboards / workbook / f"{workbook}.twbx"
    if direct.exists():
        return direct
    candidates = list((dashboards / workbook).glob("*.twbx"))
    return candidates[0] if len(candidates) == 1 else direct


def build_png_inventory(dashboards: Path) -> tuple[dict[str, list[dict]], dict]:
    paths = sorted(dashboards.glob("*/*.png"))
    hashes = Counter(sha256_file(path) for path in paths)
    by_workbook: dict[str, list[dict]] = defaultdict(list)
    invalid = 0
    for path in paths:
        digest = sha256_file(path)
        width, height = png_dimensions(path)
        is_mass_duplicate = hashes[digest] >= 10
        status = "invalid_placeholder" if is_mass_duplicate else "available"
        if status != "available":
            invalid += 1
        by_workbook[path.parent.name].append(
            {
                "path": relative_to_project(path),
                "size_bytes": path.stat().st_size,
                "sha256": digest,
                "width": width,
                "height": height,
                "status": status,
                "reason": (
                    f"Identical asset occurs {hashes[digest]} times"
                    if is_mass_duplicate
                    else ""
                ),
            }
        )
    summary = {
        "total": len(paths),
        "valid": len(paths) - invalid,
        "invalid": invalid,
        "unique_sha256": len(hashes),
        "duplicate_groups": [
            {"sha256": digest, "count": count}
            for digest, count in hashes.most_common()
            if count > 1
        ],
    }
    return dict(by_workbook), summary


def build_dataset(project: Path = PROJECT, clean: bool = False) -> dict:
    index_path = project / "index.json"
    links_path = project / "public_links_map.json"
    posts_dir = project / "posts"
    dashboards_dir = project / "dashboards"
    dataset_dir = project / "dataset"
    if clean and dataset_dir.exists():
        shutil.rmtree(dataset_dir)
    dataset_dir.mkdir(parents=True, exist_ok=True)

    index = load_json(index_path)
    links_map = load_json(links_path)
    usage_registry_path = project / "usage" / "consumed-cases.json"
    usage_registry = load_json(usage_registry_path)
    link_items = {item["html_file"]: item for item in links_map["items"]}
    png_by_workbook, png_summary = build_png_inventory(dashboards_dir)

    workbook_to_articles: dict[str, set[str]] = defaultdict(set)
    workbook_to_views: dict[str, set[str]] = defaultdict(set)
    all_workbook_names: set[str] = set()
    for item in links_map["items"]:
        for link in item["links"]:
            workbook = link.get("workbook", "")
            if not workbook:
                continue
            all_workbook_names.add(workbook)
            workbook_to_articles[workbook].add(item["article"])
            if link.get("view"):
                workbook_to_views[workbook].add(link["view"])

    workbook_records: list[dict] = []
    workbook_by_name: dict[str, dict] = {}
    extracted_root = dataset_dir / "workbooks"
    for workbook in sorted(all_workbook_names):
        source_path = find_source_twbx(dashboards_dir, workbook)
        record = inspect_workbook(workbook, source_path, extracted_root)
        record["views"] = sorted(workbook_to_views[workbook])
        record["article_stems"] = sorted(workbook_to_articles[workbook])
        record["images"] = png_by_workbook.get(workbook, [])
        workbook_records.append(record)
        workbook_by_name[workbook] = record

    cases: list[dict] = []
    missing_article_files: list[str] = []
    unresolved_links = 0
    for post in index["posts"]:
        html_path = posts_dir / post["file"]
        if html_path.exists():
            article_html = html_path.read_text(encoding="utf-8", errors="replace")
            article_asset = {
                "path": relative_to_project(html_path),
                "size_bytes": html_path.stat().st_size,
                "sha256": sha256_file(html_path),
                "format": "article_content_html",
            }
            anchors = anchor_index(article_html)
            resources = extract_resources(article_html)
            embedded_images = extract_embedded_images(article_html)
        else:
            missing_article_files.append(post["file"])
            article_asset = {
                "path": f"posts/{post['file']}",
                "format": "article_content_html",
                "missing": True,
            }
            anchors = {}
            resources = []
            embedded_images = []

        case_id = stable_case_id(post["link"], post["date"])
        item = link_items.get(post["file"], {"links": []})
        tableau_links: list[dict] = []
        for link in item["links"]:
            workbook = link.get("workbook", "")
            if workbook:
                link_type = "tableau_view"
                role, confidence, reason = classify_link(link["raw_url"])
            else:
                link_type = "tableau_resource"
                role, confidence, reason = (
                    "external_reference",
                    1.0,
                    "Public Tableau URL does not identify a workbook view",
                )
            workbook_record = workbook_by_name.get(workbook)
            if workbook and not workbook_record:
                unresolved_links += 1
            tableau_links.append(
                {
                    "link_type": link_type,
                    "raw_url": link["raw_url"],
                    "canonical_view_url": link.get("viz_url", ""),
                    "anchor_texts": anchors.get(link["raw_url"], []),
                    "owner": tableau_owner(link["raw_url"]),
                    "workbook_name": workbook,
                    "workbook_id": (
                        workbook_record["workbook_id"] if workbook_record else None
                    ),
                    "view": link.get("view", ""),
                    "role": role,
                    "role_confidence": confidence,
                    "role_reason": reason,
                    "requires_manual_role_review": bool(workbook) and confidence < 0.80,
                }
            )

        case = {
            "schema_version": SCHEMA_VERSION,
            "case_id": case_id,
            "article": {
                "title": post["title"],
                "published_date": post["date"],
                "canonical_url": post["link"],
                "asset": article_asset,
                "embedded_images": embedded_images,
            },
            "tableau_links": tableau_links,
            "resources": resources,
            "collection": {
                "source": "donnacoles.home.blog",
                "normalized_at": utc_now(),
            },
        }
        cases.append(case)
        write_json(dataset_dir / "cases" / case_id / "case.json", case)

    available_workbooks = sum(r["status"] == "available" for r in workbook_records)
    invalid_workbooks = sum(r["status"] == "invalid" for r in workbook_records)
    missing_workbooks = sum(r["status"] == "missing" for r in workbook_records)
    manual_role_reviews = sum(
        link["requires_manual_role_review"]
        for case in cases
        for link in case["tableau_links"]
    )
    resource_counts = Counter(
        resource["type"] for case in cases for resource in case["resources"]
    )
    quality = {
        "article_count": len(cases),
        "articles_with_tableau_links": sum(bool(c["tableau_links"]) for c in cases),
        "articles_without_tableau_links": sum(not c["tableau_links"] for c in cases),
        "missing_article_files": missing_article_files,
        "unique_workbook_count": len(workbook_records),
        "available_workbooks": available_workbooks,
        "invalid_workbooks": invalid_workbooks,
        "missing_workbooks": missing_workbooks,
        "missing_workbook_names": [
            record["tableau_workbook_name"]
            for record in workbook_records
            if record["status"] == "missing"
        ],
        "unresolved_tableau_links": unresolved_links,
        "links_requiring_manual_role_review": manual_role_reviews,
        "resource_counts": dict(sorted(resource_counts.items())),
        "embedded_article_images": sum(
            len(case["article"]["embedded_images"]) for case in cases
        ),
        "images": png_summary,
    }
    dataset_manifest = {
        "dataset_name": "donnacoles-tableau-cases",
        "dataset_version": DATASET_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "source": {
            "site": index["base"],
            "source_index": "index.json",
            "source_link_map": "public_links_map.json",
            "source_index_sha256": sha256_file(index_path),
            "source_link_map_sha256": sha256_file(links_path),
        },
        "artifacts": {
            "cases": "dataset/cases.jsonl",
            "workbooks": "dataset/workbooks.jsonl",
            "quality_report": "dataset/quality-report.json",
            "usage": "dataset/usage.json",
        },
        "schemas": {
            "case": {
                "path": "schemas/case.schema.json",
                "sha256": sha256_file(project / "schemas" / "case.schema.json"),
            },
            "workbook": {
                "path": "schemas/workbook.schema.json",
                "sha256": sha256_file(project / "schemas" / "workbook.schema.json"),
            },
            "usage": {
                "path": "schemas/usage.schema.json",
                "sha256": sha256_file(project / "schemas" / "usage.schema.json"),
            },
        },
        "quality": quality,
        "usage": {
            "selection_policy": usage_registry["selection_policy"],
            "consumed_case_count": len(canonical_consumed_case_ids(usage_registry)),
            "eligible_case_count": len(eligible_cases(cases, usage_registry)),
        },
    }
    write_jsonl(dataset_dir / "cases.jsonl", cases)
    write_jsonl(dataset_dir / "workbooks.jsonl", workbook_records)
    write_json(dataset_dir / "quality-report.json", quality)
    write_json(dataset_dir / "usage.json", usage_registry)
    write_json(dataset_dir / "dataset.json", dataset_manifest)
    write_quality_markdown(dataset_dir / "quality-report.md", quality)
    return dataset_manifest


def write_quality_markdown(path: Path, quality: dict) -> None:
    image_quality = quality["images"]
    lines = [
        "# Dataset Quality Report",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Articles | {quality['article_count']} |",
        f"| Articles with Tableau links | {quality['articles_with_tableau_links']} |",
        f"| Articles without Tableau links | {quality['articles_without_tableau_links']} |",
        f"| Unique workbooks | {quality['unique_workbook_count']} |",
        f"| Available and valid TWBX | {quality['available_workbooks']} |",
        f"| Invalid TWBX | {quality['invalid_workbooks']} |",
        f"| Missing TWBX | {quality['missing_workbooks']} |",
        f"| Unresolved Tableau links | {quality['unresolved_tableau_links']} |",
        f"| Links requiring manual role review | {quality['links_requiring_manual_role_review']} |",
        f"| Challenge links | {quality['resource_counts'].get('challenge', 0)} |",
        f"| Downloadable attachment links | {quality['resource_counts'].get('downloadable_attachment', 0)} |",
        f"| Embedded article image references | {quality['embedded_article_images']} |",
        f"| PNG files | {image_quality['total']} |",
        f"| Valid PNG files | {image_quality['valid']} |",
        f"| Invalid/placeholder PNG files | {image_quality['invalid']} |",
        f"| Unique PNG hashes | {image_quality['unique_sha256']} |",
        "",
        "## Important findings",
        "",
    ]
    if image_quality["invalid"]:
        lines.append(
            f"- {image_quality['invalid']} PNG files are excluded from valid visual assets "
            "because they are mass-duplicated placeholder images."
        )
    if quality["missing_workbooks"]:
        lines.append(
            f"- {quality['missing_workbooks']} linked workbooks are unavailable locally."
        )
    if quality["links_requiring_manual_role_review"]:
        lines.append(
            f"- {quality['links_requiring_manual_role_review']} links need manual role review."
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def check_dataset(project: Path = PROJECT) -> list[str]:
    dataset = project / "dataset"
    errors: list[str] = []
    required = [
        dataset / "dataset.json",
        dataset / "cases.jsonl",
        dataset / "workbooks.jsonl",
        dataset / "quality-report.json",
        dataset / "usage.json",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"Missing required artifact: {path}")
    if errors:
        return errors

    cases = [
        json.loads(line)
        for line in (dataset / "cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    workbooks = [
        json.loads(line)
        for line in (dataset / "workbooks.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    usage = load_json(dataset / "usage.json")
    case_ids = [case["case_id"] for case in cases]
    workbook_ids = [record["workbook_id"] for record in workbooks]
    if len(case_ids) != len(set(case_ids)):
        errors.append("Duplicate case_id values found")
    if len(workbook_ids) != len(set(workbook_ids)):
        errors.append("Duplicate workbook_id values found")
    known_workbook_ids = set(workbook_ids)
    try:
        aliases = case_id_aliases(usage)
    except ValueError as exc:
        errors.append(str(exc))
        aliases = {}
    source_case_ids = {aliases.get(value, value) for value in case_ids}
    seen_consumed: set[str] = set()
    for consumed in usage.get("consumed_cases", []):
        consumed_case_id = consumed.get("case_id", "")
        consumed_case_id = aliases.get(consumed_case_id, consumed_case_id)
        if consumed_case_id in seen_consumed:
            errors.append(f"Duplicate consumed case_id {consumed_case_id}")
        seen_consumed.add(consumed_case_id)
        if consumed_case_id not in source_case_ids:
            errors.append(f"Unknown consumed case_id {consumed_case_id}")
        for workbook_id in consumed.get("workbook_ids", []):
            if workbook_id not in known_workbook_ids:
                errors.append(
                    f"Unknown consumed workbook_id {workbook_id} "
                    f"for case {consumed_case_id}"
                )
    for case in cases:
        case_path = dataset / "cases" / case["case_id"] / "case.json"
        if not case_path.exists():
            errors.append(f"Missing per-case record: {case_path}")
        for link in case["tableau_links"]:
            workbook_id = link.get("workbook_id")
            if workbook_id and workbook_id not in known_workbook_ids:
                errors.append(
                    f"Unknown workbook_id {workbook_id} in case {case['case_id']}"
                )
    for workbook in workbooks:
        if workbook["status"] == "available":
            twb = workbook.get("twb") or {}
            twb_path = project / twb.get("path", "")
            if not twb_path.exists():
                errors.append(
                    f"Missing extracted TWB for {workbook['tableau_workbook_name']}"
                )
            elif sha256_file(twb_path) != twb.get("sha256"):
                errors.append(
                    f"Extracted TWB hash mismatch for {workbook['tableau_workbook_name']}"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="Rebuild dataset from scratch")
    parser.add_argument("--check", action="store_true", help="Validate an existing dataset")
    args = parser.parse_args()

    if not args.check:
        manifest = build_dataset(clean=args.clean)
        print(json.dumps(manifest["quality"], ensure_ascii=False, indent=2))
    errors = check_dataset()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Dataset validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
