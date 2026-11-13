
from datetime import datetime

from detection_rules import (
    check_calibration,
    check_physical_reading,
    check_shipment_dates,
    check_product_policy,
    reconcile_duration,
    check_temperature,
    check_humidity
)


def run_tests():

    source_readings = [
        datetime(2026, 11, 1, 10, 0),
        datetime(2026, 11, 1, 10, 5),
        datetime(2026, 11, 1, 10, 10)
    ]

    tests = [

        # 1. Calibration tests
        ("Calibrated sensor",
         check_calibration("CALIBRATED") is True),

        ("Failed calibration",
         check_calibration("FAILED") is False),

        ("Missing calibration",
         check_calibration(None) is False),

        # 2. Physical reading tests
        ("Valid physical reading",
         check_physical_reading(5, 45) is True),

        ("Invalid temperature",
         check_physical_reading(150, 45) is False),

        ("Invalid humidity",
         check_physical_reading(5, 120) is False),

        # 3. Shipment date tests
        ("Valid shipment dates",
         check_shipment_dates(
             datetime(2026, 11, 1, 10),
             datetime(2026, 11, 2, 10)
         ) is True),

        ("Arrival before departure",
         check_shipment_dates(
             datetime(2026, 11, 1, 10),
             datetime(2026, 11, 1, 9)
         ) is False),

        # 4. Product policy tests
        ("Matching product policy",
         check_product_policy("PRD-001", "PRD-001") is True),

        ("Wrong product policy",
         check_product_policy("PRD-001", "PRD-002") is False),

        # 5. Duration reconciliation tests
        ("Duration correctly reconciled",
         reconcile_duration(source_readings, 15) is True),

        ("Duration undercount detected",
         reconcile_duration(source_readings, 10) is False),

        # 6. Temperature tests
        ("High temperature",
         check_temperature(9, 2, 8) == "HIGH_TEMPERATURE"),

        ("Low temperature",
         check_temperature(1, 2, 8) == "LOW_TEMPERATURE"),

        ("Normal temperature",
         check_temperature(5, 2, 8) == "NORMAL"),

        # 7. Humidity tests
        ("High humidity",
         check_humidity(95, 30, 60) == "HIGH_HUMIDITY"),

        ("Low humidity",
         check_humidity(20, 30, 60) == "LOW_HUMIDITY"),

        ("Normal humidity",
         check_humidity(45, 30, 60) == "NORMAL"),

        # 8. Missing-value tests
        ("Missing temperature",
         check_temperature(None, 2, 8) == "INVALID_READING"),

        ("Missing humidity",
         check_humidity(None, 30, 60) == "INVALID_READING"),

        # 9. Temperature boundary tests
        ("Temperature exactly at maximum",
         check_temperature(8, 2, 8) == "NORMAL"),

        ("Temperature exactly at minimum",
         check_temperature(2, 2, 8) == "NORMAL"),

        # 10. Humidity boundary tests
        ("Humidity exactly at maximum",
         check_humidity(60, 30, 60) == "NORMAL"),

        ("Humidity exactly at minimum",
         check_humidity(30, 30, 60) == "NORMAL"),

        # 11. Missing policy test
        ("Missing product policy",
         check_product_policy("PRD-001", None) is False),

        # 12. Missing shipment date test
        ("Missing shipment date",
         check_shipment_dates(
             None,
             datetime(2026, 11, 2, 10)
         ) is False),

        # 13. Additional physical validation tests
        ("Non-numeric temperature",
         check_physical_reading("invalid", 45) is False),

        ("Non-numeric humidity",
         check_physical_reading(5, "invalid") is False),

        ("Temperature at lower physical limit",
         check_physical_reading(-100, 50) is True),

        ("Humidity at upper physical limit",
         check_physical_reading(5, 100) is True),

        # 14. Additional temperature and humidity tests
        ("Temperature outside physical range",
         check_temperature(101, 2, 8) == "INVALID_READING"),

        ("Humidity outside physical range",
         check_humidity(101, 30, 60) == "INVALID_READING"),

        ("Non-numeric temperature threshold",
         check_temperature(5, "invalid", 8) == "INVALID_READING"),

        ("Non-numeric humidity threshold",
         check_humidity(45, 30, "invalid") == "INVALID_READING"),

        # 15. Additional duration tests
        ("Negative calculated duration",
         reconcile_duration(source_readings, -5) is False),

        ("Invalid reading interval",
         reconcile_duration(
             source_readings, 15, reading_interval_minutes=0
         ) is False),

        ("Custom reading interval",
         reconcile_duration(
             source_readings, 20, reading_interval_minutes=10
         ) is True),

        # 16. Additional missing and invalid input tests
        ("Missing physical reading",
         check_physical_reading(None, 45) is False),

        ("Invalid shipment date types",
         check_shipment_dates("invalid", datetime(2026, 11, 2)) is False)
    ]

    passed = 0
    failed = 0

    print("\nDETECTION RULES VALIDATION")
    print("=" * 60)

    for name, result in tests:

        if result:
            print(f"PASS | {name}")
            passed += 1
        else:
            print(f"FAIL | {name}")
            failed += 1

    print("=" * 60)
    print("Passed:", passed)
    print("Failed:", failed)
    print("Total:", passed + failed)

    if failed == 0:
        print("\nALL DETECTION RULE TESTS PASSED.")
    else:
        print("\nVALIDATION NEEDS ATTENTION.")

    return failed == 0


if __name__ == "__main__":
    run_tests()
