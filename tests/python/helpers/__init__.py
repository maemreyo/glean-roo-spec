"""
Test Helper Functions Package

This package provides utility functions for test execution and assertions.
These helpers are designed to make tests more readable and maintainable.

Available Helpers:
- output_helpers: Functions for capturing and parsing subprocess output
- assertion_helpers: Custom assertion functions with clear error messages

Example:
    from tests.python.helpers import capture_output, assert_file_exists

    # Capture output from a Python script
    result = capture_output(['python', 'script.py'])

    # Assert file existence with optional content check
    assert_file_exists('/path/to/file.txt', expected_content='Hello World')
"""

from .output_helpers import (
    capture_output,
    run_python_script,
    parse_json_output,
    assert_exit_code
)

from .assertion_helpers import (
    assert_file_exists,
    assert_directory_exists,
    assert_json_output,
    assert_branch_name_pattern
)

__all__ = [
    # Output helpers
    'capture_output',
    'run_python_script',
    'parse_json_output',
    'assert_exit_code',
    # Assertion helpers
    'assert_file_exists',
    'assert_directory_exists',
    'assert_json_output',
    'assert_branch_name_pattern',
]
