
def validate_shipment_dates(departure_time, arrival_time):
    if departure_time is None or arrival_time is None:
        return "INVALID_DATE"

    if arrival_time < departure_time:
        return "DATE_ORDER_VIOLATION"

    return "VALID"


test_cases = [
    ("2026-10-01 08:00", "2026-10-03 12:00", "VALID"),
    ("2026-10-01 08:00", "2026-10-01 08:00", "VALID"),
    ("2026-10-03 12:00", "2026-10-01 08:00", "DATE_ORDER_VIOLATION"),
    (None, "2026-10-03 12:00", "INVALID_DATE"),
    ("2026-10-01 08:00", None, "INVALID_DATE"),
]

passed = 0
failed = 0

print("\nSHIPMENT DATE VALIDATION")

for departure, arrival, expected in test_cases:
    actual = validate_shipment_dates(departure, arrival)

    if actual == expected:
        print(f"PASS | Departure={departure} | Arrival={arrival}")
        passed += 1
    else:
        print(f"FAIL | Departure={departure} | Arrival={arrival}")
        failed += 1

print("\nPassed:", passed)
print("Failed:", failed)
print("Total:", len(test_cases))

if failed == 0:
    print("ALL SHIPMENT DATE TESTS PASSED.")
