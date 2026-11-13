
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


def evaluate_reading(reading):
    if not check_calibration(reading["calibration_status"]):
        return "CALIBRATION_FAILURE"

    if reading["data_status"] != "VALID":
        return "SENSOR_FAILURE"

    if not check_physical_reading(
        reading["temperature"],
        reading["humidity"]
    ):
        return "INVALID_READING"

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
        return temperature_result

    if humidity_result != "NORMAL":
        return humidity_result

    return "NORMAL"


def run_test(name, actual, expected):
    result = "PASS" if actual == expected else "FAIL"
    print(f"{result} | {name} | Actual: {actual} | Expected: {expected}")
    return result == "PASS"


def main():
    print("\nCOMBINED DETECTION RULE INTEGRATION TEST")
    print("=" * 65)

    passed = 0
    failed = 0

    base_reading = {
        "calibration_status": "CALIBRATED",
        "data_status": "VALID",
        "temperature": 5,
        "humidity": 50,
        "min_temperature": 2,
        "max_temperature": 8,
        "min_humidity": 30,
        "max_humidity": 60
    }

    scenarios = [
        ("Normal reading", {}, "NORMAL"),
        ("Calibration failure", {"calibration_status": "FAILED"},
         "CALIBRATION_FAILURE"),
        ("Sensor failure", {"data_status": "SENSOR_FAILURE"},
         "SENSOR_FAILURE"),
        ("Invalid temperature", {"temperature": 101},
         "INVALID_READING"),
        ("High temperature", {"temperature": 10},
         "HIGH_TEMPERATURE"),
        ("Low temperature", {"temperature": 0},
         "LOW_TEMPERATURE"),
        ("High humidity", {"humidity": 70},
         "HIGH_HUMIDITY"),
        ("Low humidity", {"humidity": 10},
         "LOW_HUMIDITY")
    ]

    for name, changes, expected in scenarios:
        reading = base_reading.copy()
        reading.update(changes)

        if run_test(name, evaluate_reading(reading), expected):
            passed += 1
        else:
            failed += 1

    departure = datetime(2026, 10, 1, 8, 0)
    arrival = departure + timedelta(days=2)

    checks = [
        (
            "Valid shipment dates",
            check_shipment_dates(departure, arrival),
            True
        ),
        (
            "Arrival before departure",
            check_shipment_dates(arrival, departure),
            False
        ),
        (
            "Matching product policy",
            check_product_policy("PRD-001", "PRD-001"),
            True
        ),
        (
            "Mismatched product policy",
            check_product_policy("PRD-001", "PRD-002"),
            False
        ),
        (
            "Duration correctly reconciled",
            reconcile_duration(
                [departure, departure + timedelta(minutes=25)],
                30
            ),
            True
        ),
        (
            "Duration undercount detected",
            reconcile_duration(
                [departure, departure + timedelta(minutes=25)],
                20
            ),
            False
        )
    ]

    for name, actual, expected in checks:
        if run_test(name, actual, expected):
            passed += 1
        else:
            failed += 1

    print("=" * 65)
    print("Passed:", passed)
    print("Failed:", failed)
    print("Total:", passed + failed)

    if failed == 0:
        print("\nALL COMBINED RULE INTEGRATION TESTS PASSED.")
    else:
        print("\nINTEGRATION TESTS FAILED.")


if __name__ == "__main__":
    main()
