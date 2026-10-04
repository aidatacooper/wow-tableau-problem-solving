"""Publish original/replica and capture hash-bound REST images and CSV states.

Credentials are read only from process environment. Captures establish REST
states and exported worksheet scope, never browser action execution.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import struct
import time

import tableauserverclient as TSC
import yaml


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def apply_state(options, state):
    for name, value in state.get("parameters", {}).items():
        options.parameter(name, str(value))
    for name, value in state.get("filters", {}).items():
        options.vf(name, str(value))
    return options


def csv_state(state, role, data_request):
    """Return the actual CSV scope; diagnostic exports may keep all members.

    Role-specific filters remain explicit overrides. Image requests always use
    the common state, independently of these per-worksheet CSV options.
    """
    ignore = data_request.get(f"{role}_ignore_state_filters", False)
    if not isinstance(ignore, bool):
        raise ValueError("ignore_state_filters must be a boolean")
    filters = {} if ignore else dict(state.get("filters", {}))
    filters.update(state.get(f"{role}_filters", {}))
    return {"parameters": dict(state.get("parameters", {})), "filters": filters}


def retry(operation):
    for attempt in range(3):
        try:
            return operation()
        except (TSC.ServerResponseError, ConnectionError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def capture(request):
    case_dir = Path(request["case_dir"]).resolve()
    case = yaml.safe_load((case_dir / "case.yaml").read_text(encoding="utf-8"))
    outputs = case_dir / "outputs"
    evidence = case_dir / "evidence"
    outputs.mkdir(exist_ok=True)
    evidence.mkdir(exist_ok=True)
    replica = outputs / "replicated-workbook.twbx"
    author = Path(request["author_workbook"])
    report = {
        "case_id": case["case_id"],
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source_hashes": {"author": digest(author), "replica": digest(replica)},
        "acceptance_scope": "cloud_rest_and_artifact_contracts",
        "browser_interaction_executed": False,
        "workbooks": {}, "states": [],
        "status": "captured_requires_independent_review",
    }
    auth = TSC.PersonalAccessTokenAuth(
        os.environ["TABLEAU_TOKEN_NAME"], os.environ["TABLEAU_TOKEN_SECRET"],
        site_id=os.environ["TABLEAU_SITE_ID"],
    )
    server = TSC.Server(os.environ["TABLEAU_SERVER_URL"], use_server_version=True)
    with server.auth.sign_in(auth):
        project = next(p for p in TSC.Pager(server.projects) if p.name == request.get("project", "default"))
        published = {}
        for role, path in (("author", author), ("replica", replica)):
            item = TSC.WorkbookItem(project.id, name=f"cwtwb-review-{case['case_id']}-{role}-{digest(path)[:12]}", show_tabs=True)
            workbook = retry(lambda: server.workbooks.publish(item, str(path), mode=TSC.Server.PublishMode.Overwrite))
            server.workbooks.populate_views(workbook)
            published[role] = workbook
            report["workbooks"][role] = {
                "id": workbook.id, "name": workbook.name, "url": workbook.webpage_url,
                "views": [{"name": v.name, "id": v.id} for v in workbook.views],
            }
            print(f"Published {role}: {workbook.id}", flush=True)
            print(f"Available {role} views: " + ", ".join(v.name for v in workbook.views), flush=True)
            (evidence / "cloud-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        for state in [{"name": "default"}, *request.get("states", [])]:
            name = state["name"]
            if not name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in name):
                raise ValueError("State names must be lowercase slug strings")
            record = {"name": name, "parameters": state.get("parameters", {}), "filters": state.get("filters", {}), "views": {}, "data": []}
            suffix = "" if name == "default" else "-" + name
            for role in ("author", "replica"):
                workbook = published[role]
                view_name = state.get(f"{role}_view", request[f"{role}_view"])
                view = next(v for v in workbook.views if v.name == view_name)
                options = apply_state(TSC.ImageRequestOptions(imageresolution=TSC.ImageRequestOptions.Resolution.High, maxage=1), state)
                retry(lambda: server.views.populate_image(view, options))
                image_path = outputs / f"cloud-{role}{suffix}.png"
                image_bytes = view.image
                image_path.write_bytes(image_bytes)
                if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise ValueError("Cloud did not return PNG bytes")
                record["views"][role] = {"id": view.id, "name": view.name, "path": image_path.relative_to(case_dir).as_posix(), "sha256": digest(image_path), "size": list(struct.unpack(">II", image_bytes[16:24]))}
                for data_request in request.get("data_views", []):
                    data_view = next(v for v in workbook.views if v.name == data_request[role])
                    applied_state = csv_state(state, role, data_request)
                    csv_options = apply_state(TSC.CSVRequestOptions(maxage=1), applied_state)
                    retry(lambda: server.views.populate_csv(data_view, csv_options))
                    csv_path = outputs / f"cloud-{role}-{data_request['name']}{suffix}.csv"
                    csv_path.write_bytes(b"".join(data_view.csv))
                    record["data"].append({"role": role, "view": data_view.name, "view_id": data_view.id, "scope": data_request["scope"], **applied_state, "path": csv_path.relative_to(case_dir).as_posix(), "sha256": digest(csv_path), "bytes": csv_path.stat().st_size})
            report["states"].append(record)
            (evidence / "cloud-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(f"Captured {case['case_id']} {name}", flush=True)
    if digest(replica) != report["source_hashes"]["replica"]:
        raise AssertionError("Replica changed during Cloud capture")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="Non-secret JSON specifying case, author path, views and states")
    args = parser.parse_args()
    capture(json.loads(args.request.read_text(encoding="utf-8")))
