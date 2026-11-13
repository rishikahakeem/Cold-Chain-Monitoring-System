
import subprocess
import sys
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TEST_FILES = [
    "validate_ground_truth.py",
    "validate_database_rules.py",
    "test_calibration_rule.py",
    "test_physical_readings.py",
    "test_shipment_date_validation.py",
    "test_threshold_mismatch.py",
    "test_duration_reconciliation.py",
    "test_detection_rules.py",
    "test_rule_integration.py",
    "test_detector_dry_run.py",
]


def run_test(file_name):

    file_path = BASE_DIR / file_name

    print("\n" + "=" * 65)
    print("RUNNING:", file_name)
    print("=" * 65)

    if not file_path.exists():
        print("FAIL: File not found:", file_name)
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(file_path)],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )

        output = (result.stdout or "") + "\n" + (result.stderr or "")

        print(output)

        if result.returncode != 0:
            print("RESULT: FAIL - Non-zero exit code")
            return False

        if file_name == "validate_database_rules.py":

            success = (
                "Read-only validation completed." in output
                and "No database records were modified." in output
                and re.search(
                    r"^\s*FAIL\s*[|:]",
                    output,
                    re.MULTILINE
                ) is None
            )

        elif file_name == "validate_ground_truth.py":

            success = (
                re.search(r"^Passed:\s*10\s*$", output, re.MULTILINE)
                is not None
                and re.search(r"^Failed:\s*0\s*$", output, re.MULTILINE)
                is not None
                and "ALL 10 ISOLATED TESTS PASSED." in output
            )

        elif file_name == "test_rule_integration.py":

            success = (
                re.search(r"^Passed:\s*14\s*$", output, re.MULTILINE)
                is not None
                and re.search(r"^Failed:\s*0\s*$", output, re.MULTILINE)
                is not None
                and "ALL COMBINED RULE INTEGRATION TESTS PASSED." in output
            )

        elif file_name == "test_detector_dry_run.py":

            success = (
                re.search(r"^Passed:\s*8\s*$", output, re.MULTILINE)
                is not None
                and re.search(r"^Failed:\s*0\s*$", output, re.MULTILINE)
                is not None
                and "ALL DETECTOR DRY-RUN TESTS PASSED." in output
                and "No database connection was used." in output
                and "No database records were modified." in output
            )

        else:

            success = (
                re.search(
                    r"^\s*Failed:\s*0\s*$",
                    output,
                    re.MULTILINE
                ) is not None
                and re.search(
                    r"ALL .* TESTS PASSED\.",
                    output
                ) is not None
            )

        if success:
            print("RESULT: PASS")
            return True

        print("RESULT: FAIL - Expected success summary not found")
        return False

    except subprocess.TimeoutExpired:
        print("FAIL: Test timed out.")
        return False

    except Exception as error:
        print("FAIL:", error)
        return False


def main():

    print("\nCOLD CHAIN MONITORING SYSTEM")
    print("COMBINED VALIDATION RUNNER")
    print("=" * 65)

    print("Project folder:", BASE_DIR)

    print("\nSafety:")
    print("- Does not run detect_excursions.py")
    print("- Does not insert or delete database records")
    print("- Database validation remains read-only")
    print("- Runs isolated detection rule tests")
    print("- Runs combined in-memory rule integration tests")
    print("- Runs in-memory detector dry-run tests")

    results = {}

    for file_name in TEST_FILES:
        results[file_name] = run_test(file_name)

    print("\n" + "=" * 65)
    print("FINAL VALIDATION SUMMARY")
    print("=" * 65)

    passed = sum(results.values())
    failed = len(results) - passed

    for file_name, status in results.items():
        print(f"{'PASS' if status else 'FAIL'} | {file_name}")

    print("-" * 65)
    print("Total test files:", len(TEST_FILES))
    print("Passed:", passed)
    print("Failed:", failed)

    if failed == 0:
        print("\nALL COMBINED VALIDATION CHECKS PASSED.")
    else:
        print("\nVALIDATION HAS FAILURES. Review the output above.")

    print("\nNo database records were modified.")


if __name__ == "__main__":
    main()
