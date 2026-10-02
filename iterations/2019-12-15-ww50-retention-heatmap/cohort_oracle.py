"""Independent SQL oracle across every legal model length; no workbook parsing."""
from pathlib import Path
import json
from tableauhyperapi import HyperProcess, Telemetry, Connection
HERE = Path(__file__).resolve().parent

def compute():
    source = next((HERE / "inputs").glob("*.hyper"))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process, Connection(process.endpoint, str(source)) as connection:
        table = connection.catalog.get_table_names("Extract")[0]
        rows = connection.execute_list_query(f'''WITH first_order AS (
            SELECT "customer_id", MIN("order_week") AS cohort FROM {table} GROUP BY "customer_id"
        ), sizes AS (SELECT cohort, COUNT(*) AS size FROM first_order GROUP BY cohort)
        SELECT first_order.cohort, DATEDIFF('day', first_order.cohort, orders."order_week") / 7 AS week,
            COUNT(DISTINCT orders."customer_id"), MAX(sizes.size), COUNT(*)
        FROM {table} orders JOIN first_order ON orders."customer_id"=first_order."customer_id"
        JOIN sizes ON sizes.cohort=first_order.cohort GROUP BY first_order.cohort, week ORDER BY first_order.cohort, week''')
        record_count = int(connection.execute_scalar_query(f"SELECT COUNT(*) FROM {table}"))
        unique_customers = int(connection.execute_scalar_query(f'SELECT COUNT(DISTINCT "customer_id") FROM {table}'))
        non_mondays = int(connection.execute_scalar_query(f'''SELECT COUNT(*) FROM {table} WHERE EXTRACT(ISODOW FROM "order_week") <> 1'''))
    assert record_count == 359574 and non_mondays == 0
    cells = {}
    for cohort, week, count, size, records in rows:
        key = str(cohort)
        week = int(week)
        cells[(key, week)] = {"cohort": key, "week": week, "returning_customers": int(count), "new_customers": int(size), "records": int(records), "retention": int(count) / int(size), "row_repeated_denominator_diagnostic": int(count) / (int(size) * int(records))}
        assert count <= size and count == records, "exactly one order per customer/week"
    cohorts = sorted({key for key, week in cells})
    states = {}
    for period in range(10, 27):
        complete = [cohort for cohort in cohorts if (cohort, period) in cells and cells[(cohort, period)]["returning_customers"] > 0]
        matrix = [cells[(cohort, week)] for cohort in reversed(complete) for week in range(1, period)]
        bars = [cells[(cohort, period)] for cohort in reversed(complete)]
        assert len(matrix) == len(complete) * (period - 1)
        returning = sum(cell["returning_customers"] for cell in bars)
        denominator = sum(cell["new_customers"] for cell in bars)
        states[str(period)] = {"cohorts": len(complete), "matrix_cells": len(matrix), "matrix": matrix, "bars": bars,
            "ban": {"returning_customers": returning, "new_customers": denominator, "retention": returning / denominator,
                "row_repeated_denominator_diagnostic": returning / sum(cell["records"] * cell["new_customers"] for cell in bars)}}
    return {"all_cells": list(cells.values()), "source_records": record_count, "source_customers": unique_customers, "source_cohorts": len(cohorts), "non_monday_records": non_mondays, "periods": states}

if __name__ == "__main__":
    result = compute()
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/data-contract.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print({period: {key: value for key, value in result["periods"][period].items() if key not in ["matrix", "bars"]} for period in ["10", "18", "26"]})
