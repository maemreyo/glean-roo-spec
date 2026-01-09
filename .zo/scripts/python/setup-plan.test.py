#!/usr/bin/env python3
"""
Test script to verify that Python implementation matches bash implementation exactly.

This script compares the output of:
1. The original bash script: .zo/scripts/bash/setup-plan.sh
2. The new Python script: .zo/scripts/python/setup-plan.py

Usage: python setup-plan.test.py
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
BASH_SCRIPT = SCRIPT_DIR.parent / "bash" / "setup-plan.sh"
PYTHON_SCRIPT = SCRIPT_DIR / "setup-plan.py"
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


def create_test_feature_dir():
    """Create a test feature directory."""
    temp_dir = tempfile.mkdtemp()
    feature_dir = Path(temp_dir) / "999-test-feature"
    feature_dir.mkdir(parents=True, exist_ok=True)
    
    # Create spec.md
    (feature_dir / "spec.md").write_text("# Test Feature Spec\n")
    
    env = {
        "SPECIFY_FEATURE": "999-test-feature",
        "SPECS_DIR": str(feature_dir.parent),
    }
    
    return feature_dir, env


def cleanup_test_feature(dir_path):
    """Clean up test feature directory."""
    if dir_path and dir_path.exists():
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


def test_text_mode():
    """Test text mode output."""
    print_header("Test: Text Mode Output")
    
    feature_dir, env = create_test_feature_dir()
    try:
        return compare_outputs(
            "Text mode output",
            [],
            env,
            check_json_equivalence=False
        )
    finally:
        cleanup_test_feature(feature_dir)


def test_json_mode():
    """Test JSON mode output."""
    print_header("Test: JSON Mode Output")
    
    feature_dir, env = create_test_feature_dir()
    try:
        return compare_json_values(
            "JSON mode output",
            ["--json"],
            env
        )
    finally:
        cleanup_test_feature(feature_dir)


def test_json_fields():
    """Test that JSON output contains all required fields."""
    print_header("Test: JSON Fields")
    
    feature_dir, env = create_test_feature_dir()
    try:
        bash_code, bash_stdout, _ = run_bash_script(["--json"], env)
        python_code, python_stdout, _ = run_python_script(["--json"], env)
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        bash_json = extract_json(bash_stdout)
        python_json = extract_json(python_stdout)
        
        # Check required fields
        required_fields = [
            "FEATURE_SPEC",
            "IMPL_PLAN",
            "DESIGN_FILE",
            "SPECS_DIR",
            "BRANCH",
            "HAS_GIT"
        ]
        
        for field in required_fields:
            if field not in bash_json or field not in python_json:
                print_fail(f"Missing field: {field}")
                return False
            
            if bash_json[field] != python_json[field]:
                print_fail(f"{field} differs: bash={bash_json[field]}, python={python_json[field]}")
                return False
        
        print_success("JSON fields match")
        return True
    finally:
        cleanup_test_feature(feature_dir)


def test_plan_creation():
    """Test that plan.md file is created."""
    print_header("Test: Plan File Creation")
    
    # Create template
    template_dir = REPO_ROOT / ".zo" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / "plan-template.md"
    template_file.write_text("# Implementation Plan\n\n## Tasks\n")
    
    feature_dir, env = create_test_feature_dir()
    
    try:
        # Run the script
        bash_code, bash_stdout, _ = run_bash_script([], env)
        python_code, python_stdout, _ = run_python_script([], env)
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        # Check that plan.md was created
        plan_file = feature_dir / "plan.md"
        if not plan_file.exists():
            print_fail("Plan file was not created")
            return False
        
        print_success("Plan file created successfully")
        return True
    finally:
        cleanup_test_feature(feature_dir)


def test_template_usage():
    """Test that template is used when available."""
    print_header("Test: Template Usage")
    
    # Create template
    template_dir = REPO_ROOT / ".zo" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / "plan-template.md"
    
    template_content = """# Implementation Plan for {{FEATURE}}

## Overview
This plan outlines the implementation strategy.

## Tasks
- Task 1
- Task 2
"""
    template_file.write_text(template_content)
    
    feature_dir, env = create_test_feature_dir()
    
    try:
        bash_code, bash_stdout, _ = run_bash_script([], env)
        python_code, python_stdout, _ = run_python_script([], env)
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        # Check that plan.md was created with content
        plan_file = feature_dir / "plan.md"
        if not plan_file.exists():
            print_fail("Plan file was not created")
            return False
        
        plan_content = plan_file.read_text()
        if "Implementation Plan" not in plan_content:
            print_fail("Template content not found in plan file")
            return False
        
        print_success("Template used successfully")
        return True
    finally:
        cleanup_test_feature(feature_dir)


def test_missing_template():
    """Test behavior when template is missing."""
    print_header("Test: Missing Template")
    
    # Remove template if it exists
    template_file = REPO_ROOT / ".zo" / "templates" / "plan-template.md"
    template_backup = None
    
    if template_file.exists():
        template_backup = template_file.read_text()
        template_file.unlink()
    
    feature_dir, env = create_test_feature_dir()
    
    try:
        bash_code, bash_stdout, bash_stderr = run_bash_script([], env)
        python_code, python_stdout, python_stderr = run_python_script([], env)
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        # Check that plan.md was created even without template
        plan_file = feature_dir / "plan.md"
        if not plan_file.exists():
            print_fail("Plan file was not created (should create empty file)")
            return False
        
        print_success("Plan file created without template")
        return True
    finally:
        cleanup_test_feature(feature_dir)
        
        # Restore template if it was backed up
        if template_backup:
            template_file.parent.mkdir(parents=True, exist_ok=True)
            template_file.write_text(template_backup)


def test_directory_creation():
    """Test that feature directory is created if it doesn't exist."""
    print_header("Test: Directory Creation")
    
    temp_dir = tempfile.mkdtemp()
    feature_dir = Path(temp_dir) / "999-new-feature"
    
    # Don't create the directory - let the script do it
    env = {
        "SPECIFY_FEATURE": "999-new-feature",
        "SPECS_DIR": str(Path(temp_dir)),
    }
    
    try:
        bash_code, bash_stdout, _ = run_bash_script([], env)
        python_code, python_stdout, _ = run_python_script([], env)
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        if not feature_dir.exists():
            print_fail("Feature directory was not created")
            return False
        
        plan_file = feature_dir / "plan.md"
        if not plan_file.exists():
            print_fail("Plan file was not created")
            return False
        
        print_success("Directory created successfully")
        return True
    finally:
        shutil.rmtree(temp_dir)


def test_has_git_detection():
    """Test HAS_GIT field detection."""
    print_header("Test: HAS_GIT Detection")
    
    feature_dir, env = create_test_feature_dir()
    
    try:
        bash_code, bash_stdout, _ = run_bash_script(["--json"], env)
        python_code, python_stdout, _ = run_python_script(["--json"], env)
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        bash_json = extract_json(bash_stdout)
        python_json = extract_json(python_stdout)
        
        if bash_json is None or python_json is None:
            print_fail("Could not extract JSON")
            return False
        
        # HAS_GIT should be a boolean or string 'true'/'false'
        bash_has_git = bash_json.get("HAS_GIT")
        python_has_git = python_json.get("HAS_GIT")
        
        if bash_has_git != python_has_git:
            print_fail(f"HAS_GIT differs: bash={bash_has_git}, python={python_has_git}")
            return False
        
        print_success(f"HAS_GIT detection matches: {bash_has_git}")
        return True
    finally:
        cleanup_test_feature(feature_dir)


def run_all_tests():
    """Run all tests and return summary."""
    print("\n" + BOLD + "=" * 60 + RESET)
    print(BOLD + "SETUP-PLAN TEST SUITE" + RESET)
    print(BOLD + "=" * 60 + RESET)
    print("\nRepo root: " + str(REPO_ROOT))
    print("Bash script: " + str(BASH_SCRIPT))
    print("Python script: " + str(PYTHON_SCRIPT))
    
    tests = [
        ("Help", test_help),
        ("Text Mode", test_text_mode),
        ("JSON Mode", test_json_mode),
        ("JSON Fields", test_json_fields),
        ("Plan Creation", test_plan_creation),
        ("Template Usage", test_template_usage),
        ("Missing Template", test_missing_template),
        ("Directory Creation", test_directory_creation),
        ("HAS_GIT Detection", test_has_git_detection),
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
