#!/usr/bin/env python3
"""
Test script to verify that Python implementation matches bash implementation exactly.

This script compares the output of:
1. The original bash script: .zo/scripts/bash/setup-design.sh
2. The new Python script: .zo/scripts/python/setup-design.py

Usage: python setup-design.test.py
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
BASH_SCRIPT = SCRIPT_DIR.parent / "bash" / "setup-design.sh"
PYTHON_SCRIPT = SCRIPT_DIR / "setup-design.py"
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


def cleanup_design_files():
    """Clean up design files created during testing."""
    design_system = REPO_ROOT / ".zo" / "design-system.md"
    if design_system.exists():
        design_system.unlink()
    
    # Clean up test feature design files
    specs_dir = REPO_ROOT / "specs"
    if specs_dir.exists():
        for design_file in specs_dir.glob("*/design.md"):
            if "999-test" in str(design_file):
                design_file.unlink()


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


def test_global_mode():
    """Test global mode (--global flag)."""
    print_header("Test: Global Mode")
    
    try:
        cleanup_design_files()
        
        # Create template
        template_dir = REPO_ROOT / ".zo" / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / "design-system-template.md"
        template_file.write_text("# Design System\n\n{{FEATURE}}\n")
        
        return compare_outputs(
            "Global mode",
            ["--global"],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_design_files()


def test_global_mode_json():
    """Test global mode with JSON output."""
    print_header("Test: Global Mode (JSON)")
    
    try:
        cleanup_design_files()
        
        # Create template
        template_dir = REPO_ROOT / ".zo" / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / "design-system-template.md"
        if not template_file.exists():
            template_file.write_text("# Design System\n\n{{FEATURE}}\n")
        
        return compare_json_values(
            "Global mode with JSON",
            ["--global", "--json"],
            None
        )
    finally:
        cleanup_design_files()


def test_feature_mode():
    """Test feature mode with explicit directory."""
    print_header("Test: Feature Mode (Explicit Directory)")
    
    try:
        cleanup_design_files()
        
        # Create a test feature directory
        specs_dir = REPO_ROOT / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        feature_dir = specs_dir / "999-test-feature"
        feature_dir.mkdir(exist_ok=True)
        
        # Create spec.md
        (feature_dir / "spec.md").write_text("# Test Feature Spec\n")
        
        # Create template
        template_dir = REPO_ROOT / ".zo" / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / "design-template.md"
        template_file.write_text("# Design for [FEATURE NAME]\n")
        
        return compare_outputs(
            "Feature mode with explicit directory",
            ["specs/999-test-feature"],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_design_files()
        if (specs_dir / "999-test-feature").exists():
            shutil.rmtree(specs_dir / "999-test-feature")


def test_feature_mode_json():
    """Test feature mode with JSON output."""
    print_header("Test: Feature Mode (JSON)")
    
    try:
        cleanup_design_files()
        
        # Create a test feature directory
        specs_dir = REPO_ROOT / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        feature_dir = specs_dir / "999-test-feature"
        feature_dir.mkdir(exist_ok=True)
        
        # Create spec.md
        (feature_dir / "spec.md").write_text("# Test Feature Spec\n")
        
        # Create template
        template_dir = REPO_ROOT / ".zo" / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / "design-template.md"
        if not template_file.exists():
            template_file.write_text("# Design for [FEATURE NAME]\n")
        
        return compare_outputs(
            "Feature mode with JSON",
            ["--json", "specs/999-test-feature"],
            None
        )
    finally:
        cleanup_design_files()
        if (specs_dir / "999-test-feature").exists():
            shutil.rmtree(specs_dir / "999-test-feature")


def test_absolute_path():
    """Test with absolute path to feature directory."""
    print_header("Test: Absolute Path")
    
    try:
        cleanup_design_files()
        
        # Create a test feature directory
        temp_dir = tempfile.mkdtemp()
        feature_dir = Path(temp_dir) / "999-test-absolute"
        feature_dir.mkdir()
        
        # Create spec.md
        (feature_dir / "spec.md").write_text("# Test Feature Spec\n")
        
        result = compare_outputs(
            "Absolute path to feature directory",
            [str(feature_dir)],
            None,
            check_json_equivalence=False
        )
        
        # Clean up
        shutil.rmtree(temp_dir)
        return result
    finally:
        cleanup_design_files()


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


def test_template_usage():
    """Test that template is used when available."""
    print_header("Test: Template Usage")
    
    try:
        cleanup_design_files()
        
        # Create template
        template_dir = REPO_ROOT / ".zo" / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = template_dir / "design-system-template.md"
        
        template_content = """# Design System
Feature: {{FEATURE}}
Last Updated: {{DATE}}
"""
        template_file.write_text(template_content)
        
        return compare_outputs(
            "Template usage in global mode",
            ["--global"],
            None,
            check_json_equivalence=False
        )
    finally:
        cleanup_design_files()


def test_json_fields():
    """Test that JSON output contains all required fields."""
    print_header("Test: JSON Fields")
    
    try:
        cleanup_design_files()
        
        bash_code, bash_stdout, _ = run_bash_script(["--global", "--json"])
        python_code, python_stdout, _ = run_python_script(["--global", "--json"])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        try:
            bash_json = json.loads(bash_stdout)
            python_json = json.loads(python_stdout)
            
            # Check required fields for global mode
            required_fields = ["MODE", "DESIGN_FILE", "FEATURE_SPEC", "FEATURE_DIR", "FEATURE_NAME"]
            
            for field in required_fields:
                if field not in bash_json or field not in python_json:
                    print_fail(f"Missing field: {field}")
                    return False
                
                if bash_json[field] != python_json[field]:
                    print_fail(f"{field} differs: bash={bash_json[field]}, python={python_json[field]}")
                    return False
            
            # Check MODE is 'global'
            if bash_json["MODE"] != "global" or python_json["MODE"] != "global":
                print_fail("MODE should be 'global'")
                return False
            
            print_success("JSON fields match and contain correct values")
            return True
        except json.JSONDecodeError as e:
            print_fail("JSON parse error: " + str(e))
            return False
    finally:
        cleanup_design_files()


def test_feature_mode_json_fields():
    """Test JSON fields for feature mode."""
    print_header("Test: Feature Mode JSON Fields")
    
    try:
        cleanup_design_files()
        
        # Create a test feature directory
        specs_dir = REPO_ROOT / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        feature_dir = specs_dir / "999-test-feature"
        feature_dir.mkdir(exist_ok=True)
        (feature_dir / "spec.md").write_text("# Test Feature\n")
        
        bash_code, bash_stdout, _ = run_bash_script(["--json", "specs/999-test-feature"])
        python_code, python_stdout, _ = run_python_script(["--json", "specs/999-test-feature"])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        try:
            bash_json = json.loads(bash_stdout)
            python_json = json.loads(python_stdout)
            
            # Check required fields for feature mode
            required_fields = ["MODE", "DESIGN_FILE", "FEATURE_SPEC", "FEATURE_DIR", "FEATURE_NAME"]
            
            for field in required_fields:
                if field not in bash_json or field not in python_json:
                    print_fail(f"Missing field: {field}")
                    return False
                
                if bash_json[field] != python_json[field]:
                    print_fail(f"{field} differs")
                    return False
            
            # Check MODE is 'feature'
            if bash_json["MODE"] != "feature" or python_json["MODE"] != "feature":
                print_fail("MODE should be 'feature'")
                return False
            
            print_success("Feature mode JSON fields match")
            return True
        except json.JSONDecodeError as e:
            print_fail("JSON parse error: " + str(e))
            return False
    finally:
        cleanup_design_files()
        if (specs_dir / "999-test-feature").exists():
            shutil.rmtree(specs_dir / "999-test-feature")


def run_all_tests():
    """Run all tests and return summary."""
    print("\n" + BOLD + "=" * 60 + RESET)
    print(BOLD + "SETUP-DESIGN TEST SUITE" + RESET)
    print(BOLD + "=" * 60 + RESET)
    print("\nRepo root: " + str(REPO_ROOT))
    print("Bash script: " + str(BASH_SCRIPT))
    print("Python script: " + str(PYTHON_SCRIPT))
    
    tests = [
        ("Help", test_help),
        ("Global Mode", test_global_mode),
        ("Global Mode (JSON)", test_global_mode_json),
        ("Feature Mode", test_feature_mode),
        ("Feature Mode (JSON)", test_feature_mode_json),
        ("Absolute Path", test_absolute_path),
        ("Non-existent Directory", test_nonexistent_directory),
        ("Template Usage", test_template_usage),
        ("JSON Fields", test_json_fields),
        ("Feature Mode JSON Fields", test_feature_mode_json_fields),
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
