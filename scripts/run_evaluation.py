import argparse
import subprocess
import sys


TEST_SUITES = {
    "unit": [
        "tests/unit",
    ],
    "deterministic": [
        "tests/evaluation/deterministic",
    ],
    "semantic": [
        "tests/evaluation/semantic",
    ],
    "all": [
        "tests/unit",
        "tests/evaluation/deterministic",
    ],
}


def parse_arguments() -> argparse.Namespace:
    """Parse the evaluation suite requested by the user."""

    parser = argparse.ArgumentParser(
        description="Run the project's evaluation and test suites."
    )

    parser.add_argument(
        "suite",
        choices=TEST_SUITES,
        help=(
            "Evaluation suite to run. "
            "'all' runs fast local checks only "
            "(unit + deterministic)."
        ),
    )

    return parser.parse_args()


def main() -> int:
    """Run the selected pytest suite."""

    args = parse_arguments()
    test_paths = TEST_SUITES[args.suite]

    command = [
        sys.executable,
        "-m",
        "pytest",
        *test_paths,
    ]

    print(f"Running {args.suite} evaluation...")
    print(f"Command: {' '.join(command)}")

    result = subprocess.run(command)

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())