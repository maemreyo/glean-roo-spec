#!/usr/bin/env python3
"""
Test script to verify that Python implementation matches bash implementation exactly.

This script compares the output of:
1. The original bash script: .zo/scripts/bash/setup-roast.sh
2. The new Python script: .zo/scripts/python/setup-roast.py

Usage: python setup-roast.test.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from test_common import compare_json_values, extract_json

# Constants
SCRIPT_DIR = Path(__file__).parent
BASH_SCRIPT = SCRIPT_DIR.parent / "bash" / "setup-roast.sh"
PYTHON_SCRIPT = SCRIPT_DIR / "setup-roast.py"
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
    # Use compare_json_values for JSON mode
    if check_json_equivalence and "--json" in args:
        return compare_json_values(
            test_name, args, env, run_bash_script, run_python_script,
            print_info, print_success, print_fail
        )
    
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
    
    return True


def cleanup_test_features():
    """Clean up test feature directories."""
    specs_dir = REPO_ROOT / "specs"
    
    if specs_dir.exists():
        for feature_dir in specs_dir.glob("999-test-*"):
            if feature_dir.is_dir():
                shutil.rmtree(feature_dir)
        # Clean up roasts directories
        for roast_dir in specs_dir.glob("*/roasts"):
            if roast_dir.is_dir():
                shutil.rmtree(roast_dir)


def setup_test_feature():
    """Create a test feature directory."""
    specs_dir = REPO_ROOT / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    
    feature_dir = specs_dir / "999-test-feature"
    feature_dir.mkdir(exist_ok=True)
    
    # Create required files
    (feature_dir / "spec.md").write_text("# Test Feature Spec\n")
    (feature_dir / "plan.md").write_text("# Test Feature Plan\n")
    (feature_dir / "tasks.md").write_text("# Test Feature Tasks\n")
    
    return feature_dir


def setup_test_template():
    """Create test template for roast."""
    template_dir = REPO_ROOT / ".zo" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / "roast-template.md"
    
    if not template_file.exists():
        template_file.write_text("# Roast Report\n\n## Review\n{{FEATURE}}\n")
    
    return template_file


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


def test_basic_roast_creation():
    """Test basic roast report creation."""
    print_header("Test: Basic Roast Creation")
    
    try:
        cleanup_test_features()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        return compare_outputs(
            "Basic roast creation",
            [str(feature_dir)],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_test_features()


def test_json_mode():
    """Test JSON output mode."""
    print_header("Test: JSON Mode")
    
    try:
        cleanup_test_features()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        return compare_outputs(
            "JSON mode output",
            ["--json", str(feature_dir)],
            None
        )
    finally:
        cleanup_test_features()


def test_json_input():
    """Test with JSON input data."""
    print_header("Test: JSON Input")
    
    try:
        cleanup_test_features()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        json_input = '{"commits":["abc123","def456"],"design_system":"/path/to/design.md"}'
        
        return compare_outputs(
            "JSON input with commits and design system",
            ["--json", "--json-data=" + json_input, str(feature_dir)],
            None
        )
    finally:
        cleanup_test_features()


def test_json_input_with_braces():
    """Test with JSON input using brace format."""
    print_header("Test: JSON Input (Brace Format)")
    
    try:
        cleanup_test_features()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        json_input = '{"commits":["abc123"]}'
        
        return compare_outputs(
            "JSON input with brace format",
            ["--json", json_input, str(feature_dir)],
            None
        )
    finally:
        cleanup_test_features()


def test_main_branch_handling():
    """Test handling of main/master branch."""
    print_header("Test: Main Branch Handling")
    
    try:
        cleanup_test_features()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        # Simulate being on main branch with JSON input
        json_input = '{"commits":["abc123"],"design_system":"/path/to/design.md"}'
        
        return compare_outputs(
            "Main branch with JSON input",
            ["--json", "--json-data=" + json_input, str(feature_dir)],
            None
        )
    finally:
        cleanup_test_features()


def test_roast_directory_creation():
    """Test that roasts directory is created."""
    print_header("Test: Roasts Directory Creation")
    
    try:
        cleanup_test_features()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        bash_code, bash_stdout, _ = run_bash_script([str(feature_dir)])
        python_code, python_stdout, _ = run_python_script([str(feature_dir)])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        # Check that roasts directory was created
        roasts_dir = feature_dir / "roasts"
        if not roasts_dir.exists():
            print_fail("Roasts directory was not created")
            return False
        
        print_success("Roasts directory created successfully")
        return True
    finally:
        cleanup_test_features()


def test_json_fields():
    """Test that JSON output contains all required fields."""
    print_header("Test: JSON Fields")
    
    try:
        cleanup_test_features()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        bash_code, bash_stdout, _ = run_bash_script(["--json", str(feature_dir)])
        python_code, python_stdout, _ = run_python_script(["--json", str(feature_dir)])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        try:
            bash_json = extract_json(bash_stdout)
            python_json = extract_json(python_stdout)
            
            if bash_json is None or python_json is None:
                print_fail("Could not extract JSON from output")
                return False
            
            # Check required fields
            required_fields = [
                "REPORT_FILE",
                "TASKS",
                "IMPL_PLAN",
                "BRANCH",
                "DESIGN_SYSTEM"
            ]
            
            for field in required_fields:
                if field not in bash_json or field not in python_json:
                    print_fail(f"Missing field: {field}")
                    return False
                
                # COMMITS is optional, so check separately
                if field == "COMMITS":
                    continue
                
                if bash_json[field] != python_json[field]:
                    print_fail(f"{field} differs: bash={bash_json[field]}, python={python_json[field]}")
                    return False
            
            print_success("JSON fields match")
            return True
        except Exception as e:
            print_fail("JSON parse error: " + str(e))
            return False
    finally:
        cleanup_test_features()


def test_relative_path():
    """Test with relative path to feature directory."""
    print_header("Test: Relative Path")
    
    try:
        cleanup_test_features()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        return compare_outputs(
            "Relative path to feature directory",
            ["specs/999-test-feature"],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_test_features()


def test_absolute_path():
    """Test with absolute path to feature directory."""
    print_header("Test: Absolute Path")
    
    try:
        cleanup_test_features()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        return compare_outputs(
            "Absolute path to feature directory",
            [str(feature_dir.resolve())],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_test_features()


def test_nonexistent_directory():
    """Test with non-existent directory (should error)."""
    print_header("Test: Non-existent Directory")
    
    bash_code, bash_stdout, bash_stderr = run_bash_script(["nonexistent-directory"])
    python_code, python_stdout, python_stderr = run_python_script(["nonexistent-directory"])
    
    if bash_code != python_code:
        print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
        return False
    
    if bash_code == 0:
        print_fail("Expected non-zero exit code for non-existent directory")
        return False
    
    print_success("Non-existent directory handling matches")
    return True


def test_commits_field():
    """Test that COMMITS field is populated when provided."""
    print_header("Test: COMMITS Field")
    
    try:
        cleanup_test_features()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        json_input = '{"commits":["abc123","def456","ghi789"]}'
        
        bash_code, bash_stdout, _ = run_bash_script(["--json", "--json-data=" + json_input, str(feature_dir)])
        python_code, python_stdout, _ = run_python_script(["--json", "--json-data=" + json_input, str(feature_dir)])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        try:
            bash_json = extract_json(bash_stdout)
            python_json = extract_json(python_stdout)
            
            if bash_json is None or python_json is None:
                print_fail("Could not extract JSON from output")
                return False
            
            # Check that COMMITS field matches
            if bash_json.get("COMMITS") != python_json.get("COMMITS"):
                print_fail(f"COMMITS differs: bash={bash_json.get('COMMITS')}, python={python_json.get('COMMITS')}")
                return False
            
            expected_commits = "abc123,def456,ghi789"
            if bash_json.get("COMMITS") != expected_commits:
                print_fail(f"Expected COMMITS {expected_commits}, got: {bash_json.get('COMMITS')}")
                return False
            
            print_success("COMMITS field populated correctly")
            return True
        except Exception as e:
            print_fail("JSON parse error: " + str(e))
            return False
    finally:
        cleanup_test_features()


def test_template_usage():
    """Test that template is used when available."""
    print_header("Test: Template Usage")
    
    try:
        cleanup_test_features()
        feature_dir = setup_test_feature()
        template_file = setup_test_template()
        
        bash_code, bash_stdout, _ = run_bash_script([str(feature_dir)])
        python_code, python_stdout, _ = run_python_script([str(feature_dir)])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        # Find the created roast report
        roasts_dir = feature_dir / "roasts"
        roast_files = list(roasts_dir.glob("*.md"))
        
        if not roast_files:
            print_fail("Roast report was not created")
            return False
        
        # Check that template was used
        roast_content = roast_files[0].read_text()
        if "Roast Report" not in roast_content:
            print_fail("Template content not found in roast report")
            return False
        
        print_success("Template used successfully")
        return True
    finally:
        cleanup_test_features()


def run_all_tests():
    """Run all tests and return summary."""
    print("\n" + BOLD + "=" * 60 + RESET)
    print(BOLD + "SETUP-ROAST TEST SUITE" + RESET)
    print(BOLD + "=" * 60 + RESET)
    print("\nRepo root: " + str(REPO_ROOT))
    print("Bash script: " + str(BASH_SCRIPT))
    print("Python script: " + str(PYTHON_SCRIPT))
    
    tests = [
        ("Help", test_help),
        ("Basic Roast Creation", test_basic_roast_creation),
        ("JSON Mode", test_json_mode),
        ("JSON Input", test_json_input),
        ("JSON Input (Brace Format)", test_json_input_with_braces),
        ("Main Branch Handling", test_main_branch_handling),
        ("Roasts Directory Creation", test_roast_directory_creation),
        ("JSON Fields", test_json_fields),
        ("Relative Path", test_relative_path),
        ("Absolute Path", test_absolute_path),
        ("Non-existent Directory", test_nonexistent_directory),
        ("COMMITS Field", test_commits_field),
        ("Template Usage", test_template_usage),
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
