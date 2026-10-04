"""Independent raw profit oracle plus native map/action and Cloud export checks."""

from pathlib import Path
from collections import defaultdict
from zipfile import ZipFile
import csv, hashlib, json, math
from lxml import etree as E
from tableauhyperapi import HyperProcess, Connection, Telemetry

HERE = Path(__file__).resolve().parent
ACCEPTANCE = [
    "complete-state-city-profit",
    "native-layer-size-highlight",
    "cloud-layout-data",
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def oracle():
    with (
        HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h,
        Connection(h.endpoint, str(next((HERE / "inputs").glob("*.hyper")))) as c,
    ):
        raw = c.execute_list_query(
            'SELECT "City","State","Profit" FROM "Extract"."Extract"'
        )
    cities = defaultdict(float)
    states = defaultdict(float)
    for city, state, profit in raw:
        cities[(state, city)] += profit
        states[state] += profit
    assert len(raw) == 9994
    assert math.isclose(sum(cities.values()), sum(states.values()), abs_tol=1e-7)
    return {
        "raw_rows": len(raw),
        "state_count": len(states),
        "city_state_count": len(cities),
        "total_profit": sum(states.values()),
        "cities": [
            {
                "state": s,
                "city": c,
                "profit": p,
                "positive": p >= 0,
                "absolute_size": abs(p),
                "positive_profit": p if p >= 0 else None,
                "negative_profit": p if p < 0 else None,
            }
            for (s, c), p in sorted(cities.items())
        ],
        "states": [{"state": s, "profit": p} for s, p in sorted(states.items())],
    }


def native():
    with ZipFile(HERE / "outputs/replicated-workbook.twbx") as z:
        r = E.fromstring(z.read(next(n for n in z.namelist() if n.endswith(".twb"))))
    m = r.find('./worksheets/worksheet[@name="Map"]')
    b = r.find('./worksheets/worksheet[@name="Bar"]')
    assert m is not None and b is not None
    panes = m.findall("table/panes/pane")
    assert len(panes) == 3
    assert panes[1].get("inert") == "true"
    assert panes[1].find("encodings/geometry") is not None
    assert panes[2].find("mark").get("class") == "Circle"
    assert panes[2].find("encodings/size") is not None
    assert any("City" in x.get("column", "") for x in panes[2].findall("encodings/lod"))
    assert any(
        "State" in x.get("column", "") for x in panes[2].findall("encodings/lod")
    )
    size = m.find('table/style/style-rule[@element="mark"]/encoding[@attr="size"]')
    assert size.get("type") == "centersize" and float(size.get("min-size")) == 0
    palette = m.find('table/style/style-rule[@element="mark"]/encoding[@attr="color"]')
    assert (
        palette.get("palette") == "red_black_10_0" and float(palette.get("center")) == 0
    )
    columns = r.findall("./datasources/datasource/column")
    f = {
        x.get("caption", x.get("name")): x.find("calculation").get("formula")
        for x in columns
        if x.find("calculation") is not None
    }
    assert f["Profit +ve?"] == "SUM([Profit])>=0"
    assert f["Loss Sort"] == "-[Profit]"
    loss = next(
        x.get("name").strip("[]") for x in columns if x.get("caption") == "Loss Sort"
    )
    sort = b.find("table/view/shelf-sorts/shelf-sort-v2")
    assert sort is not None and sort.get("direction") == "DESC"
    assert f"[sum:{loss}:qk]" in sort.get("measure-to-sort-by"), (
        "Largest city loss must sort first"
    )
    assert f["+ve Profit"].startswith("IF ") and f["-ve Profit"].startswith("IF NOT(")
    action = r.find("./actions/action")
    assert (
        action.find("activation").get("type") == "on-hover"
        and action.find("activation").get("auto-clear") == "true"
    )
    assert action.find("source").get("worksheet") == "Bar"
    assert action.find("command").get("command") == "tsc:brush"
    fields = action.find('command/param[@name="field-captions"]').get("value")
    assert "City" in fields and "State Abbrev" in fields
    assert action.find('command/param[@name="exclude"]').get("value") == "Bar"
    size = r.find("./dashboards/dashboard/size")
    assert int(size.get("maxwidth")) == 1366 and int(size.get("maxheight")) == 768
    return {
        "state_inert": True,
        "city_circle": True,
        "centered_absolute_size": True,
        "red_black_center_zero": True,
        "hover_highlight_artifact_only": True,
    }


def number(raw):
    if raw == "":
        return None
    value = raw.replace("$", "").replace(",", "").strip()
    return -float(value[1:-1]) if value.startswith("(") else float(value)


def check_value(raw, expected, key):
    actual = number(raw)
    if expected is None:
        assert actual is None, (key, raw, expected)
    else:
        assert actual is not None and abs(actual - expected) <= 0.501, (
            key,
            raw,
            expected,
        )


def cloud(data):
    path = HERE / "evidence/cloud-verification.json"
    if not path.exists():
        return {"status": "pending"}
    proof = json.loads(path.read_text())
    assert proof["source_hashes"]["replica"] == sha(
        HERE / "outputs/replicated-workbook.twbx"
    )
    export = json.loads((HERE / "evidence/export-provenance.json").read_text())
    assert proof["source_hashes"]["author"] == export["export_sha256"]
    assert proof["browser_interaction_executed"] is False
    assert len(proof["states"]) == 1 and proof["states"][0]["name"] == "default"
    records = list(proof["states"][0]["views"].values()) + proof["states"][0]["data"]
    assert len(records) == 6
    for record in records:
        assert sha(HERE / record["path"]) == record["sha256"]
    city_oracle = {(x["state"], x["city"]): x for x in data["cities"]}
    state_oracle = {x["state"]: x["profit"] for x in data["states"]}
    with (HERE / "inputs/state-abbreviations.csv").open(
        encoding="utf8", newline=""
    ) as handle:
        reverse = {x["abbreviation"]: x["state"] for x in csv.DictReader(handle)}
    checks = []
    for role in ("author", "replica"):
        for view in ("map", "bar"):
            p = HERE / f"outputs/cloud-{role}-{view}.csv"
            with p.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            seen_city, seen_state = set(), set()
            for row in rows:
                city = row["City"]
                if view == "map" and not city:
                    state = row["State"]
                    assert state not in seen_state
                    seen_state.add(state)
                    check_value(row["Profit"], state_oracle[state], (role, state))
                    continue
                state = row["State"] if view == "map" else reverse[row["State Abbrev"]]
                key = (state, city)
                assert key not in seen_city
                seen_city.add(key)
                expected = city_oracle[key]
                for field, oracle_field in (
                    ("Profit", "profit"),
                    ("+ve Profit", "positive_profit"),
                    ("-ve Profit", "negative_profit"),
                ):
                    check_value(row[field], expected[oracle_field], (role, key, field))
                assert row["Profit +ve?"].lower() == str(expected["positive"]).lower()
            assert seen_city == set(city_oracle)
            assert seen_state == (set(state_oracle) if view == "map" else set())
            checks.append(
                {
                    "file": p.name,
                    "rows": len(rows),
                    "city_keys": len(seen_city),
                    "state_keys": len(seen_state),
                    "status": "pass",
                    "sha256": sha(p),
                }
            )
    return {
        "status": "passed",
        "checks": checks,
        "numeric_scope": "Complete 604 city-state profits and 49 state profits; zero-decimal dollars checked within 0.501 rounding tolerance. Actions are native artifact contracts only.",
    }


def verify():
    data = oracle()
    contract = native()
    rest = cloud(data)
    (HERE / "outputs/data-oracle.json").write_text(
        json.dumps(data, indent=2), encoding="utf8"
    )
    result = {
        "status": "pass",
        "acceptance_ids": ACCEPTANCE,
        "artifact_sha256": sha(HERE / "outputs/replicated-workbook.twbx"),
        "raw_oracle": {k: v for k, v in data.items() if k not in ("cities", "states")},
        "native": contract,
        "cloud": rest,
    }
    (HERE / "evidence/functional-verification.json").write_text(
        json.dumps(result, indent=2), encoding="utf8"
    )
    print("PASS WW04 raw/native; Cloud=" + rest["status"])


if __name__ == "__main__":
    verify()
