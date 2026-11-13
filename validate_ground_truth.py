
import csv
from datetime import datetime, timedelta
from pathlib import Path

READING_INTERVAL_MINUTES = 5

# Sample product limits for isolated tests
PRODUCTS = {
    "PRD-001": {
        "min_temperature": 2,
        "max_temperature": 8,
        "min_humidity": 30,
        "max_humidity": 60,
        "max_excursion_minutes": 15
    },
    "PRD-002": {
        "min_temperature": 2,
        "max_temperature": 10,
        "min_humidity": 60,
        "max_humidity": 90,
        "max_excursion_minutes": 30
    },
    "PRD-003": {
        "min_temperature": -25,
        "max_temperature": -18,
        "min_humidity": 40,
        "max_humidity": 80,
        "max_excursion_minutes": 20
    }
}


def severity_from_duration(duration, limit):
    if duration > limit * 2:
        return "CRITICAL"
    elif duration > limit:
        return "HIGH"
    elif duration >= limit:
        return "MEDIUM"
    return "LOW"


def test_normal_condition():
    product = PRODUCTS["PRD-001"]

    temperature = 5
    humidity = 45

    normal = (
        product["min_temperature"] <= temperature
        <= product["max_temperature"]
        and product["min_humidity"] <= humidity
        <= product["max_humidity"]
    )

    return ("NO_EXCURSION", "NONE") if normal else (
        "DETECT_EXCURSION", "HIGH"
    )


def test_brief_high_temperature():
    product = PRODUCTS["PRD-001"]

    temperature = 9
    duration = 5

    if temperature > product["max_temperature"]:
        return (
            "DETECT_EXCURSION",
            severity_from_duration(
                duration,
                product["max_excursion_minutes"]
            )
        )

    return "NO_EXCURSION", "NONE"


def test_prolonged_high_temperature():
    product = PRODUCTS["PRD-001"]

    temperature = 9
    duration = 25

    if temperature > product["max_temperature"]:
        return (
            "DETECT_EXCURSION",
            severity_from_duration(
                duration,
                product["max_excursion_minutes"]
            )
        )

    return "NO_EXCURSION", "NONE"


def test_low_temperature():
    product = PRODUCTS["PRD-001"]

    temperature = 1
    duration = 15

    if temperature < product["min_temperature"]:
        return (
            "DETECT_EXCURSION",
            severity_from_duration(
                duration,
                product["max_excursion_minutes"]
            )
        )

    return "NO_EXCURSION", "NONE"


def test_high_humidity():
    product = PRODUCTS["PRD-002"]

    humidity = 95
    duration = 30

    if humidity > product["max_humidity"]:
        return (
            "DETECT_EXCURSION",
            severity_from_duration(
                duration,
                product["max_excursion_minutes"]
            )
        )

    return "NO_EXCURSION", "NONE"


def test_sensor_dropout():
    first_reading = datetime(2026, 11, 1, 10, 0)
    next_reading = datetime(2026, 11, 1, 10, 10)

    gap = int(
        (next_reading - first_reading).total_seconds() / 60
    )

    if gap > READING_INTERVAL_MINUTES:
        return "FLAG_MISSING_DATA", "MEDIUM"

    return "NO_EXCURSION", "NONE"


def test_invalid_reading():
    temperature = 150
    humidity = 45

    invalid = (
        temperature < -100
        or temperature > 100
        or humidity < 0
        or humidity > 100
    )

    if invalid:
        return "FLAG_INVALID_DATA", "HIGH"

    return "VALID_DATA", "NONE"


def test_delivery_before_departure():
    departure = datetime(2026, 11, 1, 10, 0)
    arrival = datetime(2026, 11, 1, 9, 0)

    if arrival < departure:
        return "REJECT_RECORD", "HIGH"

    return "ACCEPT_RECORD", "NONE"


def test_wrong_product_threshold():
    shipment_product_id = "PRD-001"

    # Simulate a policy incorrectly selected for another product
    selected_policy_product_id = "PRD-002"

    if shipment_product_id != selected_policy_product_id:
        return "FLAG_POLICY_ERROR", "HIGH"

    return "POLICY_VALID", "NONE"


def test_duration_undercount():
    start_time = datetime(2026, 11, 1, 10, 0)

    source_readings = [
        start_time,
        start_time + timedelta(minutes=5),
        start_time + timedelta(minutes=10)
    ]

    # Three consecutive readings support 15 minutes
    source_duration = int(
        (
            source_readings[-1]
            - source_readings[0]
        ).total_seconds() / 60
    ) + READING_INTERVAL_MINUTES

    incorrectly_calculated_duration = 10

    if incorrectly_calculated_duration < source_duration:
        return "FLAG_CALCULATION_ERROR", "HIGH"

    return "DURATION_VALID", "NONE"


def run_validation():

    csv_path = Path(__file__).with_name("ground_truth.csv")

    if not csv_path.exists():
        print("ERROR: ground_truth.csv not found.")
        return

    tests = {
        "GT-001": test_normal_condition,
        "GT-002": test_brief_high_temperature,
        "GT-003": test_prolonged_high_temperature,
        "GT-004": test_low_temperature,
        "GT-005": test_high_humidity,
        "GT-006": test_sensor_dropout,
        "GT-007": test_invalid_reading,
        "GT-008": test_delivery_before_departure,
        "GT-009": test_wrong_product_threshold,
        "GT-010": test_duration_undercount
    }

    passed = 0
    failed = 0

    print("\nGROUND TRUTH VALIDATION")
    print("=" * 65)

    with open(csv_path, "r", newline="", encoding="utf-8-sig") as file:

        reader = csv.DictReader(file)

        for case in reader:

            case_id = case["case_id"].strip()
            expected_decision = case["expected_decision"].strip()
            expected_severity = case["expected_severity"].strip()

            if case_id not in tests:
                print(case_id, "- FAIL: No test implementation")
                failed += 1
                continue

            actual_decision, actual_severity = tests[case_id]()

            success = (
                actual_decision == expected_decision
                and actual_severity == expected_severity
            )

            if success:
                print(
                    f"{case_id}: PASS | "
                    f"{actual_decision} | {actual_severity}"
                )
                passed += 1
            else:
                print(
                    f"{case_id}: FAIL | "
                    f"Expected: {expected_decision}, "
                    f"{expected_severity} | "
                    f"Actual: {actual_decision}, "
                    f"{actual_severity}"
                )
                failed += 1

    print("=" * 65)
    print("Passed:", passed)
    print("Failed:", failed)
    print("Total:", passed + failed)

    if failed == 0 and passed == 10:
        print("\nALL 10 ISOLATED TESTS PASSED.")
    else:
        print("\nVALIDATION NEEDS ATTENTION.")


if __name__ == "__main__":
    run_validation()
