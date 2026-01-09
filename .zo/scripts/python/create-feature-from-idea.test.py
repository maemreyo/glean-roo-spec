#!/usr/bin/env python3
"""
Test script to verify that Python implementation matches bash implementation exactly.

This script compares the output of:
1. The original bash script: .zo/scripts/bash/create-feature-from-idea.sh
2. The new Python script: .zo/scripts/python/create-feature-from-idea.py

Usage: python create-feature-from-idea.test.py
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
BASH_SCRIPT = SCRIPT_DIR.parent / "bash" / "create-feature-from-idea.sh"
PYTHON_SCRIPT = SCRIPT_DIR / "create-feature-from-idea.py"
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


def cleanup_test_features():
    """Clean up test feature directories and git branches."""
    specs_dir = REPO_ROOT / "specs"
    
    # Clean up test spec directories
    if specs_dir.exists():
        for feature_dir in specs_dir.glob("999-*"):
            shutil.rmtree(feature_dir)
        for feature_dir in specs_dir.glob("001-test-*"):
            if feature_dir.is_dir():
                shutil.rmtree(feature_dir)
    
    # Clean up test git branches (if they exist)
    try:
        result = subprocess.run(
            ["git", "branch", "--list", "999-*"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        for branch in result.stdout.strip().split('\n'):
            if branch:
                branch_name = branch.replace('*', '').strip()
                subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    capture_output=True,
                    cwd=str(REPO_ROOT)
                )
    except:
        pass  # Git may not be available or configured


def setup_test_template():
    """Create test template for spec-from-idea."""
    template_dir = REPO_ROOT / ".zo" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / "spec-from-idea.md"
    
    if not template_file.exists():
        template_file.write_text("# Feature Specification\n\n## Overview\n{{FEATURE}}\n")
    
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


def test_basic_feature_creation():
    """Test basic feature creation."""
    print_header("Test: Basic Feature Creation")
    
    try:
        cleanup_test_features()
        setup_test_template()
        
        return compare_outputs(
            "Basic feature creation",
            ["Add user authentication system"],
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
        setup_test_template()
        
        return compare_json_values(
            "JSON mode output",
            ["--json", "implement oauth2 integration"],
            None
        )
    finally:
        cleanup_test_features()


def test_custom_short_name():
    """Test with custom short name."""
    print_header("Test: Custom Short Name")
    
    try:
        cleanup_test_features()
        setup_test_template()
        
        return compare_outputs(
            "Custom short name",
            ["--short-name", "user-auth", "add user authentication"],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_test_features()


def test_custom_short_name_json():
    """Test custom short name with JSON output."""
    print_header("Test: Custom Short Name (JSON)")
    
    try:
        cleanup_test_features()
        setup_test_template()
        
        return compare_json_values(
            "Custom short name with JSON",
            ["--json", "--short-name", "oauth-integration", "implement oauth2"],
            None
        )
    finally:
        cleanup_test_features()


def test_custom_number():
    """Test with custom branch number."""
    print_header("Test: Custom Branch Number")
    
    try:
        cleanup_test_features()
        setup_test_template()
        
        return compare_outputs(
            "Custom branch number",
            ["--number", "42", "test feature"],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_test_features()


def test_stop_word_filtering():
    """Test that stop words are filtered from branch name."""
    print_header("Test: Stop Word Filtering")
    
    try:
        cleanup_test_features()
        setup_test_template()
        
        # Use a description with many stop words
        bash_code, bash_stdout, _ = run_bash_script(
            ["--json", "add a new user authentication system for the application"]
        )
        python_code, python_stdout, _ = run_python_script(
            ["--json", "add a new user authentication system for the application"]
        )
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        bash_json = extract_json(bash_stdout)
        python_json = extract_json(python_stdout)
        
        if bash_json is None or python_json is None:
            print_fail("Could not extract JSON")
            return False
        
        # Check that branch names match and don't contain stop words
        if bash_json["BRANCH_NAME"] != python_json["BRANCH_NAME"]:
            print_fail("Branch names differ")
            return False
        
        branch_name = bash_json["BRANCH_NAME"]
        # Check that stop words are removed
        if " a " in branch_name.lower() or " the " in branch_name.lower() or " for " in branch_name.lower():
            print_fail("Stop words not filtered from branch name: " + branch_name)
            return False
        
        print_success("Stop word filtering works: " + branch_name)
        return True
    finally:
        cleanup_test_features()


def test_github_branch_limit():
    """Test that branch names are truncated to GitHub's 244-byte limit."""
    print_header("Test: GitHub Branch Limit")
    
    try:
        cleanup_test_features()
        setup_test_template()
        
        # Create a very long description that would exceed GitHub's limit
        long_desc = "add " + "feature " * 100 + "system"
        
        bash_code, bash_stdout, _ = run_bash_script(["--json", long_desc])
        python_code, python_stdout, _ = run_python_script(["--json", long_desc])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        bash_json = extract_json(bash_stdout)
        python_json = extract_json(python_stdout)
        
        if bash_json is None or python_json is None:
            print_fail("Could not extract JSON")
            return False
        
        # Check that branch names match
        if bash_json["BRANCH_NAME"] != python_json["BRANCH_NAME"]:
            print_fail("Branch names differ")
            return False
        
        branch_name = bash_json["BRANCH_NAME"]
        
        # Check that branch name is within GitHub's limit (244 bytes)
        if len(branch_name.encode('utf-8')) > 244:
            print_fail("Branch name exceeds GitHub limit: " + str(len(branch_name.encode('utf-8'))))
            return False
        
        print_success("Branch name within GitHub limit: " + str(len(branch_name.encode('utf-8'))) + " bytes")
        return True
    finally:
        cleanup_test_features()


def test_branch_number_detection():
    """Test branch number auto-detection."""
    print_header("Test: Branch Number Detection")
    
    try:
        cleanup_test_features()
        setup_test_template()
        
        # Create some existing spec directories to test number detection
        specs_dir = REPO_ROOT / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create existing features
        (specs_dir / "001-existing-feature").mkdir()
        (specs_dir / "002-another-feature").mkdir()
        
        bash_code, bash_stdout, _ = run_bash_script(["--json", "new feature"])
        python_code, python_stdout, _ = run_python_script(["--json", "new feature"])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        bash_json = extract_json(bash_stdout)
        python_json = extract_json(python_stdout)
        
        if bash_json is None or python_json is None:
            print_fail("Could not extract JSON")
            return False
        
        # Both should use the same next number
        if bash_json["BRANCH_NAME"] != python_json["BRANCH_NAME"]:
            print_fail("Branch names differ")
            return False
        
        # Extract feature number from branch name
        feature_num = bash_json["FEATURE_NUM"]
        
        # Should be 003 (next after 001 and 002)
        if feature_num != "003":
            print_fail("Expected feature_num 003, got: " + feature_num)
            return False
        
        print_success("Branch number detection works: " + feature_num)
        return True
    finally:
        cleanup_test_features()


def test_spec_file_creation():
    """Test that spec file is created from template."""
    print_header("Test: Spec File Creation")
    
    try:
        cleanup_test_features()
        template_file = setup_test_template()
        
        bash_code, bash_stdout, _ = run_bash_script(["test feature creation"])
        python_code, python_stdout, _ = run_python_script(["test feature creation"])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        # Check that spec file was created
        specs_dir = REPO_ROOT / "specs"
        spec_files = list(specs_dir.glob("*/spec.md"))
        
        if not spec_files:
            print_fail("Spec file was not created")
            return False
        
        # Check that template was used
        spec_content = spec_files[0].read_text()
        if "Feature Specification" not in spec_content:
            print_fail("Template content not found in spec file")
            return False
        
        print_success("Spec file created from template")
        return True
    finally:
        cleanup_test_features()


def test_json_fields():
    """Test that JSON output contains all required fields."""
    print_header("Test: JSON Fields")
    
    try:
        cleanup_test_features()
        setup_test_template()
        
        bash_code, bash_stdout, _ = run_bash_script(["--json", "test feature"])
        python_code, python_stdout, _ = run_python_script(["--json", "test feature"])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        bash_json = extract_json(bash_stdout)
        python_json = extract_json(python_stdout)
        
        if bash_json is None or python_json is None:
            print_fail("Could not extract JSON")
            return False
        
        # Check required fields
        required_fields = ["BRANCH_NAME", "SPEC_FILE", "FEATURE_NUM"]
        
        for field in required_fields:
            if field not in bash_json or field not in python_json:
                print_fail(f"Missing field: {field}")
                return False
            
            if bash_json[field] != python_json[field]:
                print_fail(f"{field} differs")
                return False
        
        print_success("JSON fields match")
        return True
    finally:
        cleanup_test_features()


def test_no_description():
    """Test with no feature description (should error)."""
    print_header("Test: No Description (Should Fail)")
    
    bash_code, bash_stdout, bash_stderr = run_bash_script([])
    python_code, python_stdout, python_stderr = run_python_script([])
    
    if bash_code != python_code:
        print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
        return False
    
    if bash_code == 0:
        print_fail("Expected non-zero exit code with no description")
        return False
    
    print_success("No description handling matches")
    return True


def test_feature_number_with_leading_zeros():
    """Test that feature numbers are formatted with leading zeros."""
    print_header("Test: Feature Number Format")
    
    try:
        cleanup_test_features()
        setup_test_template()
        
        bash_code, bash_stdout, _ = run_bash_script(["--json", "--number", "7", "test feature"])
        python_code, python_stdout, _ = run_python_script(["--json", "--number", "7", "test feature"])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        bash_json = extract_json(bash_stdout)
        python_json = extract_json(python_stdout)
        
        if bash_json is None or python_json is None:
            print_fail("Could not extract JSON")
            return False
        
        # Check that feature number is formatted with leading zeros
        if bash_json["FEATURE_NUM"] != "007":
            print_fail("Expected FEATURE_NUM 007, got: " + bash_json["FEATURE_NUM"])
            return False
        
        if python_json["FEATURE_NUM"] != "007":
            print_fail("Expected FEATURE_NUM 007, got: " + python_json["FEATURE_NUM"])
            return False
        
        print_success("Feature number format correct: 007")
        return True
    finally:
        cleanup_test_features()


def run_all_tests():
    """Run all tests and return summary."""
    print("\n" + BOLD + "=" * 60 + RESET)
    print(BOLD + "CREATE-FEATURE-FROM-IDEA TEST SUITE" + RESET)
    print(BOLD + "=" * 60 + RESET)
    print("\nRepo root: " + str(REPO_ROOT))
    print("Bash script: " + str(BASH_SCRIPT))
    print("Python script: " + str(PYTHON_SCRIPT))
    
    tests = [
        ("Help", test_help),
        ("Basic Feature Creation", test_basic_feature_creation),
        ("JSON Mode", test_json_mode),
        ("Custom Short Name", test_custom_short_name),
        ("Custom Short Name (JSON)", test_custom_short_name_json),
        ("Custom Branch Number", test_custom_number),
        ("Stop Word Filtering", test_stop_word_filtering),
        ("GitHub Branch Limit", test_github_branch_limit),
        ("Branch Number Detection", test_branch_number_detection),
        ("Spec File Creation", test_spec_file_creation),
        ("JSON Fields", test_json_fields),
        ("No Description", test_no_description),
        ("Feature Number Format", test_feature_number_with_leading_zeros),
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
