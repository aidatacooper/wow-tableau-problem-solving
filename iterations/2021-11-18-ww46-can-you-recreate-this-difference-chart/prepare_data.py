"""Add a typed NULL spacer to extracted rows, without accessing any workbook."""
from pathlib import Path
from tableauhyperapi import Connection, HyperProcess, Telemetry, CreateMode, TableDefinition, TableName, SqlType, Inserter
HERE = Path(__file__).resolve().parent
RAW = HERE / 'inputs/federated_1vsdkg41w50rva1bkcpyx0.hyper'
DERIVED = HERE / 'inputs/sales-with-spacer.hyper'
def prepare():
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process:
        with Connection(process.endpoint, str(RAW)) as connection:
            rows = connection.execute_list_query('SELECT "Order Date", "Segment", "Category", "Sales" FROM "Extract"."Extract"')
        table = TableDefinition(TableName('Extract', 'Extract'), [
            TableDefinition.Column('Order Date', SqlType.date()),
            TableDefinition.Column('Segment', SqlType.text()),
            TableDefinition.Column('Category', SqlType.text()),
            TableDefinition.Column('Sales', SqlType.double()),
            TableDefinition.Column('Spacer', SqlType.double()),
        ])
        with Connection(process.endpoint, str(DERIVED), CreateMode.CREATE_AND_REPLACE) as connection:
            connection.catalog.create_schema('Extract')
            connection.catalog.create_table(table)
            with Inserter(connection, table) as insert:
                insert.add_rows([*row, None] for row in rows)
                insert.execute()
    print(f'Prepared {len(rows)} unchanged sales rows plus nullable Spacer')
if __name__ == '__main__': prepare()
