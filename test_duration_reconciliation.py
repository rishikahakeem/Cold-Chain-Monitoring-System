
def validate_duration(start_minutes, end_minutes, recorded_duration):
    actual_duration = end_minutes - start_minutes

    if recorded_duration < actual_duration:
        return "DURATION_UNDERCOUNT"

    if recorded_duration > actual_duration:
        return "DURATION_OVERCOUNT"

    return "VALID"


test_cases = [
    (0, 30, 30, "VALID"),
    (0, 30, 20, "DURATION_UNDERCOUNT"),
    (0, 30, 40, "DURATION_OVERCOUNT"),
    (10, 50, 40, "VALID"),
    (10, 50, 35, "DURATION_UNDERCOUNT"),
]

passed = 0
failed = 0

print("\nEXCURSION DURATION VALIDATION")

for start, end, recorded, expected in test_cases:
    actual = validate_duration(start, end, recorded)

    if actual == expected:
        print(
            f"PASS | Actual: {end - start} min "
            f"| Recorded: {recorded} min "
            f"| Result: {actual}"
        )
        passed += 1
    else:
        print(
            f"FAIL | Actual: {end - start} min "
            f"| Recorded: {recorded} min"
        )
        failed += 1

print("\nPassed:", passed)
print("Failed:", failed)
print("Total:", len(test_cases))

if failed == 0:
    print("ALL DURATION TESTS PASSED.")
