
from datetime import datetime, timedelta

from detection_rules import (
    check_calibration,
    check_physical_reading,
    check_shipment_dates,
    check_product_policy,
    reconcile_duration,
    check_temperature,
    check_humidity
)


def evaluate_shipment(shipment, readings):

    issues = []

    # 1. Shipment date validation
    if not check_shipment_dates(
        shipment["departure_time"],
        shipment["actual_arrival"]
    ):
        issues.append("DATE_ORDER_VIOLATION")

    # 2. Product policy validation
    if not check_product_policy(
        shipment["product_id"],
        shipment["policy_product_id"]
    ):
        issues.append("THRESHOLD_MISMATCH")

    # 3. Reading-level validation
    for reading in readings:

        if not check_calibration(reading["calibration_status"]):
            issues.append("CALIBRATION_FAILURE")
            continue

        if reading["data_status"] != "VALID":
            issues.append("SENSOR_FAILURE")
            continue

        if not check_physical_reading(
            reading["temperature"],
            reading["humidity"]
        ):
            issues.append("INVALID_READING")
            continue

        temperature_result = check_temperature(
            reading["temperature"],
            reading["min_temperature"],
            reading["max_temperature"]
        )

        humidity_result = check_humidity(
            reading["humidity"],
            reading["min_humidity"],
            reading["max_humidity"]
        )

        if temperature_result != "NORMAL":
            issues.append(temperature_result)

        if humidity_result != "NORMAL":
            issues.append(humidity_result)

    # 4. Duration reconciliation
    # A minimum of two readings is required.
    if len(readings) >= 2:

        timestamps = sorted(
            reading["reading_time"]
            for reading in readings
        )

        calculated_duration = (
            timestamps[-1] - timestamps[0]
        ).total_seconds() / 60 + 5

        if not reconcile_duration(
            timestamps,
            calculated_duration
        ):
            issues.append("DURATION_RECONCILIATION")

    return sorted(set(issues))


def run_test(name, actual, expected):

    passed = actual == expected

    print(
        f"{'PASS' if passed else 'FAIL'} | "
        f"{name} | Actual: {actual} | Expected: {expected}"
    )

    return passed


def main():

    print("\nDETECTOR DRY-RUN VALIDATION")
    print("=" * 70)

    departure = datetime(2026, 10, 1, 8, 0)

    shipment = {
        "product_id": "PRD-001",
        "policy_product_id": "PRD-001",
        "departure_time": departure,
        "actual_arrival": departure + timedelta(days=2)
    }

    base_reading = {
        "calibration_status": "CALIBRATED",
        "data_status": "VALID",
        "temperature": 5,
        "humidity": 50,
        "min_temperature": 2,
        "max_temperature": 8,
        "min_humidity": 30,
        "max_humidity": 60,
        "reading_time": departure + timedelta(minutes=5)
    }

    readings = [
        base_reading.copy(),
        {
            **base_reading,
            "reading_time": departure + timedelta(minutes=10)
        }
    ]

    tests = []

    # Normal shipment
    tests.append((
        "Normal shipment",
        evaluate_shipment(shipment, readings),
        []
    ))

    # Shipment date violation
    invalid_dates = shipment.copy()
    invalid_dates["actual_arrival"] = departure - timedelta(hours=1)

    tests.append((
        "Arrival before departure",
        evaluate_shipment(invalid_dates, readings),
        ["DATE_ORDER_VIOLATION"]
    ))

    # Product policy mismatch
    wrong_policy = shipment.copy()
    wrong_policy["policy_product_id"] = "PRD-002"

    tests.append((
        "Wrong product policy",
        evaluate_shipment(wrong_policy, readings),
        ["THRESHOLD_MISMATCH"]
    ))

    # Calibration failure
    failed_calibration = [
        {**base_reading, "calibration_status": "FAILED"}
    ]

    tests.append((
        "Calibration failure",
        evaluate_shipment(shipment, failed_calibration),
        ["CALIBRATION_FAILURE"]
    ))

    # Invalid physical temperature
    invalid_temperature = [
        {**base_reading, "temperature": 150}
    ]

    tests.append((
        "Invalid physical temperature",
        evaluate_shipment(shipment, invalid_temperature),
        ["INVALID_READING"]
    ))

    # High temperature
    high_temperature = [
        {**base_reading, "temperature": 10}
    ]

    tests.append((
        "High temperature",
        evaluate_shipment(shipment, high_temperature),
        ["HIGH_TEMPERATURE"]
    ))

    # High humidity
    high_humidity = [
        {**base_reading, "humidity": 75}
    ]

    tests.append((
        "High humidity",
        evaluate_shipment(shipment, high_humidity),
        ["HIGH_HUMIDITY"]
    ))

    # Sensor failure
    sensor_failure = [
        {**base_reading, "data_status": "SENSOR_FAILURE"}
    ]

    tests.append((
        "Sensor failure",
        evaluate_shipment(shipment, sensor_failure),
        ["SENSOR_FAILURE"]
    ))

    passed = 0
    failed = 0

    for name, actual, expected in tests:

        if run_test(name, actual, expected):
            passed += 1
        else:
            failed += 1

    print("=" * 70)
    print("Passed:", passed)
    print("Failed:", failed)
    print("Total:", passed + failed)

    if failed == 0:
        print("\nALL DETECTOR DRY-RUN TESTS PASSED.")
    else:
        print("\nDETECTOR DRY-RUN TESTS FAILED.")

    print("\nNo database connection was used.")
    print("No database records were modified.")


if __name__ == "__main__":
    main()
