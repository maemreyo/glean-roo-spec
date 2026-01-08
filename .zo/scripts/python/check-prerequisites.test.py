#!/usr/bin/env python3
"""
Test script to verify that Python implementation matches bash implementation exactly.

This script compares the output of:
1. The original bash script: .zo/scripts/bash/check-prerequisites.sh
2. The new Python script: .zo/scripts/python/check-prerequisites.py

Usage: python test_check_prerequisites.py
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
BASH_SCRIPT = SCRIPT_DIR.parent / "bash" / "check-prerequisites.sh"
PYTHON_SCRIPT = SCRIPT_DIR / "check-prerequisites.py"
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


def create_test_feature_dir():
    """Create a test feature directory with all possible files."""
    temp_dir = tempfile.mkdtemp()
    feature_dir = Path(temp_dir) / "specs" / "999-test-feature"
    feature_dir.mkdir(parents=True, exist_ok=True)
    
    # Create all possible files
    files = {
        "spec.md": "# Spec",
        "plan.md": "# Plan",
        "tasks.md": "# Tasks",
        "research.md": "# Research",
        "data-model.md": "# Data Model",
        "design.md": "# Design",
        "quickstart.md": "# Quickstart",
    }
    
    created_files = {}
    for filename, content in files.items():
        filepath = feature_dir / filename
        filepath.write_text(content)
        created_files[filename] = str(filepath)
    
    # Create contracts directory with a file
    contracts_dir = feature_dir / "contracts"
    contracts_dir.mkdir()
    (contracts_dir / "example.json").write_text('{"test": "contract"}')
    
    env = {
        "SPECIFY_FEATURE": "999-test-feature",
        "SPECS_DIR": str(feature_dir.parent),
    }
    
    return feature_dir, env


def cleanup_test_feature(dir_path):
    """Clean up test feature directory."""
    if dir_path.exists():
        shutil.rmtree(dir_path.parent)


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


def test_paths_only():
    """Test --paths-only output."""
    print_header("Test: --paths-only Output")
    
    feature_dir, env = create_test_feature_dir()
    try:
        return compare_outputs(
            "Paths only (text mode)",
            ["--paths-only"],
            env
        )
    finally:
        cleanup_test_feature(feature_dir)


def test_paths_only_json():
    """Test --paths-only --json output."""
    print_header("Test: --paths-only --json Output")
    
    feature_dir, env = create_test_feature_dir()
    try:
        return compare_outputs(
            "Paths only (JSON mode)",
            ["--paths-only", "--json"],
            env
        )
    finally:
        cleanup_test_feature(feature_dir)


def test_json_mode():
    """Test --json output."""
    print_header("Test: --json Output")
    
    feature_dir, env = create_test_feature_dir()
    try:
        return compare_outputs(
            "JSON mode",
            ["--json"],
            env
        )
    finally:
        cleanup_test_feature(feature_dir)


def test_json_mode_with_include_tasks():
    """Test --json --include-tasks output."""
    print_header("Test: --json --include-tasks Output")
    
    feature_dir, env = create_test_feature_dir()
    try:
        return compare_outputs(
            "JSON mode with include-tasks",
            ["--json", "--include-tasks"],
            env
        )
    finally:
        cleanup_test_feature(feature_dir)


def test_require_tasks_failure():
    """Test --require-tasks when tasks.md is missing."""
    print_header("Test: --require-tasks Failure (missing tasks.md)")
    
    # Create feature dir WITHOUT tasks.md
    temp_dir = tempfile.mkdtemp()
    feature_dir = Path(temp_dir) / "specs" / "998-test-no-tasks"
    feature_dir.mkdir(parents=True, exist_ok=True)
    
    # Only create plan.md, not tasks.md
    (feature_dir / "spec.md").write_text("# Spec")
    (feature_dir / "plan.md").write_text("# Plan")
    
    env = {
        "SPECIFY_FEATURE": "998-test-no-tasks",
        "SPECS_DIR": str(feature_dir.parent),
    }
    
    try:
        return compare_outputs(
            "Require tasks (should fail)",
            ["--require-tasks"],
            env
        )
    finally:
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)


def test_text_mode():
    """Test text mode output."""
    print_header("Test: Text Mode Output")
    
    feature_dir, env = create_test_feature_dir()
    try:
        return compare_outputs(
            "Text mode",
            [],
            env,
            check_json_equivalence=False  # Text mode doesn't output JSON
        )
    finally:
        cleanup_test_feature(feature_dir)


def test_text_mode_include_tasks():
    """Test text mode with --include-tasks."""
    print_header("Test: Text Mode with --include-tasks")
    
    feature_dir, env = create_test_feature_dir()
    try:
        return compare_outputs(
            "Text mode with include-tasks",
            ["--include-tasks"],
            env,
            check_json_equivalence=False
        )
    finally:
        cleanup_test_feature(feature_dir)


def test_feature_dir_not_found():
    """Test error when feature directory doesn't exist."""
    print_header("Test: Feature Directory Not Found")
    
    env = {
        "SPECIFY_FEATURE": "nonexistent-feature-xyz",
    }
    
    return compare_outputs(
        "Feature dir not found (should fail)",
        [],
        env
    )


def test_invalid_option():
    """Test handling of invalid options."""
    print_header("Test: Invalid Option")
    
    bash_code, _, bash_stderr = run_bash_script(["--invalid-option"])
    python_code, _, python_stderr = run_python_script(["--invalid-option"])
    
    if bash_code != python_code:
        print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
        return False
    
    if bash_stderr.strip() != python_stderr.strip():
        print_fail("Stderr differs:")
        print("  Bash stderr: " + bash_stderr)
        print("  Python stderr: " + python_stderr)
        return False
    
    print_success("Invalid option handling matches")
    return True


def run_all_tests():
    """Run all tests and return summary."""
    print("\n" + BOLD + "=" * 60 + RESET)
    print(BOLD + "CHECK-PREREQUISITES TEST SUITE" + RESET)
    print(BOLD + "=" * 60 + RESET)
    print("\nRepo root: " + str(REPO_ROOT))
    print("Bash script: " + str(BASH_SCRIPT))
    print("Python script: " + str(PYTHON_SCRIPT))
    
    tests = [
        ("Help", test_help),
        ("Paths Only (text)", test_paths_only),
        ("Paths Only (JSON)", test_paths_only_json),
        ("JSON Mode", test_json_mode),
        ("JSON Mode with --include-tasks", test_json_mode_with_include_tasks),
        ("Require Tasks Failure", test_require_tasks_failure),
        ("Text Mode", test_text_mode),
        ("Text Mode with --include-tasks", test_text_mode_include_tasks),
        ("Feature Directory Not Found", test_feature_dir_not_found),
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
