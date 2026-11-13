
def validate_reading(temperature, humidity):
    if temperature < -100 or temperature > 100:
        return "PHYSICALLY_INVALID_READING"

    if humidity < 0 or humidity > 100:
        return "PHYSICALLY_INVALID_READING"

    return "VALID"


test_cases = [
    (5, 50, "VALID"),
    (-101, 50, "PHYSICALLY_INVALID_READING"),
    (101, 50, "PHYSICALLY_INVALID_READING"),
    (5, -1, "PHYSICALLY_INVALID_READING"),
    (5, 101, "PHYSICALLY_INVALID_READING"),
    (-100, 0, "VALID"),
    (100, 100, "VALID"),
]

passed = 0
failed = 0

print("\nPHYSICAL READING VALIDATION")

for temperature, humidity, expected in test_cases:
    actual = validate_reading(temperature, humidity)

    if actual == expected:
        print(f"PASS | Temp={temperature} | Humidity={humidity}")
        passed += 1
    else:
        print(f"FAIL | Temp={temperature} | Humidity={humidity}")
        failed += 1

print("\nPassed:", passed)
print("Failed:", failed)
print("Total:", len(test_cases))

if failed == 0:
    print("ALL PHYSICAL READING TESTS PASSED.")
