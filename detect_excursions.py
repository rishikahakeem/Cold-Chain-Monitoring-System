
from db import get_connection
from datetime import timedelta
from collections import defaultdict

READING_INTERVAL_MINUTES = 5
TEST_DATABASE = "yottaflex_test_db"


def detect_excursions():

    connection = get_connection(TEST_DATABASE)

    if connection is None:
        print("Database connection failed.")
        return

    cursor = connection.cursor(dictionary=True)

    try:
        print("\nACTUAL EXCURSION DETECTION")
        print("Connected database:", connection.database)

        if connection.database != TEST_DATABASE:
            print("ERROR: Wrong database. Stopping.")
            return

        cursor.execute("SELECT COUNT(*) AS total FROM excursions")
        excursion_count = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM corrective_actions"
        )
        action_count = cursor.fetchone()["total"]

        if excursion_count > 0 or action_count > 0:
            print("Existing results found.")
            print("Excursions:", excursion_count)
            print("Corrective actions:", action_count)
            print("Stopping to prevent duplicate records.")
            return

        query = """
            SELECT
                sr.reading_id,
                sr.sensor_id,
                sr.shipment_id,
                sr.temperature,
                sr.humidity,
                sr.reading_time,
                sr.data_status,
                s.calibration_status,
                p.min_temperature,
                p.max_temperature,
                p.min_humidity,
                p.max_humidity,
                COALESCE(
                    (
                        SELECT tp.max_excursion_minutes
                        FROM threshold_policies tp
                        WHERE tp.product_id = p.product_id
                          AND DATE(sr.reading_time) >= tp.effective_from
                          AND (
                              tp.effective_to IS NULL
                              OR DATE(sr.reading_time) <= tp.effective_to
                          )
                        ORDER BY tp.effective_from DESC
                        LIMIT 1
                    ),
                    15
                ) AS max_excursion_minutes
            FROM sensor_readings sr
            JOIN sensors s
                ON sr.sensor_id = s.sensor_id
            JOIN shipments sh
                ON sr.shipment_id = sh.shipment_id
            JOIN products p
                ON sh.product_id = p.product_id
            ORDER BY sr.sensor_id, sr.reading_time
        """

        cursor.execute(query)
        readings = cursor.fetchall()

        print("Total readings fetched:", len(readings))

        active = {}
        previous = {}
        detected = []

        def close_incident(key, end_time):

            incident = active.pop(key)

            duration = max(
                READING_INTERVAL_MINUTES,
                int(
                    (
                        end_time - incident["start_time"]
                    ).total_seconds() / 60
                )
            )

            limit = incident["max_excursion_minutes"]

            if key[1] == "CALIBRATION_FAILURE":
                severity = "HIGH"
            elif duration > limit * 2:
                severity = "CRITICAL"
            elif duration > limit:
                severity = "HIGH"
            elif duration >= limit:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            detected.append({
                "sensor_id": key[0],
                "shipment_id": incident["shipment_id"],
                "excursion_type": key[1],
                "start_time": incident["start_time"],
                "end_time": end_time,
                "duration_minutes": duration,
                "maximum_temperature": incident["maximum_temperature"],
                "maximum_humidity": incident["maximum_humidity"],
                "severity": severity
            })

        for reading in readings:

            sensor_id = reading["sensor_id"]
            shipment_id = reading["shipment_id"]
            current_time = reading["reading_time"]
            temperature = reading["temperature"]
            humidity = reading["humidity"]

            previous_reading = previous.get(sensor_id)

            if previous_reading:

                if previous_reading["shipment_id"] != shipment_id:

                    for key in list(active):
                        if key[0] == sensor_id:
                            close_incident(
                                key,
                                previous_reading["reading_time"]
                                + timedelta(minutes=5)
                            )

                    previous_reading = None

                else:
                    gap = int(
                        (
                            current_time
                            - previous_reading["reading_time"]
                        ).total_seconds() / 60
                    )

                    if gap > READING_INTERVAL_MINUTES:

                        gap_start = (
                            previous_reading["reading_time"]
                            + timedelta(minutes=5)
                        )

                        for key in list(active):
                            if key[0] == sensor_id:
                                close_incident(key, gap_start)

                        detected.append({
                            "sensor_id": sensor_id,
                            "shipment_id": shipment_id,
                            "excursion_type": "MISSING_DATA",
                            "start_time": gap_start,
                            "end_time": current_time,
                            "duration_minutes": gap - 5,
                            "maximum_temperature": None,
                            "maximum_humidity": None,
                            "severity": "MEDIUM"
                        })

            violations = []

            calibration_status = (
                reading["calibration_status"] or ""
            ).strip().upper()

            if calibration_status != "CALIBRATED":
                violations.append("CALIBRATION_FAILURE")

            if reading["data_status"] != "VALID":
                violations.append("SENSOR_FAILURE")

            elif calibration_status == "CALIBRATED":

                if (
                    temperature is not None
                    and temperature > reading["max_temperature"]
                ):
                    violations.append("HIGH_TEMPERATURE")

                if (
                    temperature is not None
                    and temperature < reading["min_temperature"]
                ):
                    violations.append("LOW_TEMPERATURE")

                if (
                    humidity is not None
                    and reading["max_humidity"] is not None
                    and humidity > reading["max_humidity"]
                ):
                    violations.append("HIGH_HUMIDITY")

                if (
                    humidity is not None
                    and reading["min_humidity"] is not None
                    and humidity < reading["min_humidity"]
                ):
                    violations.append("LOW_HUMIDITY")

            for key in list(active):
                if key[0] == sensor_id and key[1] not in violations:
                    close_incident(key, current_time)

            for violation in violations:

                key = (sensor_id, violation)

                if key not in active:

                    active[key] = {
                        "shipment_id": shipment_id,
                        "start_time": current_time,
                        "max_excursion_minutes":
                            reading["max_excursion_minutes"],
                        "maximum_temperature": temperature,
                        "maximum_humidity": humidity
                    }

                else:
                    if temperature is not None:
                        old_temp = active[key]["maximum_temperature"]

                        if old_temp is None or temperature > old_temp:
                            active[key]["maximum_temperature"] = temperature

                    if humidity is not None:
                        old_humidity = active[key]["maximum_humidity"]

                        if (
                            old_humidity is None
                            or humidity > old_humidity
                        ):
                            active[key]["maximum_humidity"] = humidity

            previous[sensor_id] = {
                "shipment_id": shipment_id,
                "reading_time": current_time
            }

        for key in list(active):

            last_reading = previous[key[0]]["reading_time"]

            close_incident(
                key,
                last_reading + timedelta(minutes=5)
            )

        print("Detected incidents:", len(detected))

        excursion_number = 1
        actions_created = 0

        for incident in detected:

            excursion_id = f"EXC-{excursion_number:06d}"
            excursion_number += 1

            cursor.execute(
                """
                INSERT INTO excursions (
                    excursion_id,
                    shipment_id,
                    sensor_id,
                    excursion_type,
                    start_time,
                    end_time,
                    duration_minutes,
                    maximum_temperature,
                    maximum_humidity,
                    excursion_status,
                    severity
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                """,
                (
                    excursion_id,
                    incident["shipment_id"],
                    incident["sensor_id"],
                    incident["excursion_type"],
                    incident["start_time"],
                    incident["end_time"],
                    incident["duration_minutes"],
                    incident["maximum_temperature"],
                    incident["maximum_humidity"],
                    "OPEN",
                    incident["severity"]
                )
            )

            if incident["severity"] in ("HIGH", "CRITICAL"):

                description = (
                    f"{incident['severity']} {incident['excursion_type']} "
                    f"incident detected for sensor "
                    f"{incident['sensor_id']}. "
                    f"Duration: {incident['duration_minutes']} minutes. "
                    "Investigate the shipment and take corrective action."
                )

                cursor.execute(
                    """
                    INSERT INTO corrective_actions (
                        excursion_id,
                        shipment_id,
                        action_description,
                        assigned_to,
                        action_status
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        excursion_id,
                        incident["shipment_id"],
                        description,
                        None,
                        "PENDING"
                    )
                )

                actions_created += 1

        connection.commit()

        excursion_summary = defaultdict(int)
        severity_summary = defaultdict(int)

        for incident in detected:
            excursion_summary[incident["excursion_type"]] += 1
            severity_summary[incident["severity"]] += 1

        print("\n========== SAVING RESULTS ==========")

        print("\nExcursion summary:")
        for name, count in sorted(excursion_summary.items()):
            print(name, ":", count)

        print("\nSeverity summary:")
        for name, count in sorted(severity_summary.items()):
            print(name, ":", count)

        print("\nTotal excursions saved:", len(detected))
        print("Corrective actions created:", actions_created)
        print("Database changes committed successfully.")

    except Exception as error:
        connection.rollback()
        print("Detection failed. Changes rolled back.")
        print("Error:", error)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    detect_excursions()
