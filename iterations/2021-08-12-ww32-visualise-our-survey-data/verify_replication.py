"""Check distinct respondent oracles and native survey workbook contracts."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from tableauhyperapi import HyperProcess, Connection, Telemetry

HERE = Path(__file__).resolve().parent
ACCEPTANCE = ["ww32-distinct-respondents", "ww32-filtered-percentages",
              "ww32-neutral-halves", "ww32-answer-ranking", "ww32-native-actions"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle(rows):
    population = {r[0] for r in rows}
    groups = defaultdict(lambda: defaultdict(set))
    for respondent, track, frequency, question, answer in rows:
        if answer is not None and answer != "N/A":
            groups[question][answer].add(respondent)
    result = {}
    for question, answers in groups.items():
        total = len(set().union(*answers.values()))
        counts = {answer: len(ids) for answer, ids in answers.items()}
        assert sum(counts.values()) == total, "respondent gives multiple answers to one question"
        shares = {answer: count / total for answer, count in counts.items()}
        assert abs(sum(shares.values()) - 1) < 1e-12
        neutral = shares.get("Neither Agree nor Disagree", 0)
        left = sum(shares.get(a, 0) for a in ("Disagree", "Strongly Disagree")) + neutral / 2
        right = sum(shares.get(a, 0) for a in ("Agree", "Strongly Agree")) + neutral / 2
        if question.startswith("I ") or question.startswith("The challenges"):
            if set(answers) <= {"Disagree", "Strongly Disagree", "Neither Agree nor Disagree", "Agree", "Strongly Agree"}:
                assert abs(left + right - 1) < 1e-12
        ranks = {answer: n for n, answer in enumerate(sorted(counts, key=lambda a: (-counts[a], a)), 1)}
        assert sorted(ranks.values()) == list(range(1, len(answers) + 1))
        result[question] = {"counts": counts, "shares": shares, "rank_with_alphabetic_ties": ranks,
                            "negative_width": left, "positive_width": right}
    return {"respondents": len(population), "questions": result,
            "tracks": {k:len({r[0] for r in rows if r[1]==k}) for k in {r[1] for r in rows}},
            "frequencies": {k:len({r[0] for r in rows if r[2]==k}) for k in {r[2] for r in rows}}}


def verify():
    lock = json.loads((HERE / "inputs/source-lock.json").read_text(encoding="utf-8"))
    for item in lock["extracted_data"]:
        assert digest(HERE / item["file"]) == item["sha256"]
    data = next((HERE / "inputs").glob("*.hyper"))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h, Connection(h.endpoint, str(data)) as c:
        table = c.catalog.get_table_names("Extract")[0]
        rows = c.execute_list_query(f"SELECT * FROM {table}")
    assert len(rows) == 1134
    assert len({r[0] for r in rows}) == 63
    assert {t: len({r[0] for r in rows if r[1] == t}) for t in {r[1] for r in rows}} == {"Both": 11, "PBI": 10, "Tableau": 42}
    states = {"default": oracle(rows)}
    for track in ("Both", "PBI", "Tableau"):
        states[track] = oracle([r for r in rows if r[1] == track])
        for frequency in {r[2] for r in rows}:
            selected = [r for r in rows if r[1] == track and r[2] == frequency]
            if selected:
                states[track + ":" + frequency] = oracle(selected)
    output = HERE / "outputs/replicated-workbook.twbx"
    with ZipFile(output) as z:
        root = etree.fromstring(z.read(next(n for n in z.namelist() if n.endswith(".twb"))))
    assert len(root.findall("./worksheets/worksheet")) == 5
    fields = {c.get("caption", c.get("name")): c for c in root.findall("./datasources/datasource/column")}
    assert fields["Respondents"].find("calculation").get("formula") == "COUNTD([Respondent])"
    assert "TOTAL(COUNTD([Respondent]))" in fields["Answer Share"].find("calculation").get("formula")
    for field in ("Positive Share", "Negative Share"):
        assert "Neither Agree nor Disagree" in fields[field].find("calculation").get("formula")
        assert "/2" in fields[field].find("calculation").get("formula")
    assert "RANK_UNIQUE" in fields["Answer Rank"].find("calculation").get("formula")
    actions = root.findall("./actions/action")
    filters = [a for a in actions if a.find("command").get("command") == "tsc:tsl-filter"]
    assert len(filters) == 8, "each selector must filter four target sheets"
    assert len([a for a in actions if a.find("activation").get("type") == "on-hover"]) == 1
    evidence = {"scope": "Raw-data oracle and workbook structure; Desktop/Cloud tracked separately.",
                "acceptance": ACCEPTANCE, "output_sha256": digest(output), "states": states}
    (HERE / "outputs/independent-verification.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"PASS: 63 respondents, 1134 rows, {len(states)} independently calculated filter states, 8 filter actions")
    return evidence


if __name__ == "__main__":
    verify()
