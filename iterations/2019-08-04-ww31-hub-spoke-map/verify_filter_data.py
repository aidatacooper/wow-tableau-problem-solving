"""Independent Hyper evidence for the declared Artist/Region word-cloud filter contract."""
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from tableauhyperapi import Connection, HyperProcess, TableName, Telemetry

CASE = Path(__file__).resolve().parent

def literal(value):
    return "'" + value.replace("'", "''") + "'"

def verify(output=None):
    hyper = CASE / "inputs/2019_07_31_PD25_WWPD_MusicData_Output.hyper"
    regions = CASE / "inputs/region-members.csv"
    lock = json.loads((CASE / "inputs/source-lock.json").read_text())
    for item in lock["extracted_data"]:
        assert sha256((CASE / item["file"]).read_bytes()).hexdigest() == item["sha256"]
    with regions.open(newline="") as file:
        groups = list(csv.DictReader(file))
    region = "CASE \"Location\" " + " ".join("WHEN " + literal(row["Location"]) + " THEN " + literal(row["Region"]) for row in groups) + " ELSE 'Other' END"
    cte = 'WITH data AS (SELECT "Artist" AS artist, ' + region + ' AS region, "Fellow Artist" AS fellow, "ConcertID" AS concert FROM ' + str(TableName("Extract", "Extract")) + ') '
    aggregate = 'SELECT region, fellow, COUNT(fellow) FROM data WHERE fellow IS NOT NULL {restriction} GROUP BY region, fellow ORDER BY region, fellow'
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process:
        with Connection(process.endpoint, str(hyper)) as connection:
            baseline = connection.execute_list_query(cte + aggregate.format(restriction=""))
            detailed = connection.execute_list_query(cte + 'SELECT artist, region, fellow, COUNT(fellow) FROM data WHERE fellow IS NOT NULL GROUP BY artist, region, fellow')
            states = []
            for artist, area, expected in [("Ben Howard", "Europe", 111), ("Ed Sheeran", "North America", 605)]:
                restriction = ' AND artist=' + literal(artist) + ' AND region=' + literal(area)
                sql_rows = connection.execute_list_query(cte + aggregate.format(restriction=restriction))
                independently_selected = sorted([[row[1], row[2], row[3]] for row in detailed if row[0] == artist and row[1] == area])
                assert {tuple(row[:2]): row[2] for row in sql_rows} == {tuple(row[:2]): row[2] for row in independently_selected} and sql_rows, "Artist/Region selection must address both fields"
                distinct_concerts = connection.execute_scalar_query(cte + 'SELECT COUNT(DISTINCT concert) FROM data WHERE artist=' + literal(artist) + ' AND region=' + literal(area))
                assert distinct_concerts == expected
                assert sql_rows != baseline, "Selected word cloud must differ from all artists/regions"
                states.append({"artist": artist, "region": area, "distinct_concerts": distinct_concerts, "wordcloud_group_count": len(sql_rows), "wordcloud_count_total": sum(row[2] for row in sql_rows), "sql_matches_independent_selection": True})
            cleared = connection.execute_list_query(cte + aggregate.format(restriction=""))
            assert cleared == baseline
    report = {"verified_at": datetime.now(timezone.utc).isoformat(), "acceptance_scope": "cloud_rest_and_artifact_contracts", "browser_interaction_executed": False, "input_sha256": {"hyper": sha256(hyper.read_bytes()).hexdigest(), "region_members": sha256(regions.read_bytes()).hexdigest()}, "baseline_group_count": len(baseline), "baseline_wordcloud_count_total": sum(row[2] for row in baseline), "filter_states": states, "removing_artist_and_region_restrictions_restores_baseline": True, "query_template": cte + aggregate, "scope": "Independent SQL checks selected input aggregation and declared auto-clear/remove-filter semantics. Does not execute hover events, browser clearing, or claim REST filter screenshots were obtained.", "passed": True}
    if output:
        output.write_text(json.dumps(report, indent=2) + "\n")
    return report

if __name__ == "__main__":
    print(json.dumps(verify(CASE / "evidence/wordcloud-filter-data.json"), indent=2))
