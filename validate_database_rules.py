
from db import get_connection

DATABASE = "yottaflex_test_db"


def validate_database_rules():

    connection = get_connection(DATABASE)

    if connection is None:
        print("Database connection failed.")
        return

    cursor = connection.cursor(dictionary=True)

    try:
        print("\nDATABASE RULE VALIDATION")
        print("Database:", connection.database)

        if connection.database != DATABASE:
            print("ERROR: Wrong database. Stopping.")
            return

        checks = {
            "Temperature below -100": """
                SELECT COUNT(*) AS total
                FROM sensor_readings
                WHERE temperature < -100
            """,

            "Temperature above 100": """
                SELECT COUNT(*) AS total
                FROM sensor_readings
                WHERE temperature > 100
            """,

            "Humidity below 0": """
                SELECT COUNT(*) AS total
                FROM sensor_readings
                WHERE humidity < 0
            """,

            "Humidity above 100": """
                SELECT COUNT(*) AS total
                FROM sensor_readings
                WHERE humidity > 100
            """,

            "Delivery before departure": """
                SELECT COUNT(*) AS total
                FROM shipments
                WHERE actual_arrival IS NOT NULL
                  AND departure_time IS NOT NULL
                  AND actual_arrival < departure_time
            """,

            "Excursion duration undercount": """
                SELECT COUNT(*) AS total
                FROM excursions
                WHERE end_time IS NOT NULL
                  AND duration_minutes <
                      TIMESTAMPDIFF(MINUTE, start_time, end_time)
            """,

            "Excursion duration overcount": """
                SELECT COUNT(*) AS total
                FROM excursions
                WHERE end_time IS NOT NULL
                  AND duration_minutes >
                      TIMESTAMPDIFF(MINUTE, start_time, end_time)
            """,

            "Policies without products": """
                SELECT COUNT(*) AS total
                FROM threshold_policies tp
                LEFT JOIN products p
                    ON tp.product_id = p.product_id
                WHERE p.product_id IS NULL
            """,

            "Readings without an active product threshold": """
                SELECT COUNT(*) AS total
                FROM sensor_readings sr
                JOIN shipments sh
                    ON sr.shipment_id = sh.shipment_id
                LEFT JOIN threshold_policies tp
                    ON tp.product_id = sh.product_id
                   AND DATE(sr.reading_time) >= tp.effective_from
                   AND (
                       tp.effective_to IS NULL
                       OR DATE(sr.reading_time) <= tp.effective_to
                   )
                WHERE tp.policy_id IS NULL
            """
        }

        print("\n========== VALIDATION RESULTS ==========")

        for name, query in checks.items():
            cursor.execute(query)
            count = cursor.fetchone()["total"]

            status = "PASS" if count == 0 else "CHECK"

            print(f"{status} | {name}: {count}")

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM sensors
            WHERE calibration_status IS NULL
               OR UPPER(TRIM(calibration_status)) <> 'CALIBRATED'
        """)

        calibration_count = cursor.fetchone()["total"]

        status = "PASS" if calibration_count == 0 else "CHECK"

        print(
            f"{status} | Non-calibrated sensors: "
            f"{calibration_count}"
        )

        print("\nRead-only validation completed.")
        print("No database records were modified.")

    except Exception as error:
        print("Validation failed:", error)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    validate_database_rules()
