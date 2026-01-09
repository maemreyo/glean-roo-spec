#!/usr/bin/env python3
"""
Test script to verify that Python implementation matches bash implementation exactly.

This script compares the output of:
1. The original bash script: .zo/scripts/bash/setup-specify-idea.sh
2. The new Python script: .zo/scripts/python/setup-specify-idea.py

Usage: python setup-specify-idea.test.py
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
BASH_SCRIPT = SCRIPT_DIR.parent / "bash" / "setup-specify-idea.sh"
PYTHON_SCRIPT = SCRIPT_DIR / "setup-specify-idea.py"
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


def cleanup_test_files():
    """Clean up test brainstorm files and feature directories."""
    # Clean up test brainstorms
    brainstorms_dir = REPO_ROOT / ".zo" / "brainstorms"
    if brainstorms_dir.exists():
        for file in brainstorms_dir.glob("test-*.md"):
            file.unlink()
    
    # Clean up test feature directories
    specs_dir = REPO_ROOT / "specs"
    if specs_dir.exists():
        for feature_dir in specs_dir.glob("999-test-*"):
            if feature_dir.is_dir():
                shutil.rmtree(feature_dir)


def setup_test_brainstorm():
    """Create a test brainstorm file."""
    brainstorms_dir = REPO_ROOT / ".zo" / "brainstorms"
    brainstorms_dir.mkdir(parents=True, exist_ok=True)
    
    brainstorm_file = brainstorms_dir / "test-brainstorm-idea.md"
    brainstorm_file.write_text("# Test Brainstorm\n\n## Ideas\nTest idea content\n")
    
    return brainstorm_file


def setup_test_feature_with_design():
    """Create a test feature directory with design file."""
    specs_dir = REPO_ROOT / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    
    feature_dir = specs_dir / "999-test-feature"
    feature_dir.mkdir(exist_ok=True)
    
    # Create design file
    (feature_dir / "design.md").write_text("# Test Design\n\n## Overview\nTest design content\n")
    
    return feature_dir


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


def test_basic_usage():
    """Test basic usage without arguments."""
    print_header("Test: Basic Usage")
    
    try:
        cleanup_test_files()
        brainstorm_file = setup_test_brainstorm()
        feature_dir = setup_test_feature_with_design()
        
        return compare_outputs(
            "Basic usage",
            [],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_test_files()


def test_json_mode():
    """Test JSON output mode."""
    print_header("Test: JSON Mode")
    
    try:
        cleanup_test_files()
        brainstorm_file = setup_test_brainstorm()
        feature_dir = setup_test_feature_with_design()
        
        return compare_outputs(
            "JSON mode output",
            ["--json"],
            None
        )
    finally:
        cleanup_test_files()


def test_custom_brainstorm_path():
    """Test with custom brainstorm file path."""
    print_header("Test: Custom Brainstorm Path")
    
    try:
        cleanup_test_files()
        brainstorm_file = setup_test_brainstorm()
        feature_dir = setup_test_feature_with_design()
        
        return compare_outputs(
            "Custom brainstorm path",
            [str(brainstorm_file)],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_test_files()


def test_custom_brainstorm_path_json():
    """Test with custom brainstorm path and JSON output."""
    print_header("Test: Custom Brainstorm Path (JSON)")
    
    try:
        cleanup_test_files()
        brainstorm_file = setup_test_brainstorm()
        feature_dir = setup_test_feature_with_design()
        
        return compare_outputs(
            "Custom brainstorm path with JSON",
            ["--json", str(brainstorm_file)],
            None
        )
    finally:
        cleanup_test_files()


def test_json_fields():
    """Test that JSON output contains all required fields."""
    print_header("Test: JSON Fields")
    
    try:
        cleanup_test_files()
        brainstorm_file = setup_test_brainstorm()
        feature_dir = setup_test_feature_with_design()
        
        bash_code, bash_stdout, _ = run_bash_script(["--json"])
        python_code, python_stdout, _ = run_python_script(["--json"])
        
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
            required_fields = ["BRAINSTORM_FILE", "SPEC_TEMPLATE", "DESIGN_FILE"]
            
            for field in required_fields:
                if field not in bash_json or field not in python_json:
                    print_fail(f"Missing field: {field}")
                    return False
                
                if bash_json[field] != python_json[field]:
                    print_fail(f"{field} differs: bash={bash_json[field]}, python={python_json[field]}")
                    return False
            
            print_success("JSON fields match")
            return True
        except Exception as e:
            print_fail("JSON parse error: " + str(e))
            return False
    finally:
        cleanup_test_files()


def test_primary_brainstorm_location():
    """Test finding brainstorm in primary location (.zo/brainstorms/)."""
    print_header("Test: Primary Brainstorm Location")
    
    try:
        cleanup_test_files()
        brainstorm_file = setup_test_brainstorm()
        feature_dir = setup_test_feature_with_design()
        
        bash_code, bash_stdout, _ = run_bash_script(["--json"])
        python_code, python_stdout, _ = run_python_script(["--json"])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        try:
            bash_json = extract_json(bash_stdout)
            python_json = extract_json(python_stdout)
            
            if bash_json is None or python_json is None:
                print_fail("Could not extract JSON from output")
                return False
            
            # Check that brainstorm file points to primary location
            if ".zo/brainstorms" not in bash_json["BRAINSTORM_FILE"]:
                print_fail("Should find brainstorm in primary location")
                return False
            
            if bash_json["BRAINSTORM_FILE"] != python_json["BRAINSTORM_FILE"]:
                print_fail("Brainstorm file paths differ")
                return False
            
            print_success("Primary brainstorm location found correctly")
            return True
        except Exception as e:
            print_fail("JSON parse error: " + str(e))
            return False
    finally:
        cleanup_test_files()


def test_legacy_feature_brainstorm_location():
    """Test finding brainstorm in legacy feature location."""
    print_header("Test: Legacy Feature Brainstorm Location")
    
    try:
        cleanup_test_files()
        
        # Create feature directory with brainstorm
        specs_dir = REPO_ROOT / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        
        feature_dir = specs_dir / "999-test-feature"
        feature_dir.mkdir(exist_ok=True)
        
        # Create design file
        (feature_dir / "design.md").write_text("# Design\n")
        
        # Create brainstorm in legacy location (feature/brainstorms/)
        feature_brainstorms_dir = feature_dir / "brainstorms"
        feature_brainstorms_dir.mkdir(exist_ok=True)
        
        legacy_brainstorm = feature_brainstorms_dir / "brainstorm-999-test-feature-2026-01-01.md"
        legacy_brainstorm.write_text("# Legacy Brainstorm\n")
        
        # Remove primary brainstorms to force legacy location
        primary_brainstorms = REPO_ROOT / ".zo" / "brainstorms"
        if primary_brainstorms.exists():
            shutil.rmtree(primary_brainstorms)
        
        bash_code, bash_stdout, _ = run_bash_script(["--json"])
        python_code, python_stdout, _ = run_python_script(["--json"])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        try:
            bash_json = extract_json(bash_stdout)
            python_json = extract_json(python_stdout)
            
            if bash_json is None or python_json is None:
                print_fail("Could not extract JSON from output")
                return False
            
            # Check that brainstorm file points to legacy location
            if bash_json["BRAINSTORM_FILE"] != python_json["BRAINSTORM_FILE"]:
                print_fail("Brainstorm file paths differ")
                return False
            
            if "brainstorms" not in bash_json["BRAINSTORM_FILE"]:
                print_fail("Should find brainstorm in legacy location")
                return False
            
            print_success("Legacy brainstorm location found correctly")
            return True
        except Exception as e:
            print_fail("JSON parse error: " + str(e))
            return False
    finally:
        cleanup_test_files()


def test_legacy_docs_brainstorm_location():
    """Test finding brainstorm in legacy docs location."""
    print_header("Test: Legacy Docs Brainstorm Location")
    
    try:
        cleanup_test_files()
        
        # Create feature directory
        specs_dir = REPO_ROOT / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        
        feature_dir = specs_dir / "999-test-feature"
        feature_dir.mkdir(exist_ok=True)
        
        # Create design file
        (feature_dir / "design.md").write_text("# Design\n")
        
        # Create brainstorm in legacy docs location
        docs_dir = REPO_ROOT / "docs" / "brainstorms"
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        legacy_brainstorm = docs_dir / "brainstorm-test-2026-01-01.md"
        legacy_brainstorm.write_text("# Legacy Docs Brainstorm\n")
        
        # Remove other brainstorms to force docs location
        primary_brainstorms = REPO_ROOT / ".zo" / "brainstorms"
        if primary_brainstorms.exists():
            shutil.rmtree(primary_brainstorms)
        
        bash_code, bash_stdout, _ = run_bash_script(["--json"])
        python_code, python_stdout, _ = run_python_script(["--json"])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        try:
            bash_json = extract_json(bash_stdout)
            python_json = extract_json(python_stdout)
            
            if bash_json is None or python_json is None:
                print_fail("Could not extract JSON from output")
                return False
            
            # Check that brainstorm file points to docs location
            if bash_json["BRAINSTORM_FILE"] != python_json["BRAINSTORM_FILE"]:
                print_fail("Brainstorm file paths differ")
                return False
            
            if "docs/brainstorms" not in bash_json["BRAINSTORM_FILE"]:
                print_fail("Should find brainstorm in docs location")
                return False
            
            print_success("Legacy docs brainstorm location found correctly")
            return True
        except Exception as e:
            print_fail("JSON parse error: " + str(e))
            return False
    finally:
        cleanup_test_files()
        
        # Clean up docs directory
        docs_dir = REPO_ROOT / "docs"
        if docs_dir.exists():
            shutil.rmtree(docs_dir)


def test_no_brainstorm_found():
    """Test when no brainstorm file is found (should error)."""
    print_header("Test: No Brainstorm Found (Should Fail)")
    
    try:
        cleanup_test_files()
        
        # Create feature directory but no brainstorm
        specs_dir = REPO_ROOT / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        
        feature_dir = specs_dir / "999-test-feature"
        feature_dir.mkdir(exist_ok=True)
        
        (feature_dir / "design.md").write_text("# Design\n")
        
        bash_code, bash_stdout, bash_stderr = run_bash_script([])
        python_code, python_stdout, python_stderr = run_python_script([])
        
        if bash_code != python_code:
            print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
            return False
        
        if bash_code == 0:
            print_fail("Expected non-zero exit code when no brainstorm found")
            return False
        
        print_success("No brainstorm handling matches")
        return True
    finally:
        cleanup_test_files()


def test_custom_brainstorm_not_found():
    """Test with custom brainstorm path that doesn't exist (should error)."""
    print_header("Test: Custom Brainstorm Not Found (Should Fail)")
    
    try:
        cleanup_test_files()
        
        bash_code, bash_stdout, bash_stderr = run_bash_script(["nonexistent-brainstorm.md"])
        python_code, python_stdout, python_stderr = run_python_script(["nonexistent-brainstorm.md"])
        
        if bash_code != python_code:
            print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
            return False
        
        if bash_code == 0:
            print_fail("Expected non-zero exit code for non-existent brainstorm")
            return False
        
        print_success("Non-existent brainstorm handling matches")
        return True
    finally:
        cleanup_test_files()


def run_all_tests():
    """Run all tests and return summary."""
    print("\n" + BOLD + "=" * 60 + RESET)
    print(BOLD + "SETUP-SPECIFY-IDEA TEST SUITE" + RESET)
    print(BOLD + "=" * 60 + RESET)
    print("\nRepo root: " + str(REPO_ROOT))
    print("Bash script: " + str(BASH_SCRIPT))
    print("Python script: " + str(PYTHON_SCRIPT))
    
    tests = [
        ("Help", test_help),
        ("Basic Usage", test_basic_usage),
        ("JSON Mode", test_json_mode),
        ("Custom Brainstorm Path", test_custom_brainstorm_path),
        ("Custom Brainstorm Path (JSON)", test_custom_brainstorm_path_json),
        ("JSON Fields", test_json_fields),
        ("Primary Brainstorm Location", test_primary_brainstorm_location),
        ("Legacy Feature Brainstorm Location", test_legacy_feature_brainstorm_location),
        ("Legacy Docs Brainstorm Location", test_legacy_docs_brainstorm_location),
        ("No Brainstorm Found", test_no_brainstorm_found),
        ("Custom Brainstorm Not Found", test_custom_brainstorm_not_found),
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
