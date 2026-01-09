#!/usr/bin/env python3
"""
Test Runner Script

This script discovers and runs all tests in the Python test suite.
It provides clear output formatting and supports verbose mode.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py -v           # Run with verbose output
    python run_tests.py test_core    # Run specific test package
"""

import argparse
import sys
import unittest
from io import StringIO
from typing import Optional


class TestResultWithOutput(unittest.TextTestResult):
    """
    Custom test result class that captures test output.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_outputs: dict = {}
        self.current_output: Optional[StringIO] = None

    def startTest(self, test):
        super().startTest(test)
        self.current_output = StringIO()

    def stopTest(self, test):
        super().stopTest(test)
        if self.current_output:
            self.test_outputs[test.id()] = self.current_output.getvalue()
            self.current_output = None


class TestRunnerWithOutput(unittest.TextTestRunner):
    """
    Custom test runner that uses our custom result class.
    """

    def __init__(self, verbosity=1, stream=None):
        if stream is None:
            stream = sys.stdout
        super().__init__(verbosity=verbosity, stream=stream)

    def _makeResult(self):
        return TestResultWithOutput(
            stream=self.stream,
            descriptions=self.descriptions,
            verbosity=self.verbosity
        )


def run_tests(test_target: Optional[str] = None, verbose: bool = False) -> int:
    """
    Run tests and return exit code.

    Args:
        test_target: Specific test package to run (default: all tests)
        verbose: Whether to use verbose output

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Determine which tests to run
    if test_target:
        # Import the specific test package
        test_module = __import__(f'tests.python.{test_target}', fromlist=[''])
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        test_name = f'tests.python.{test_target}'
    else:
        # Discover all tests
        loader = unittest.TestLoader()
        start_dir = 'tests/python'
        suite = loader.discover(start_dir, pattern='test_*.py')
        test_name = 'tests.python'

    # Set verbosity
    verbosity = 2 if verbose else 1

    # Create and run the test runner
    print(f"\n{'=' * 70}")
    print(f"Running tests: {test_name}")
    print(f"{'=' * 70}\n")

    runner = TestRunnerWithOutput(verbosity=verbosity)
    result = runner.run(suite)

    # Print summary
    print(f"\n{'=' * 70}")
    print(f"Test Summary")
    print(f"{'=' * 70}")
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    # Return exit code
    return 0 if result.wasSuccessful() else 1


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description='Run Python tests for .zo scripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                 Run all tests
  %(prog)s -v              Run all tests with verbose output
  %(prog)s test_core       Run only core utility tests
  %(prog)s test_features   Run only feature creation tests
        """
    )

    parser.add_argument(
        'test_target',
        nargs='?',
        help='Specific test package to run (e.g., test_core, test_features)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Run the tests
    exit_code = run_tests(args.test_target, args.verbose)

    # Exit with appropriate code
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
