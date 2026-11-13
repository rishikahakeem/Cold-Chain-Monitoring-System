
import random
import mysql.connector
from datetime import datetime, timedelta
from db import get_connection

# Reproducible data
random.seed(42)

# IMPORTANT: This generator writes ONLY to the test database.
TEST_DATABASE = "yottaflex_test_db"

TOTAL_SHIPMENTS = 1000
TOTAL_CONTAINERS = 300
READING_INTERVAL_MINUTES = 5
BATCH_SIZE = 5000

CITIES = [
    "Hyderabad", "Mumbai", "Delhi", "Bangalore",
    "Chennai", "Pune", "Kolkata", "Ahmedabad",
    "Jaipur", "Lucknow", "Nagpur", "Visakhapatnam"
]


def generate_controlled_event(sensor_number, policy_limit):
    """
    Create deterministic consecutive abnormal readings.

    The detector closes an incident when the next normal
    reading arrives. Therefore N abnormal readings at
    five-minute intervals represent approximately N * 5
    minutes of detected duration.
    """

    event_type = sensor_number % 5

    if event_type == 0:
        # Brief high-temperature event: LOW severity
        return {
            "type": "HIGH_TEMPERATURE",
            "count": 2
        }

    elif event_type == 1:
        # Above the permitted excursion duration: HIGH
        return {
            "type": "HIGH_TEMPERATURE",
            "count": int(policy_limit // 5) + 1
        }

    elif event_type == 2:
        # More than twice the permitted duration: CRITICAL
        return {
            "type": "LOW_TEMPERATURE",
            "count": int((policy_limit * 2) // 5) + 1
        }

    elif event_type == 3:
        # Prolonged high humidity: HIGH
        return {
            "type": "HIGH_HUMIDITY",
            "count": int(policy_limit // 5) + 1
        }

    else:
        # Prolonged high humidity: CRITICAL
        return {
            "type": "HIGH_HUMIDITY",
            "count": int((policy_limit * 2) // 5) + 1
        }


def generate_data():

    connection = get_connection(TEST_DATABASE)

    if not connection:
        print("Cannot connect to test database.")
        return

    cursor = connection.cursor()

    try:
        # Confirm the database before writing anything.
        cursor.execute("SELECT DATABASE()")
        selected_database = cursor.fetchone()[0]

        print("Connected database:", selected_database)

        if selected_database != TEST_DATABASE:
            print("ERROR: Wrong database. Generation cancelled.")
            return

        # Prevent accidental duplicate generation.
        cursor.execute("SELECT COUNT(*) FROM shipments")

        if cursor.fetchone()[0] > 0:
            print("Shipments already exist in the test database.")
            print("Generation stopped to prevent duplicates.")
            return

        # Fetch products and their latest policy.
        cursor.execute("""
            SELECT
                p.product_id,
                p.min_temperature,
                p.max_temperature,
                p.min_humidity,
                p.max_humidity,
                COALESCE(
                    (
                        SELECT tp.max_excursion_minutes
                        FROM threshold_policies tp
                        WHERE tp.product_id = p.product_id
                          AND tp.effective_from <= '2026-12-31'
                          AND (
                              tp.effective_to IS NULL
                              OR tp.effective_to >= '2026-01-01'
                          )
                        ORDER BY tp.effective_from DESC
                        LIMIT 1
                    ),
                    15
                ) AS max_excursion_minutes
            FROM products p
            ORDER BY p.product_id
        """)

        products = cursor.fetchall()

        if not products:
            print("No products found in test database.")
            return

        shipments = []
        containers = []
        sensors = []
        route_stops = []
        custody_events = []
        monitored_trips = []

        print("\nGenerating shipments...")

        base_date = datetime(2026, 1, 1)

        for i in range(1, TOTAL_SHIPMENTS + 1):

            shipment_id = f"SHP-{i:04d}"

            product = random.choice(products)

            product_id = product[0]
            min_temp = float(product[1])
            max_temp = float(product[2])
            min_humidity = float(product[3] or 0)
            max_humidity = float(
                product[4] if product[4] is not None else 100
            )
            policy_limit = int(product[5])

            origin = random.choice(CITIES)

            destination = random.choice([
                city for city in CITIES if city != origin
            ])

            departure = base_date + timedelta(
                days=random.randint(0, 300),
                hours=random.randint(0, 23)
            )

            duration_days = random.randint(2, 5)

            expected_arrival = departure + timedelta(
                days=duration_days
            )

            delay_hours = (
                random.randint(1, 12)
                if random.random() < 0.10
                else 0
            )

            actual_arrival = expected_arrival + timedelta(
                hours=delay_hours
            )

            shipments.append((
                shipment_id,
                product_id,
                origin,
                destination,
                departure,
                expected_arrival,
                actual_arrival,
                "DELAYED" if delay_hours else "DELIVERED"
            ))

            # Three route stops per shipment.
            middle_city = random.choice([
                city for city in CITIES
                if city not in [origin, destination]
            ])

            locations = [origin, middle_city, destination]

            trip_duration = actual_arrival - departure

            for stop_number, location in enumerate(locations):

                arrival = departure + (
                    trip_duration * stop_number / 2
                )

                leave = arrival + timedelta(hours=2)

                route_stops.append((
                    shipment_id,
                    stop_number + 1,
                    location,
                    arrival,
                    leave,
                    "COMPLETED"
                ))

            # Two custody events per shipment.
            custody_events.append((
                shipment_id,
                "PICKUP",
                "Warehouse Manager",
                origin,
                departure,
                "Shipment handed over for transportation"
            ))

            custody_events.append((
                shipment_id,
                "DELIVERY",
                "Delivery Manager",
                destination,
                actual_arrival,
                "Shipment delivery recorded"
            ))

            # First 300 shipments receive containers and sensors.
            if i <= TOTAL_CONTAINERS:

                container_id = f"CONT-{i:04d}"
                sensor_id = f"SENSOR-{i:04d}"

                containers.append((
                    container_id,
                    shipment_id,
                    "Refrigerated Container",
                    "ACTIVE"
                ))

                sensors.append((
                    sensor_id,
                    container_id,
                    "TEMPERATURE_HUMIDITY",
                    "CALIBRATED",
                    departure - timedelta(days=10)
                ))

                # Create a controlled event for this sensor.
                controlled_event = generate_controlled_event(
                    i,
                    policy_limit
                )

                # Spread event start times through each trip.
                event_start = departure + timedelta(
                    hours=6 + (i % 12)
                )

                monitored_trips.append({
                    "shipment_id": shipment_id,
                    "sensor_id": sensor_id,
                    "sensor_number": i,
                    "departure": departure,
                    "arrival": actual_arrival,
                    "min_temp": min_temp,
                    "max_temp": max_temp,
                    "min_humidity": min_humidity,
                    "max_humidity": max_humidity,
                    "policy_limit": policy_limit,
                    "event_type": controlled_event["type"],
                    "event_count": controlled_event["count"],
                    "event_start": event_start
                })

        # Insert shipments.
        print("Inserting shipments...")

        cursor.executemany("""
            INSERT INTO shipments
            (
                shipment_id,
                product_id,
                origin,
                destination,
                departure_time,
                expected_arrival,
                actual_arrival,
                shipment_status
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, shipments)

        connection.commit()

        # Insert route stops.
        print("Inserting route stops...")

        for start in range(0, len(route_stops), BATCH_SIZE):

            cursor.executemany("""
                INSERT INTO route_stops
                (
                    shipment_id,
                    stop_number,
                    location,
                    arrival_time,
                    departure_time,
                    stop_status
                )
                VALUES (%s,%s,%s,%s,%s,%s)
            """, route_stops[start:start + BATCH_SIZE])

            connection.commit()

        # Retrieve route stop IDs.
        stop_id_map = {}

        cursor.execute("""
            SELECT stop_id, shipment_id
            FROM route_stops
            ORDER BY shipment_id, stop_number
        """)

        for stop_id, shipment_id in cursor.fetchall():

            stop_id_map.setdefault(
                shipment_id, []
            ).append(stop_id)

        # Insert containers and sensors.
        print("Inserting containers and sensors...")

        cursor.executemany("""
            INSERT INTO containers
            (
                container_id,
                shipment_id,
                container_type,
                container_status
            )
            VALUES (%s,%s,%s,%s)
        """, containers)

        cursor.executemany("""
            INSERT INTO sensors
            (
                sensor_id,
                container_id,
                sensor_type,
                calibration_status,
                last_calibrated
            )
            VALUES (%s,%s,%s,%s,%s)
        """, sensors)

        connection.commit()

        # Insert custody events.
        print("Inserting custody events...")

        cursor.executemany("""
            INSERT INTO custody_events
            (
                shipment_id,
                event_type,
                responsible_person,
                event_location,
                event_time,
                remarks
            )
            VALUES (%s,%s,%s,%s,%s,%s)
        """, custody_events)

        connection.commit()

        # Generate sensor readings.
        print("Generating sensor readings...")

        reading_batch = []
        total_readings = 0
        failed_readings = 0
        random_excursion_readings = 0
        controlled_excursion_readings = 0

        for trip in monitored_trips:

            current_time = trip["departure"]
            arrival = trip["arrival"]

            stop_ids = stop_id_map[trip["shipment_id"]]

            trip_seconds = (
                arrival - trip["departure"]
            ).total_seconds()

            event_end = trip["event_start"] + timedelta(
                minutes=(
                    trip["event_count"]
                    * READING_INTERVAL_MINUTES
                )
            )

            while current_time <= arrival:

                in_controlled_event = (
                    trip["event_start"]
                    <= current_time
                    < event_end
                )

                # Never randomly skip a reading inside a
                # controlled event. This preserves its sequence.
                if (
                    not in_controlled_event
                    and random.random() < 0.001
                ):
                    current_time += timedelta(
                        minutes=READING_INTERVAL_MINUTES
                    )
                    continue

                temperature = random.uniform(
                    trip["min_temp"],
                    trip["max_temp"]
                )

                humidity = random.uniform(
                    trip["min_humidity"],
                    trip["max_humidity"]
                )

                data_status = "VALID"

                if in_controlled_event:

                    event_type = trip["event_type"]

                    if event_type == "HIGH_TEMPERATURE":

                        temperature = (
                            trip["max_temp"]
                            + random.uniform(2, 5)
                        )

                    elif event_type == "LOW_TEMPERATURE":

                        temperature = (
                            trip["min_temp"]
                            - random.uniform(2, 5)
                        )

                    elif event_type == "HIGH_HUMIDITY":

                        humidity = (
                            trip["max_humidity"]
                            + random.uniform(5, 10)
                        )

                    controlled_excursion_readings += 1

                else:

                    # Random sensor failures outside controlled events.
                    if random.random() < 0.001:

                        data_status = "SENSOR_FAILURE"
                        failed_readings += 1

                    # Random isolated temperature anomalies.
                    elif random.random() < 0.005:

                        if random.random() < 0.5:

                            temperature = (
                                trip["max_temp"]
                                + random.uniform(1, 5)
                            )

                        else:

                            temperature = (
                                trip["min_temp"]
                                - random.uniform(1, 5)
                            )

                        random_excursion_readings += 1

                    # Random isolated humidity anomalies.
                    elif random.random() < 0.003:

                        humidity = (
                            trip["max_humidity"]
                            + random.uniform(1, 10)
                        )

                        random_excursion_readings += 1

                elapsed = (
                    current_time - trip["departure"]
                ).total_seconds()

                segment = min(
                    2,
                    int((elapsed / trip_seconds) * 3)
                )

                reading_id = (
                    f"{trip['sensor_id']}-"
                    f"{current_time.strftime('%Y%m%d%H%M')}"
                )

                reading_batch.append((
                    reading_id,
                    trip["sensor_id"],
                    trip["shipment_id"],
                    stop_ids[segment],
                    round(temperature, 2),
                    round(humidity, 2),
                    current_time,
                    data_status
                ))

                if len(reading_batch) >= BATCH_SIZE:

                    cursor.executemany("""
                        INSERT INTO sensor_readings
                        (
                            reading_id,
                            sensor_id,
                            shipment_id,
                            stop_id,
                            temperature,
                            humidity,
                            reading_time,
                            data_status
                        )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """, reading_batch)

                    connection.commit()

                    total_readings += len(reading_batch)
                    reading_batch.clear()

                current_time += timedelta(
                    minutes=READING_INTERVAL_MINUTES
                )

        # Insert remaining readings.
        if reading_batch:

            cursor.executemany("""
                INSERT INTO sensor_readings
                (
                    reading_id,
                    sensor_id,
                    shipment_id,
                    stop_id,
                    temperature,
                    humidity,
                    reading_time,
                    data_status
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, reading_batch)

            connection.commit()

            total_readings += len(reading_batch)

        print("\n========== TEST DATA GENERATION COMPLETE ==========")
        print("Database:", selected_database)
        print("Shipments:", len(shipments))
        print("Containers:", len(containers))
        print("Sensors:", len(sensors))
        print("Route stops:", len(route_stops))
        print("Custody events:", len(custody_events))
        print("Sensor readings:", total_readings)
        print("Sensor failure readings:", failed_readings)
        print("Random excursion readings:", random_excursion_readings)
        print("Controlled consecutive excursion readings:",
              controlled_excursion_readings)

        print("\nGeneration completed in the TEST database only.")

    except mysql.connector.Error as error:

        connection.rollback()
        print("MySQL error:", error)

    except Exception as error:

        connection.rollback()
        print("Unexpected error:", error)

    finally:

        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_data()
