#!/usr/bin/env python3
"""
Test script to verify that Python implementation matches bash implementation exactly.

This script compares the output of:
1. The original bash script: .zo/scripts/bash/setup-roast-verify.sh
2. The new Python script: .zo/scripts/python/setup-roast-verify.py

Usage: python setup-roast-verify.test.py
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
BASH_SCRIPT = SCRIPT_DIR.parent / "bash" / "setup-roast-verify.sh"
PYTHON_SCRIPT = SCRIPT_DIR / "setup-roast-verify.py"
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


def cleanup_test_features():
    """Clean up test feature directories."""
    specs_dir = REPO_ROOT / "specs"
    
    if specs_dir.exists():
        for feature_dir in specs_dir.glob("999-test-*"):
            if feature_dir.is_dir():
                shutil.rmtree(feature_dir)


def setup_test_feature_with_roast():
    """Create a test feature directory with a roast report."""
    specs_dir = REPO_ROOT / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    
    feature_dir = specs_dir / "999-test-feature"
    feature_dir.mkdir(exist_ok=True)
    
    # Create required files
    (feature_dir / "spec.md").write_text("# Test Feature Spec\n")
    (feature_dir / "tasks.md").write_text("# Test Feature Tasks\n")
    
    # Create roasts directory with a roast report
    roasts_dir = feature_dir / "roasts"
    roasts_dir.mkdir(exist_ok=True)
    
    # Create a roast report with the expected naming pattern
    roast_file = roasts_dir / "roast-report-999-test-feature-2026-01-01-1200.md"
    roast_file.write_text("# Roast Report\n\n## Review\nTest review\n")
    
    return feature_dir, roast_file


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


def test_find_latest_roast():
    """Test finding the latest roast report."""
    print_header("Test: Find Latest Roast Report")
    
    try:
        cleanup_test_features()
        feature_dir, roast_file = setup_test_feature_with_roast()
        
        return compare_outputs(
            "Find latest roast report",
            [str(feature_dir)],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_test_features()


def test_find_latest_roast_json():
    """Test finding the latest roast report with JSON output."""
    print_header("Test: Find Latest Roast Report (JSON)")
    
    try:
        cleanup_test_features()
        feature_dir, roast_file = setup_test_feature_with_roast()
        
        return compare_outputs(
            "Find latest roast report with JSON",
            ["--json", str(feature_dir)],
            None
        )
    finally:
        cleanup_test_features()


def test_custom_report_path():
    """Test with custom report path."""
    print_header("Test: Custom Report Path")
    
    try:
        cleanup_test_features()
        feature_dir, roast_file = setup_test_feature_with_roast()
        
        return compare_outputs(
            "Custom report path",
            ["--report", str(roast_file), str(feature_dir)],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_test_features()


def test_custom_report_path_json():
    """Test with custom report path and JSON output."""
    print_header("Test: Custom Report Path (JSON)")
    
    try:
        cleanup_test_features()
        feature_dir, roast_file = setup_test_feature_with_roast()
        
        return compare_outputs(
            "Custom report path with JSON",
            ["--json", "--report", str(roast_file), str(feature_dir)],
            None
        )
    finally:
        cleanup_test_features()


def test_relative_report_path():
    """Test with relative path to report file."""
    print_header("Test: Relative Report Path")
    
    try:
        cleanup_test_features()
        feature_dir, roast_file = setup_test_feature_with_roast()
        
        # Change to feature directory and use relative path
        relative_report = "roasts/roast-report-999-test-feature-2026-01-01-1200.md"
        
        # Change to feature directory for test
        original_cwd = os.getcwd()
        os.chdir(str(feature_dir))
        
        try:
            return compare_outputs(
                "Relative report path",
                ["--report", relative_report],
                None,
                check_json_equivalence=False
            )
        finally:
            os.chdir(original_cwd)
    finally:
        cleanup_test_features()


def test_json_fields():
    """Test that JSON output contains all required fields."""
    print_header("Test: JSON Fields")
    
    try:
        cleanup_test_features()
        feature_dir, roast_file = setup_test_feature_with_roast()
        
        bash_code, bash_stdout, _ = run_bash_script(["--json", str(feature_dir)])
        python_code, python_stdout, _ = run_python_script(["--json", str(feature_dir)])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        try:
            bash_json = json.loads(bash_stdout)
            python_json = json.loads(python_stdout)
            
            # Check required fields
            required_fields = ["REPORT_FILE", "TASKS", "BRANCH"]
            
            for field in required_fields:
                if field not in bash_json or field not in python_json:
                    print_fail(f"Missing field: {field}")
                    return False
                
                if bash_json[field] != python_json[field]:
                    print_fail(f"{field} differs")
                    return False
            
            print_success("JSON fields match")
            return True
        except json.JSONDecodeError as e:
            print_fail("JSON parse error: " + str(e))
            return False
    finally:
        cleanup_test_features()


def test_no_roast_reports():
    """Test when no roast reports exist (should error)."""
    print_header("Test: No Roast Reports (Should Fail)")
    
    try:
        cleanup_test_features()
        
        # Create feature directory without roasts
        specs_dir = REPO_ROOT / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        
        feature_dir = specs_dir / "999-test-feature"
        feature_dir.mkdir(exist_ok=True)
        (feature_dir / "tasks.md").write_text("# Tasks\n")
        
        # Create empty roasts directory
        roasts_dir = feature_dir / "roasts"
        roasts_dir.mkdir(exist_ok=True)
        
        bash_code, bash_stdout, bash_stderr = run_bash_script([str(feature_dir)])
        python_code, python_stdout, python_stderr = run_python_script([str(feature_dir)])
        
        if bash_code != python_code:
            print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
            return False
        
        if bash_code == 0:
            print_fail("Expected non-zero exit code when no roast reports found")
            return False
        
        print_success("No roast reports handling matches")
        return True
    finally:
        cleanup_test_features()


def test_custom_report_not_found():
    """Test with custom report path that doesn't exist (should error)."""
    print_header("Test: Custom Report Not Found (Should Fail)")
    
    try:
        cleanup_test_features()
        
        # Create feature directory
        specs_dir = REPO_ROOT / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        
        feature_dir = specs_dir / "999-test-feature"
        feature_dir.mkdir(exist_ok=True)
        (feature_dir / "tasks.md").write_text("# Tasks\n")
        
        bash_code, bash_stdout, bash_stderr = run_bash_script([
            "--report", "nonexistent-report.md",
            str(feature_dir)
        ])
        python_code, python_stdout, python_stderr = run_python_script([
            "--report", "nonexistent-report.md",
            str(feature_dir)
        ])
        
        if bash_code != python_code:
            print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
            return False
        
        if bash_code == 0:
            print_fail("Expected non-zero exit code for non-existent report")
            return False
        
        print_success("Non-existent report handling matches")
        return True
    finally:
        cleanup_test_features()


def test_multiple_roast_reports():
    """Test finding the latest roast report when multiple exist."""
    print_header("Test: Multiple Roast Reports")
    
    try:
        cleanup_test_features()
        
        specs_dir = REPO_ROOT / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        
        feature_dir = specs_dir / "999-test-feature"
        feature_dir.mkdir(exist_ok=True)
        
        (feature_dir / "spec.md").write_text("# Spec\n")
        (feature_dir / "tasks.md").write_text("# Tasks\n")
        
        # Create multiple roast reports
        roasts_dir = feature_dir / "roasts"
        roasts_dir.mkdir(exist_ok=True)
        
        # Create old roast report
        old_roast = roasts_dir / "roast-report-999-test-feature-2026-01-01-1000.md"
        old_roast.write_text("# Old Roast\n")
        
        # Create new roast report
        new_roast = roasts_dir / "roast-report-999-test-feature-2026-01-01-1200.md"
        new_roast.write_text("# New Roast\n")
        
        bash_code, bash_stdout, _ = run_bash_script(["--json", str(feature_dir)])
        python_code, python_stdout, _ = run_python_script(["--json", str(feature_dir)])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        try:
            bash_json = json.loads(bash_stdout)
            python_json = json.loads(python_stdout)
            
            # Both should return the same report
            if bash_json["REPORT_FILE"] != python_json["REPORT_FILE"]:
                print_fail("Report files differ")
                return False
            
            # Verify it's the newer report
            if "1200" not in bash_json["REPORT_FILE"]:
                print_fail("Should return the latest roast report")
                return False
            
            print_success("Latest roast report selected correctly")
            return True
        except json.JSONDecodeError as e:
            print_fail("JSON parse error: " + str(e))
            return False
    finally:
        cleanup_test_features()


def test_absolute_path_feature_dir():
    """Test with absolute path to feature directory."""
    print_header("Test: Absolute Path to Feature Directory")
    
    try:
        cleanup_test_features()
        feature_dir, roast_file = setup_test_feature_with_roast()
        
        return compare_outputs(
            "Absolute path to feature directory",
            [str(feature_dir.resolve())],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_test_features()


def test_relative_path_feature_dir():
    """Test with relative path to feature directory."""
    print_header("Test: Relative Path to Feature Directory")
    
    try:
        cleanup_test_features()
        feature_dir, roast_file = setup_test_feature_with_roast()
        
        # Change to repo root and use relative path
        original_cwd = os.getcwd()
        os.chdir(str(REPO_ROOT))
        
        try:
            return compare_outputs(
                "Relative path to feature directory",
                ["specs/999-test-feature"],
                None,
                check_json_equivalence=False
            )
        finally:
            os.chdir(original_cwd)
    finally:
        cleanup_test_features()


def run_all_tests():
    """Run all tests and return summary."""
    print("\n" + BOLD + "=" * 60 + RESET)
    print(BOLD + "SETUP-ROAST-VERIFY TEST SUITE" + RESET)
    print(BOLD + "=" * 60 + RESET)
    print("\nRepo root: " + str(REPO_ROOT))
    print("Bash script: " + str(BASH_SCRIPT))
    print("Python script: " + str(PYTHON_SCRIPT))
    
    tests = [
        ("Help", test_help),
        ("Find Latest Roast Report", test_find_latest_roast),
        ("Find Latest Roast Report (JSON)", test_find_latest_roast_json),
        ("Custom Report Path", test_custom_report_path),
        ("Custom Report Path (JSON)", test_custom_report_path_json),
        ("Relative Report Path", test_relative_report_path),
        ("JSON Fields", test_json_fields),
        ("No Roast Reports", test_no_roast_reports),
        ("Custom Report Not Found", test_custom_report_not_found),
        ("Multiple Roast Reports", test_multiple_roast_reports),
        ("Absolute Path Feature Dir", test_absolute_path_feature_dir),
        ("Relative Path Feature Dir", test_relative_path_feature_dir),
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
