
def is_calibration_failure(status):
    calibration_status = (status or "").strip().upper()
    return calibration_status != "CALIBRATED"


test_cases = [
    ("CALIBRATED", False),
    ("FAILED", True),
    ("EXPIRED", True),
    (None, True),
    ("", True),
    ("UNKNOWN", True),
]

print("\nCALIBRATION FAILURE VALIDATION")

passed = 0
failed = 0

for status, expected in test_cases:
    actual = is_calibration_failure(status)

    if actual == expected:
        print(f"PASS | Status: {status} | Failure: {actual}")
        passed += 1
    else:
        print(f"FAIL | Status: {status} | Expected: {expected}")
        failed += 1

print("\nPassed:", passed)
print("Failed:", failed)
print("Total:", len(test_cases))

if failed == 0:
    print("ALL CALIBRATION RULE TESTS PASSED.")
