
import csv
from pathlib import Path

from db import get_connection

TEST_DATABASE = "yottaflex_test_db"

EXPORT_DIR = Path(__file__).resolve().parent / "exports"

TABLES = [
    "products",
    "threshold_policies",
    "shipments",
    "containers",
    "sensors",
    "route_stops",
    "custody_events",
    "sensor_readings",
    "excursions",
    "corrective_actions",
]


def export_table(cursor, table_name):

    # Table names are selected only from the fixed allowlist above.
    cursor.execute(f"SELECT * FROM `{table_name}`")

    columns = [column[0] for column in cursor.description]

    output_path = EXPORT_DIR / f"{table_name}.csv"

    row_count = 0

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        writer.writerow(columns)

        while True:

            rows = cursor.fetchmany(5000)

            if not rows:
                break

            writer.writerows(rows)

            row_count += len(rows)

    print(
        f"EXPORTED | {table_name} | "
        f"{row_count} records | {output_path.name}"
    )

    return row_count


def main():

    print("\nCOLD CHAIN TEST DATA EXPORT")
    print("=" * 65)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    connection = get_connection(TEST_DATABASE)

    if connection is None:
        print("ERROR: Database connection failed.")
        return

    cursor = None

    try:

        cursor = connection.cursor()

        cursor.execute("SELECT DATABASE()")
        selected_database = cursor.fetchone()[0]

        print("Connected database:", selected_database)

        if selected_database != TEST_DATABASE:
            print("ERROR: Wrong database. Export cancelled.")
            return

        total_records = 0

        for table_name in TABLES:

            total_records += export_table(
                cursor,
                table_name
            )

        print("\n" + "=" * 65)
        print("EXPORT COMPLETED")
        print("Database:", selected_database)
        print("Tables exported:", len(TABLES))
        print("Total records exported:", total_records)
        print("Export folder:", EXPORT_DIR)
        print("\nDatabase records were not modified.")

    except Exception as error:

        print("EXPORT FAILED:", error)

    finally:

        if cursor:
            cursor.close()

        connection.close()


if __name__ == "__main__":
    main()
