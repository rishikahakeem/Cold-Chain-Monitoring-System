
def validate_threshold_product(shipment_product_id, policy_product_id):
    if shipment_product_id != policy_product_id:
        return "THRESHOLD_MISMATCH"

    return "VALID"


test_cases = [
    ("PRD-001", "PRD-001", "VALID"),
    ("PRD-002", "PRD-002", "VALID"),
    ("PRD-003", "PRD-003", "VALID"),
    ("PRD-001", "PRD-002", "THRESHOLD_MISMATCH"),
    ("PRD-002", "PRD-003", "THRESHOLD_MISMATCH"),
    ("PRD-003", "PRD-001", "THRESHOLD_MISMATCH"),
]

passed = 0
failed = 0

print("\nTHRESHOLD PRODUCT VALIDATION")

for shipment_product, policy_product, expected in test_cases:
    actual = validate_threshold_product(
        shipment_product,
        policy_product
    )

    if actual == expected:
        print(
            f"PASS | Shipment: {shipment_product} "
            f"| Policy: {policy_product} | Result: {actual}"
        )
        passed += 1
    else:
        print(
            f"FAIL | Shipment: {shipment_product} "
            f"| Policy: {policy_product}"
        )
        failed += 1

print("\nPassed:", passed)
print("Failed:", failed)
print("Total:", len(test_cases))

if failed == 0:
    print("ALL THRESHOLD TESTS PASSED.")
