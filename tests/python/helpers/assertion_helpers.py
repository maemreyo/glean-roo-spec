"""
Assertion Helper Functions

This module provides custom assertion functions with clear error messages.
These helpers make tests more readable and provide better error diagnostics.

Functions:
    assert_file_exists: Assert file exists with optional content check
    assert_directory_exists: Assert directory exists
    assert_json_output: Assert valid JSON output with expected keys
    assert_branch_name_pattern: Assert branch name follows pattern
"""

import os
import re
import json
from typing import Optional, List, Dict, Any


def assert_file_exists(
    file_path: str,
    expected_content: Optional[str] = None,
    description: Optional[str] = None
) -> None:
    """
    Assert that a file exists with optional content check.

    Args:
        file_path: Path to the file to check
        expected_content: Optional content to check for in the file
        description: Optional description for error messages

    Raises:
        AssertionError: If file doesn't exist or content doesn't match

    Example:
        assert_file_exists('/tmp/test.txt', expected_content='Hello World')
    """
    if not os.path.isfile(file_path):
        desc = description or "File"
        raise AssertionError(
            f"{desc} does not exist: {file_path}\n"
            f"Expected path: {os.path.abspath(file_path)}"
        )

    if expected_content is not None:
        with open(file_path, 'r') as f:
            actual_content = f.read()

        if expected_content not in actual_content:
            raise AssertionError(
                f"File content does not match expected content.\n"
                f"File: {file_path}\n"
                f"Expected to contain: {expected_content}\n"
                f"Actual content:\n{actual_content}"
            )


def assert_directory_exists(
    dir_path: str,
    description: Optional[str] = None
) -> None:
    """
    Assert that a directory exists.

    Args:
        dir_path: Path to the directory to check
        description: Optional description for error messages

    Raises:
        AssertionError: If directory doesn't exist

    Example:
        assert_directory_exists('/tmp/test_dir')
    """
    if not os.path.isdir(dir_path):
        desc = description or "Directory"
        raise AssertionError(
            f"{desc} does not exist: {dir_path}\n"
            f"Expected path: {os.path.abspath(dir_path)}"
        )


def assert_json_output(
    output: str,
    expected_keys: Optional[List[str]] = None,
    expected_values: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Assert valid JSON output with expected keys/values.

    Args:
        output: JSON string to validate
        expected_keys: List of keys that must be present
        expected_values: Dictionary of key-value pairs to validate

    Returns:
        Parsed JSON as a dictionary

    Raises:
        AssertionError: If JSON is invalid or keys/values don't match

    Example:
        data = assert_json_output(
            '{"status": "success", "id": 123}',
            expected_keys=['status', 'id'],
            expected_values={'status': 'success'}
        )
    """
    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        raise AssertionError(
            f"Output is not valid JSON: {e}\n"
            f"Output was:\n{output}"
        )

    if not isinstance(data, dict):
        raise AssertionError(
            f"JSON output is not an object/dictionary.\n"
            f"Type: {type(data).__name__}\n"
            f"Output was:\n{output}"
        )

    if expected_keys:
        missing_keys = set(expected_keys) - set(data.keys())
        if missing_keys:
            raise AssertionError(
                f"JSON output missing expected keys: {missing_keys}\n"
                f"Expected keys: {expected_keys}\n"
                f"Actual keys: {list(data.keys())}\n"
                f"Output was:\n{output}"
            )

    if expected_values:
        for key, expected_value in expected_values.items():
            if key not in data:
                raise AssertionError(
                    f"JSON output missing key: {key}\n"
                    f"Output was:\n{output}"
                )

            actual_value = data[key]
            if actual_value != expected_value:
                raise AssertionError(
                    f"JSON output value mismatch for key '{key}'.\n"
                    f"Expected: {expected_value}\n"
                    f"Actual: {actual_value}\n"
                    f"Output was:\n{output}"
                )

    return data


def assert_branch_name_pattern(
    branch_name: str,
    pattern: str = r'^(feature|bugfix|hotfix)/\d{3}-[a-z0-9-]+$'
) -> None:
    """
    Assert that branch name follows the expected pattern.

    Args:
        branch_name: Branch name to validate
        pattern: Regex pattern to match (default: standard .zo pattern)

    Raises:
        AssertionError: If branch name doesn't match pattern

    Example:
        assert_branch_name_pattern('feature/001-test-feature')
    """
    if not re.match(pattern, branch_name):
        raise AssertionError(
            f"Branch name '{branch_name}' does not match pattern '{pattern}'.\n"
            f"Expected format: feature/###-name-with-dashes or bugfix/###-name"
        )


def assert_file_contains(
    file_path: str,
    expected_content: str,
    description: Optional[str] = None
) -> None:
    """
    Assert that a file contains specific content.

    Args:
        file_path: Path to the file to check
        expected_content: Content that must be in the file
        description: Optional description for error messages

    Raises:
        AssertionError: If file doesn't exist or doesn't contain content

    Example:
        assert_file_contains('/tmp/test.txt', 'Hello World')
    """
    if not os.path.isfile(file_path):
        raise AssertionError(
            f"File does not exist: {file_path}"
        )

    with open(file_path, 'r') as f:
        actual_content = f.read()

    if expected_content not in actual_content:
        desc = description or "File"
        raise AssertionError(
            f"{desc} does not contain expected content.\n"
            f"File: {file_path}\n"
            f"Expected to contain: {expected_content}\n"
            f"Actual content:\n{actual_content}"
        )


def assert_directory_structure(
    base_path: str,
    expected_structure: Dict[str, Any]
) -> None:
    """
    Assert that a directory structure matches expected structure.

    Args:
        base_path: Base directory path
        expected_structure: Dictionary describing expected structure
            (keys are paths, values are either True for directories
            or content strings for files)

    Raises:
        AssertionError: If structure doesn't match

    Example:
        assert_directory_structure('/tmp/test', {
            'subdir': True,  # directory exists
            'file.txt': 'content',  # file with content
            'subdir/nested.txt': 'nested'  # nested file
        })
    """
    for path, expectation in expected_structure.items():
        full_path = os.path.join(base_path, path)

        if expectation is True:
            # Should be a directory
            if not os.path.isdir(full_path):
                raise AssertionError(
                    f"Expected directory does not exist: {full_path}"
                )
        elif isinstance(expectation, str):
            # Should be a file with content
            assert_file_contains(full_path, expectation)
        else:
            # Just check existence
            if not os.path.exists(full_path):
                raise AssertionError(
                    f"Expected path does not exist: {full_path}"
                )


def assert_list_contains(
    actual_list: List[Any],
    expected_items: List[Any],
    description: Optional[str] = None
) -> None:
    """
    Assert that a list contains all expected items.

    Args:
        actual_list: The list to check
        expected_items: Items that must be in the list
        description: Optional description for error messages

    Raises:
        AssertionError: If any expected item is missing

    Example:
        assert_list_contains(['a', 'b', 'c'], ['a', 'c'])
    """
    missing_items = set(expected_items) - set(actual_list)

    if missing_items:
        desc = description or "List"
        raise AssertionError(
            f"{desc} is missing expected items: {missing_items}\n"
            f"Expected items: {expected_items}\n"
            f"Actual list: {actual_list}"
        )


def assert_no_duplicate_items(
    items: List[Any],
    description: Optional[str] = None
) -> None:
    """
    Assert that a list contains no duplicate items.

    Args:
        items: List to check for duplicates
        description: Optional description for error messages

    Raises:
        AssertionError: If duplicates are found

    Example:
        assert_no_duplicate_items(['a', 'b', 'c'])
    """
    seen = set()
    duplicates = []

    for item in items:
        if item in seen:
            duplicates.append(item)
        seen.add(item)

    if duplicates:
        desc = description or "List"
        unique_duplicates = list(set(duplicates))
        raise AssertionError(
            f"{desc} contains duplicate items: {unique_duplicates}\n"
            f"Full list: {items}"
        )
