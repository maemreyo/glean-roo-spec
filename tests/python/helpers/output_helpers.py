"""
Output Helper Functions

This module provides utility functions for capturing and parsing output
from subprocess execution. These helpers make it easier to test Python
scripts that output to stdout/stderr.

Functions:
    capture_output: Capture stdout/stderr from subprocess execution
    run_python_script: Execute Python scripts and return results
    parse_json_output: Parse JSON output with error handling
    assert_exit_code: Assert exit codes with clear error messages
"""

import json
import subprocess
import sys
from typing import Optional, Dict, Any, List


class ProcessResult:
    """
    Result object for subprocess execution.

    Attributes:
        stdout: Standard output content
        stderr: Standard error content
        exit_code: Process exit code
        success: True if exit code is 0
    """

    def __init__(self, stdout: str, stderr: str, exit_code: int):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.success = exit_code == 0

    def __repr__(self) -> str:
        return (f"ProcessResult(success={self.success}, "
                f"exit_code={self.exit_code}, "
                f"stdout_len={len(self.stdout)}, "
                f"stderr_len={len(self.stderr)})")


def capture_output(
    command: List[str],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    input_text: Optional[str] = None,
    timeout: Optional[int] = None
) -> ProcessResult:
    """
    Capture stdout/stderr from subprocess execution.

    Args:
        command: Command to execute as a list of strings
        cwd: Working directory for the command
        env: Environment variables (default: current environment)
        input_text: Text to provide as stdin
        timeout: Timeout in seconds (default: no timeout)

    Returns:
        ProcessResult object with stdout, stderr, and exit code

    Raises:
        subprocess.TimeoutExpired: If command times out
        FileNotFoundError: If command executable not found

    Example:
        result = capture_output(['ls', '-la'])
        print(result.stdout)
        assert result.success
    """
    try:
        process_result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return ProcessResult(
            stdout=process_result.stdout,
            stderr=process_result.stderr,
            exit_code=process_result.returncode
        )

    except subprocess.TimeoutExpired as e:
        # Return timeout information in result
        return ProcessResult(
            stdout=e.stdout.decode() if e.stdout else '',
            stderr=e.stderr.decode() if e.stderr else '',
            exit_code=-1  # Special code for timeout
        )


def run_python_script(
    script_path: str,
    args: Optional[List[str]] = None,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> ProcessResult:
    """
    Execute a Python script and return the result.

    Args:
        script_path: Path to the Python script
        args: Additional arguments to pass to the script
        cwd: Working directory for execution
        env: Environment variables (default: current environment)

    Returns:
        ProcessResult object with stdout, stderr, and exit code

    Example:
        result = run_python_script('myscript.py', ['--verbose'])
        assert result.success
    """
    command = [sys.executable, script_path]

    if args:
        command.extend(args)

    return capture_output(command, cwd=cwd, env=env)


def parse_json_output(output: str) -> Dict[str, Any]:
    """
    Parse JSON output with error handling.

    Args:
        output: JSON string to parse

    Returns:
        Parsed JSON as a dictionary

    Raises:
        ValueError: If output is not valid JSON

    Example:
        result = run_python_script('script.py')
        data = parse_json_output(result.stdout)
        assert data['status'] == 'success'
    """
    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse JSON output: {e}\n"
            f"Output was:\n{output}"
        )


def assert_exit_code(
    result: ProcessResult,
    expected_code: int = 0,
    error_message: Optional[str] = None
) -> None:
    """
    Assert exit code with clear error messages.

    Args:
        result: ProcessResult object
        expected_code: Expected exit code (default: 0)
        error_message: Custom error message (optional)

    Raises:
        AssertionError: If exit code doesn't match

    Example:
        result = run_python_script('script.py')
        assert_exit_code(result, expected_code=0)
    """
    if result.exit_code != expected_code:
        message = error_message or (
            f"Expected exit code {expected_code}, but got {result.exit_code}\n"
            f"Command output:\n{result.stdout}\n"
            f"Command errors:\n{result.stderr}"
        )
        raise AssertionError(message)


def assert_output_contains(
    result: ProcessResult,
    expected_text: str,
    in_stderr: bool = False
) -> None:
    """
    Assert that output contains expected text.

    Args:
        result: ProcessResult object
        expected_text: Text expected to be in output
        in_stderr: Check stderr instead of stdout (default: False)

    Raises:
        AssertionError: If expected text not found

    Example:
        result = run_python_script('script.py')
        assert_output_contains(result, 'Operation completed')
    """
    output = result.stderr if in_stderr else result.stdout

    if expected_text not in output:
        raise AssertionError(
            f"Expected text not found in output:\n"
            f"Expected: '{expected_text}'\n"
            f"Actual output:\n{output}"
        )


def assert_output_matches(
    result: ProcessResult,
    pattern: str,
    in_stderr: bool = False
) -> None:
    """
    Assert that output matches a regex pattern.

    Args:
        result: ProcessResult object
        pattern: Regex pattern to match
        in_stderr: Check stderr instead of stdout (default: False)

    Raises:
        AssertionError: If pattern doesn't match
        re.error: If pattern is invalid regex

    Example:
        result = run_python_script('script.py')
        assert_output_matches(result, r'Created file: \w+\.txt')
    """
    import re

    output = result.stderr if in_stderr else result.stdout

    if not re.search(pattern, output):
        raise AssertionError(
            f"Output does not match pattern '{pattern}'\n"
            f"Actual output:\n{output}"
        )
