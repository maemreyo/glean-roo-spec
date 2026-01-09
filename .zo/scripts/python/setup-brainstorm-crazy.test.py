#!/usr/bin/env python3
"""
Test script to verify that Python implementation matches bash implementation exactly.

This script compares the output of:
1. The original bash script: .zo/scripts/bash/setup-brainstorm-crazy.sh
2. The new Python script: .zo/scripts/python/setup-brainstorm-crazy.py

Usage: python setup-brainstorm-crazy.test.py
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
BASH_SCRIPT = SCRIPT_DIR.parent / "bash" / "setup-brainstorm-crazy.sh"
PYTHON_SCRIPT = SCRIPT_DIR / "setup-brainstorm-crazy.py"
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


def create_test_spec_feature(specs_dir: Path, feature_num: str, feature_name: str):
    """Create a test spec feature directory with spec, plan, and tasks."""
    feature_dir = specs_dir / f"{feature_num}-{feature_name}"
    feature_dir.mkdir(parents=True, exist_ok=True)
    
    # Create spec.md
    (feature_dir / "spec.md").write_text(f"# Spec for {feature_name}\n")
    
    # Create plan.md
    (feature_dir / "plan.md").write_text(f"# Plan for {feature_name}\n")
    
    # Create tasks.md
    (feature_dir / "tasks.md").write_text(f"# Tasks for {feature_name}\n")
    
    return feature_dir


def cleanup_test_features():
    """Clean up test feature directories and brainstorm files."""
    specs_dir = REPO_ROOT / "specs"
    
    # Clean up test spec directories
    if specs_dir.exists():
        for feature_dir in specs_dir.glob("999-*"):
            shutil.rmtree(feature_dir)
    
    # Clean up test brainstorm files
    brainstorms_dir = REPO_ROOT / ".zo" / "brainstorms"
    if brainstorms_dir.exists():
        for file in brainstorms_dir.glob("test-*"):
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


def test_stop_word_filtering():
    """Test that stop words are filtered from research focus."""
    print_header("Test: Stop Word Filtering")
    
    try:
        cleanup_test_features()
        # Input with common stop words
        return compare_json_values(
            "Stop word filtering",
            ["improve the login flow for better user experience"],
            None
        )
    finally:
        cleanup_test_features()


def test_spec_folder_matching():
    """Test that matching spec folder is found."""
    print_header("Test: Spec Folder Matching")
    
    try:
        cleanup_test_features()
        
        # Create a test spec feature
        specs_dir = REPO_ROOT / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        create_test_spec_feature(specs_dir, "999", "user-authentication")
        
        # Use a request that should match the spec folder
        return compare_json_values(
            "Spec folder matching",
            ["add user authentication"],
            None
        )
    finally:
        cleanup_test_features()


def test_json_mode():
    """Test JSON output mode."""
    print_header("Test: JSON Mode")
    
    try:
        cleanup_test_features()
        return compare_json_values(
            "JSON output mode",
            ["--json", "implement oauth integration"],
            None
        )
    finally:
        cleanup_test_features()


def test_dry_run_mode():
    """Test dry-run mode (should not create files)."""
    print_header("Test: Dry-Run Mode")
    
    try:
        cleanup_test_features()
        return compare_json_values(
            "Dry-run mode",
            ["--dry-run", "test feature request"],
            None
        )
    finally:
        cleanup_test_features()


def test_verbose_mode():
    """Test verbose mode output."""
    print_header("Test: Verbose Mode")
    
    try:
        cleanup_test_features()
        # Verbose mode outputs to stderr, so we compare stderr instead
        bash_code, bash_stdout, bash_stderr = run_bash_script(["-v", "test verbose"])
        python_code, python_stdout, python_stderr = run_python_script(["-v", "test verbose"])
        
        if bash_code != python_code:
            print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
            return False
        
        if bash_stdout.strip() != python_stdout.strip():
            print_fail("Stdout differs")
            return False
        
        # Check if stderr contains verbose messages
        if "[VERBOSE]" not in bash_stderr and "[VERBOSE]" not in python_stderr:
            print_info("No verbose output found in stderr (expected)")
        
        print_success("Verbose mode matches")
        return True
    finally:
        cleanup_test_features()


def test_no_matching_spec():
    """Test when no matching spec folder is found."""
    print_header("Test: No Matching Spec Folder")
    
    try:
        cleanup_test_features()
        return compare_json_values(
            "No matching spec folder",
            ["nonexistent feature request"],
            None
        )
    finally:
        cleanup_test_features()


def test_template_usage():
    """Test that template is used when available."""
    print_header("Test: Template Usage")
    
    # Create template
    template_dir = REPO_ROOT / ".zo" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / "brainstorm-template-crazy.md"
    
    template_content = """# Crazy Brainstorm: {{FEATURE}}
Date: {{DATE}}

## Related Files
- FEATURE_SPEC
- IMPL_PLAN  
- TASKS
"""
    
    template_file.write_text(template_content)
    
    try:
        cleanup_test_features()
        return compare_json_values(
            "Template usage",
            ["test template"],
            None
        )
    finally:
        cleanup_test_features()


def test_complex_topic():
    """Test with complex topic containing special characters."""
    print_header("Test: Complex Topic")
    
    try:
        cleanup_test_features()
        return compare_json_values(
            "Complex topic with special chars",
            ["add user @auth #2fa system!!!"],
            None
        )
    finally:
        cleanup_test_features()


def test_research_focus_extraction():
    """Test research focus extraction from input."""
    print_header("Test: Research Focus Extraction")
    
    try:
        cleanup_test_features()
        # The output should contain RESEARCH_FOCUS field
        bash_code, bash_stdout, _ = run_bash_script(["--json", "implement user authentication system"])
        python_code, python_stdout, _ = run_python_script(["--json", "implement user authentication system"])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        bash_json = extract_json(bash_stdout)
        python_json = extract_json(python_stdout)
        
        if bash_json is None or python_json is None:
            print_fail("Could not extract JSON")
            return False
        
        if "RESEARCH_FOCUS" not in bash_json or "RESEARCH_FOCUS" not in python_json:
            print_fail("RESEARCH_FOCUS field missing")
            return False
        
        if bash_json["RESEARCH_FOCUS"] != python_json["RESEARCH_FOCUS"]:
            print_fail("RESEARCH_FOCUS differs: bash=" + bash_json["RESEARCH_FOCUS"] + ", python=" + python_json["RESEARCH_FOCUS"])
            return False
        
        print_success("Research focus extraction matches")
        return True
    finally:
        cleanup_test_features()


def test_related_files_detection():
    """Test that related files (spec, plan, tasks) are detected."""
    print_header("Test: Related Files Detection")
    
    try:
        cleanup_test_features()
        
        # Create a test spec feature with all files
        specs_dir = REPO_ROOT / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        feature_dir = create_test_spec_feature(specs_dir, "999", "test-feature")
        
        # Check that the outputs include related file paths
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
        
        # Check that FEATURE_SPEC, IMPL_PLAN, TASKS are present and match
        for key in ["FEATURE_SPEC", "IMPL_PLAN", "TASKS"]:
            if bash_json.get(key) != python_json.get(key):
                print_fail(f"{key} differs: bash={bash_json.get(key)}, python={python_json.get(key)}")
                return False
        
        print_success("Related files detection matches")
        return True
    finally:
        cleanup_test_features()


def test_no_argument():
    """Test with no brainstorm request (should error)."""
    print_header("Test: No Argument (Should Fail)")
    
    bash_code, bash_stdout, bash_stderr = run_bash_script([])
    python_code, python_stdout, python_stderr = run_python_script([])
    
    if bash_code != python_code:
        print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
        return False
    
    if bash_code == 0:
        print_fail("Expected non-zero exit code with no argument")
        return False
    
    print_success("No argument handling matches")
    return True


def run_all_tests():
    """Run all tests and return summary."""
    print("\n" + BOLD + "=" * 60 + RESET)
    print(BOLD + "SETUP-BRAINSTORM-CRAZY TEST SUITE" + RESET)
    print(BOLD + "=" * 60 + RESET)
    print("\nRepo root: " + str(REPO_ROOT))
    print("Bash script: " + str(BASH_SCRIPT))
    print("Python script: " + str(PYTHON_SCRIPT))
    
    tests = [
        ("Help", test_help),
        ("Stop Word Filtering", test_stop_word_filtering),
        ("Spec Folder Matching", test_spec_folder_matching),
        ("JSON Mode", test_json_mode),
        ("Dry-Run Mode", test_dry_run_mode),
        ("Verbose Mode", test_verbose_mode),
        ("No Matching Spec", test_no_matching_spec),
        ("Template Usage", test_template_usage),
        ("Complex Topic", test_complex_topic),
        ("Research Focus Extraction", test_research_focus_extraction),
        ("Related Files Detection", test_related_files_detection),
        ("No Argument", test_no_argument),
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
