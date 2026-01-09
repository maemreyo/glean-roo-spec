#!/usr/bin/env python3
"""
Test script to verify that Python implementation matches bash implementation exactly.

This script compares the output of:
1. The original bash script: .zo/scripts/bash/setup-brainstorm.sh
2. The new Python script: .zo/scripts/python/setup-brainstorm.py

Usage: python setup-brainstorm.test.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Constants
SCRIPT_DIR = Path(__file__).parent
BASH_SCRIPT = SCRIPT_DIR.parent / "bash" / "setup-brainstorm.sh"
PYTHON_SCRIPT = SCRIPT_DIR / "setup-brainstorm.py"
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent  # Go up 4 levels: python -> scripts -> .zo -> project

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text):
    """Print a test section header."""
    separator = "=" * 60
    print("\n" + BOLD + separator + RESET)
    print(BOLD + text + RESET)
    print(BOLD + separator + RESET + "\n")


def print_success(text):
    """Print a success message."""
    print(GREEN + "✓ " + text + RESET)


def print_fail(text):
    """Print a failure message."""
    print(RED + "✗ " + text + RESET)


def print_info(text):
    """Print an info message."""
    print(YELLOW + "→ " + text + RESET)


def run_bash_script(args, env=None):
    """Run the bash script and return (exit_code, stdout, stderr)."""
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    
    try:
        result = subprocess.run(
            ["bash", str(BASH_SCRIPT)] + args,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(REPO_ROOT),
            env=run_env
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except FileNotFoundError:
        return -1, "", "Bash script not found"


def run_python_script(args, env=None):
    """Run the Python script and return (exit_code, stdout, stderr)."""
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    
    try:
        result = subprocess.run(
            [sys.executable, str(PYTHON_SCRIPT)] + args,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(REPO_ROOT),
            env=run_env
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except FileNotFoundError:
        return -1, "", "Python script not found"


def extract_json(output):
    """Extract JSON from output, skipping non-JSON lines."""
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            try:
                return json.loads(line)
            except:
                pass
    return None


def compare_json_values(test_name, args, env=None):
    """
    Compare JSON values between bash and Python outputs.
    Only compares JSON fields, ignores log lines.
    
    Args:
        test_name: Name of the test
        args: Command line arguments
        env: Environment variables
        
    Returns:
        True if JSON values match, False otherwise
    """
    print_info("Test: " + test_name)
    print_info("Args: " + str(args))
    if env:
        print_info("Env: " + str(env))
    
    bash_code, bash_stdout, bash_stderr = run_bash_script(args, env)
    python_code, python_stdout, python_stderr = run_python_script(args, env)
    
    # Compare exit codes
    if bash_code != python_code:
        print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
        return False
    print_success("Exit codes match: " + str(bash_code))
    
    # Extract JSON from output (skip non-JSON lines)
    bash_json = extract_json(bash_stdout)
    python_json = extract_json(python_stdout)
    
    if bash_json is None or python_json is None:
        print_fail("Could not extract JSON from output")
        print("  Bash stdout:", bash_stdout[:200] if bash_stdout else "(empty)")
        print("  Python stdout:", python_stdout[:200] if python_stdout else "(empty)")
        return False
    
    # Compare JSON values
    if bash_json == python_json:
        print_success("JSON values match")
        return True
    else:
        print_fail("JSON values differ:")
        print("  Bash:", json.dumps(bash_json, indent=2))
        print("  Python:", json.dumps(python_json, indent=2))
        return False


def compare_outputs(test_name, args, env=None, check_json_equivalence=True):
    """
    Compare outputs of bash and Python scripts.
    
    Args:
        test_name: Name of the test
        args: Command line arguments
        env: Environment variables
        check_json_equivalence: Whether to check JSON equivalence
        
    Returns:
        True if outputs match, False otherwise
    """
    print_info("Test: " + test_name)
    print_info("Args: " + str(args))
    if env:
        print_info("Env: " + str(env))
    
    bash_code, bash_stdout, bash_stderr = run_bash_script(args, env)
    python_code, python_stdout, python_stderr = run_python_script(args, env)
    
    # Compare exit codes
    if bash_code != python_code:
        print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
        return False
    print_success("Exit codes match: " + str(bash_code))
    
    # Compare stdout (normalize whitespace for comparison)
    bash_normalized = bash_stdout.strip()
    python_normalized = python_stdout.strip()
    
    if bash_normalized != python_normalized:
        print_fail("Stdout differs:")
        print("  Bash stdout:")
        print(bash_stdout)
        print("  Python stdout:")
        print(python_stdout)
        return False
    print_success("Stdout matches")
    
    # If JSON mode, verify JSON equivalence
    if check_json_equivalence and "--json" in args:
        try:
            bash_json = json.loads(bash_stdout)
            python_json = json.loads(python_stdout)
            if bash_json != python_json:
                print_fail("JSON content differs:")
                print("  Bash JSON: " + json.dumps(bash_json, indent=2))
                print("  Python JSON: " + json.dumps(python_json, indent=2))
                return False
            print_success("JSON content matches")
        except json.JSONDecodeError as e:
            print_fail("JSON parse error: " + str(e))
            return False
    
    return True


def cleanup_brainstorm_files():
    """Clean up any created brainstorm files for testing."""
    brainstorms_dir = REPO_ROOT / ".zo" / "brainstorms"
    if brainstorms_dir.exists():
        # Clean up test brainstorm files
        for file in brainstorms_dir.glob("test-*.md"):
            file.unlink()
        for file in brainstorms_dir.glob("improve-login-*.md"):
            file.unlink()
        for file in brainstorms_dir.glob("add-dark-mode-*.md"):
            file.unlink()


def test_help():
    """Test --help output."""
    print_header("Test: Help Output")
    
    bash_code, bash_stdout, _ = run_bash_script(["--help"])
    python_code, python_stdout, _ = run_python_script(["--help"])
    
    if bash_code != python_code:
        print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
        return False
    
    if bash_stdout.strip() != python_stdout.strip():
        print_fail("Help output differs")
        return False
    
    print_success("Help output matches")
    return True


def test_topic_generation():
    """Test topic generation with text mode."""
    print_header("Test: Topic Generation (Text Mode)")
    
    try:
        cleanup_brainstorm_files()
        return compare_outputs(
            "Topic generation with text mode",
            ["improve login flow"],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_brainstorm_files()


def test_topic_generation_json():
    """Test topic generation with JSON mode."""
    print_header("Test: Topic Generation (JSON Mode)")
    
    try:
        cleanup_brainstorm_files()
        return compare_json_values(
            "Topic generation with JSON mode",
            ["--json", "add dark mode"],
            None
        )
    finally:
        cleanup_brainstorm_files()


def test_no_topic():
    """Test with no topic provided (should use default)."""
    print_header("Test: No Topic Provided")
    
    try:
        cleanup_brainstorm_files()
        return compare_outputs(
            "No topic provided",
            [],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_brainstorm_files()


def test_no_topic_json():
    """Test with no topic provided in JSON mode."""
    print_header("Test: No Topic Provided (JSON Mode)")
    
    try:
        cleanup_brainstorm_files()
        return compare_json_values(
            "No topic provided with JSON",
            ["--json"],
            None
        )
    finally:
        cleanup_brainstorm_files()


def test_slugification():
    """Test that topic is properly slugified."""
    print_header("Test: Topic Slugification")
    
    try:
        cleanup_brainstorm_files()
        return compare_outputs(
            "Complex topic with special characters",
            ["Test Feature! @#$%^&*()"],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_brainstorm_files()


def test_template_usage():
    """Test that template is used when available."""
    print_header("Test: Template Usage")
    
    # Create template directory and file
    template_dir = REPO_ROOT / ".zo" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / "brainstorm-template.md"
    
    # Create a simple template
    template_content = """# Brainstorm: {{FEATURE}}
Date: {{DATE}}

## Notes
"""
    
    template_file.write_text(template_content)
    
    try:
        cleanup_brainstorm_files()
        result = compare_outputs(
            "Template usage",
            ["test template usage"],
            None,
            check_json_equivalence=False
        )
        return result
    finally:
        cleanup_brainstorm_files()


def test_template_usage_json():
    """Test template usage with JSON output."""
    print_header("Test: Template Usage (JSON Mode)")
    
    # Ensure template exists
    template_dir = REPO_ROOT / ".zo" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / "brainstorm-template.md"
    
    if not template_file.exists():
        template_file.write_text("# Brainstorm: {{FEATURE}}\nDate: {{DATE}}\n")
    
    try:
        cleanup_brainstorm_files()
        return compare_json_values(
            "Template usage with JSON",
            ["--json", "test template"],
            None
        )
    finally:
        cleanup_brainstorm_files()


def test_invalid_option():
    """Test handling of invalid options."""
    print_header("Test: Invalid Option")
    
    bash_code, _, bash_stderr = run_bash_script(["--invalid-option"])
    python_code, _, python_stderr = run_python_script(["--invalid-option"])
    
    if bash_code != python_code:
        print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
        return False
    
    print_success("Invalid option handling matches")
    return True


def run_all_tests():
    """Run all tests and return summary."""
    print("\n" + BOLD + "=" * 60 + RESET)
    print(BOLD + "SETUP-BRAINSTORM TEST SUITE" + RESET)
    print(BOLD + "=" * 60 + RESET)
    print("\nRepo root: " + str(REPO_ROOT))
    print("Bash script: " + str(BASH_SCRIPT))
    print("Python script: " + str(PYTHON_SCRIPT))
    
    tests = [
        ("Help", test_help),
        ("Topic Generation (text)", test_topic_generation),
        ("Topic Generation (JSON)", test_topic_generation_json),
        ("No Topic Provided", test_no_topic),
        ("No Topic Provided (JSON)", test_no_topic_json),
        ("Topic Slugification", test_slugification),
        ("Template Usage", test_template_usage),
        ("Template Usage (JSON)", test_template_usage_json),
        ("Invalid Option", test_invalid_option),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_fail("Test crashed: " + str(e))
            results.append((test_name, False))
    
    # Print summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(test_name)
        else:
            print_fail(test_name)
    
    print("\n" + BOLD + "Results: " + str(passed) + "/" + str(total) + " tests passed" + RESET)
    
    if passed == total:
        print(GREEN + BOLD + "All tests passed!" + RESET + " ✓")
        return 0
    else:
        print(RED + BOLD + "Some tests failed!" + RESET + " ✗")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
