#!/usr/bin/env python3
"""
Test script to verify that Python implementation matches bash implementation exactly.

This script compares the output of:
1. The original bash script: .zo/scripts/bash/update-agent-context.sh
2. The new Python script: .zo/scripts/python/update-agent-context.py

Usage: python update-agent-context.test.py
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
BASH_SCRIPT = SCRIPT_DIR.parent / "bash" / "update-agent-context.sh"
PYTHON_SCRIPT = SCRIPT_DIR / "update-agent-context.py"
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
            timeout=30,
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
            timeout=30,
            cwd=str(REPO_ROOT),
            env=run_env
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except FileNotFoundError:
        return -1, "", "Python script not found"


def compare_outputs(test_name, args, env=None):
    """
    Compare outputs of bash and Python scripts.
    
    Args:
        test_name: Name of the test
        args: Command line arguments
        env: Environment variables
        
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
    
    # Compare stderr (normalize whitespace)
    bash_stderr_normalized = bash_stderr.strip()
    python_stderr_normalized = python_stderr.strip()
    
    if bash_stderr_normalized != python_stderr_normalized:
        print_fail("Stderr differs:")
        print("  Bash stderr:")
        print(bash_stderr)
        print("  Python stderr:")
        print(python_stderr)
        return False
    print_success("Stderr matches")
    
    return True


def cleanup_test_files():
    """Clean up test agent files and feature directories."""
    # Clean up test agent files
    agent_files = [
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / ".roo" / "rules" / "specify-rules.md",
        REPO_ROOT / "GEMINI.md",
        REPO_ROOT / ".cursor" / "rules" / "specify-rules.mdc",
        REPO_ROOT / ".windsurf" / "rules" / "specify-rules.md",
    ]
    
    for agent_file in agent_files:
        if agent_file.exists():
            agent_file.unlink()
    
    # Clean up test feature directories
    specs_dir = REPO_ROOT / "specs"
    if specs_dir.exists():
        for feature_dir in specs_dir.glob("999-test-*"):
            if feature_dir.is_dir():
                shutil.rmtree(feature_dir)


def setup_test_feature():
    """Create a test feature directory with plan.md."""
    specs_dir = REPO_ROOT / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    
    feature_dir = specs_dir / "999-test-feature"
    feature_dir.mkdir(exist_ok=True)
    
    # Create plan.md with test data
    plan_content = """# Implementation Plan

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Pydantic
**Storage**: PostgreSQL
**Project Type**: Web Application

## Overview
Test implementation plan.
"""
    
    (feature_dir / "plan.md").write_text(plan_content)
    
    return feature_dir


def setup_test_template():
    """Create test template for agent files."""
    template_dir = REPO_ROOT / ".zo" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    
    template_file = template_dir / "agent-file-template.md"
    template_content = """# [PROJECT NAME] Agent Rules

**Last updated**: [DATE]

## Active Technologies
[EXTRACTED FROM ALL PLAN.MD FILES]

## Project Structure
[ACTUAL STRUCTURE FROM PLANS]

## Commands
[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]

## Code Style
[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]

## Recent Changes
[LAST 3 FEATURES AND WHAT THEY ADDED]
"""
    
    template_file.write_text(template_content)
    
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


def test_default_agent_creation():
    """Test default agent (Claude) file creation."""
    print_header("Test: Default Agent Creation")
    
    try:
        cleanup_test_files()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        bash_code, bash_stdout, bash_stderr = run_bash_script([])
        python_code, python_stdout, python_stderr = run_python_script([])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        # Check that CLAUDE.md was created
        claude_file = REPO_ROOT / "CLAUDE.md"
        if not claude_file.exists():
            print_fail("CLAUDE.md was not created")
            return False
        
        print_success("Default agent file created successfully")
        return True
    finally:
        cleanup_test_files()


def test_specific_agent_claude():
    """Test updating specific Claude agent."""
    print_header("Test: Specific Agent (Claude)")
    
    try:
        cleanup_test_files()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        return compare_outputs(
            "Update Claude agent",
            ["claude"],
            None
        )
    finally:
        cleanup_test_files()


def test_specific_agent_gemini():
    """Test updating specific Gemini agent."""
    print_header("Test: Specific Agent (Gemini)")
    
    try:
        cleanup_test_files()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        return compare_outputs(
            "Update Gemini agent",
            ["gemini"],
            None
        )
    finally:
        cleanup_test_files()


def test_specific_agent_cursor():
    """Test updating specific Cursor agent."""
    print_header("Test: Specific Agent (Cursor)")
    
    try:
        cleanup_test_files()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        return compare_outputs(
            "Update Cursor agent",
            ["cursor-agent"],
            None
        )
    finally:
        cleanup_test_files()


def test_specific_agent_windsurf():
    """Test updating specific Windsurf agent."""
    print_header("Test: Specific Agent (Windsurf)")
    
    try:
        cleanup_test_files()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        return compare_outputs(
            "Update Windsurf agent",
            ["windsurf"],
            None
        )
    finally:
        cleanup_test_files()


def test_specific_agent_roo():
    """Test updating specific Roo agent."""
    print_header("Test: Specific Agent (Roo)")
    
    try:
        cleanup_test_files()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        return compare_outputs(
            "Update Roo agent",
            ["roo"],
            None
        )
    finally:
        cleanup_test_files()


def test_plan_data_extraction():
    """Test that plan data is extracted correctly."""
    print_header("Test: Plan Data Extraction")
    
    try:
        cleanup_test_files()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        bash_code, bash_stdout, bash_stderr = run_bash_script([])
        python_code, python_stdout, python_stderr = run_python_script([])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        # Check that the agent file contains the extracted data
        claude_file = REPO_ROOT / "CLAUDE.md"
        if not claude_file.exists():
            print_fail("CLAUDE.md was not created")
            return False
        
        content = claude_file.read_text()
        
        # Check for language, framework, and database
        if "Python 3.11+" not in content:
            print_fail("Language not found in agent file")
            return False
        
        if "FastAPI" not in content:
            print_fail("Framework not found in agent file")
            return False
        
        if "PostgreSQL" not in content:
            print_fail("Database not found in agent file")
            return False
        
        print_success("Plan data extracted correctly")
        return True
    finally:
        cleanup_test_files()


def test_template_usage():
    """Test that template is used when creating new agent file."""
    print_header("Test: Template Usage")
    
    try:
        cleanup_test_files()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        bash_code, bash_stdout, bash_stderr = run_bash_script([])
        python_code, python_stdout, python_stderr = run_python_script([])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        # Check that the agent file was created from template
        claude_file = REPO_ROOT / "CLAUDE.md"
        if not claude_file.exists():
            print_fail("CLAUDE.md was not created")
            return False
        
        content = claude_file.read_text()
        
        # Check for template markers
        if "## Active Technologies" not in content:
            print_fail("Template structure not found")
            return False
        
        if "## Project Structure" not in content:
            print_fail("Template structure not found")
            return False
        
        print_success("Template used successfully")
        return True
    finally:
        cleanup_test_files()


def test_update_existing_agent():
    """Test updating an existing agent file."""
    print_header("Test: Update Existing Agent")
    
    try:
        cleanup_test_files()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        # Create an existing agent file
        claude_file = REPO_ROOT / "CLAUDE.md"
        existing_content = """# Existing Agent Rules

**Last updated**: 2026-01-01

## Active Technologies
- TypeScript 5.3+ (existing-feature)

## Recent Changes
- 2026-01-01: Added TypeScript 5.3+
"""
        
        claude_file.write_text(existing_content)
        
        bash_code, bash_stdout, bash_stderr = run_bash_script([])
        python_code, python_stdout, python_stderr = run_python_script([])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        # Check that the file was updated
        content = claude_file.read_text()
        
        # Should have both old and new technologies
        if "TypeScript 5.3+ (existing-feature)" not in content:
            print_fail("Existing technology was removed")
            return False
        
        if "Python 3.11+ (999-test-feature)" not in content:
            print_fail("New technology was not added")
            return False
        
        # Check that recent changes were updated
        if "999-test-feature" not in content:
            print_fail("Recent changes not updated")
            return False
        
        print_success("Existing agent file updated successfully")
        return True
    finally:
        cleanup_test_files()


def test_no_plan_file():
    """Test behavior when plan.md doesn't exist."""
    print_header("Test: No Plan File (Should Fail)")
    
    try:
        cleanup_test_files()
        
        # Create feature directory without plan.md
        specs_dir = REPO_ROOT / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        
        feature_dir = specs_dir / "999-test-feature"
        feature_dir.mkdir(exist_ok=True)
        
        bash_code, bash_stdout, bash_stderr = run_bash_script([])
        python_code, python_stdout, python_stderr = run_python_script([])
        
        if bash_code != python_code:
            print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
            return False
        
        if bash_code == 0:
            print_fail("Expected non-zero exit code when plan.md missing")
            return False
        
        print_success("No plan file handling matches")
        return True
    finally:
        cleanup_test_files()


def test_invalid_agent_type():
    """Test with invalid agent type (should error)."""
    print_header("Test: Invalid Agent Type (Should Fail)")
    
    try:
        cleanup_test_files()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        bash_code, bash_stdout, bash_stderr = run_bash_script(["invalid-agent"])
        python_code, python_stdout, python_stderr = run_python_script(["invalid-agent"])
        
        if bash_code != python_code:
            print_fail("Exit codes differ: bash=" + str(bash_code) + ", python=" + str(python_code))
            return False
        
        if bash_code == 0:
            print_fail("Expected non-zero exit code for invalid agent type")
            return False
        
        print_success("Invalid agent type handling matches")
        return True
    finally:
        cleanup_test_files()


def test_multiple_agent_types():
    """Test updating multiple agent types."""
    print_header("Test: Multiple Agent Types")
    
    try:
        cleanup_test_files()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        # Create existing agent files for multiple types
        claude_file = REPO_ROOT / "CLAUDE.md"
        claude_file.write_text("# Claude\n")
        
        gemini_dir = REPO_ROOT
        (gemini_dir / "GEMINI.md").write_text("# Gemini\n")
        
        # Run without specifying agent (should update all existing)
        bash_code, bash_stdout, bash_stderr = run_bash_script([])
        python_code, python_stdout, python_stderr = run_python_script([])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        # Check that both files were updated
        claude_content = claude_file.read_text()
        gemini_content = (gemini_dir / "GEMINI.md").read_text()
        
        if "999-test-feature" not in claude_content:
            print_fail("Claude agent not updated")
            return False
        
        if "999-test-feature" not in gemini_content:
            print_fail("Gemini agent not updated")
            return False
        
        print_success("Multiple agents updated successfully")
        return True
    finally:
        cleanup_test_files()


def test_technology_stack_formatting():
    """Test that technology stack is formatted correctly."""
    print_header("Test: Technology Stack Formatting")
    
    try:
        cleanup_test_files()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        bash_code, bash_stdout, bash_stderr = run_bash_script([])
        python_code, python_stdout, python_stderr = run_python_script([])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        claude_file = REPO_ROOT / "CLAUDE.md"
        content = claude_file.read_text()
        
        # Check for "language + framework" format
        if "Python 3.11+ + FastAPI" in content or "Python 3.11+, FastAPI" in content:
            print_success("Technology stack formatted correctly")
            return True
        else:
            print_fail("Technology stack not formatted correctly")
            print("Content: " + content[:500])
            return False
    finally:
        cleanup_test_files()


def test_directory_structure_detection():
    """Test that project structure is detected correctly."""
    print_header("Test: Directory Structure Detection")
    
    try:
        cleanup_test_files()
        feature_dir = setup_test_feature()
        setup_test_template()
        
        bash_code, bash_stdout, bash_stderr = run_bash_script([])
        python_code, python_stdout, python_stderr = run_python_script([])
        
        if bash_code != python_code:
            print_fail("Exit codes differ")
            return False
        
        claude_file = REPO_ROOT / "CLAUDE.md"
        content = claude_file.read_text()
        
        # Check for backend/frontend structure (web application)
        if "backend/" in content or "frontend/" in content:
            print_success("Project structure detected correctly")
            return True
        else:
            print_fail("Project structure not found")
            return False
    finally:
        cleanup_test_files()


def run_all_tests():
    """Run all tests and return summary."""
    print("\n" + BOLD + "=" * 60 + RESET)
    print(BOLD + "UPDATE-AGENT-CONTEXT TEST SUITE" + RESET)
    print(BOLD + "=" * 60 + RESET)
    print("\nRepo root: " + str(REPO_ROOT))
    print("Bash script: " + str(BASH_SCRIPT))
    print("Python script: " + str(PYTHON_SCRIPT))
    
    tests = [
        ("Help", test_help),
        ("Default Agent Creation", test_default_agent_creation),
        ("Specific Agent (Claude)", test_specific_agent_claude),
        ("Specific Agent (Gemini)", test_specific_agent_gemini),
        ("Specific Agent (Cursor)", test_specific_agent_cursor),
        ("Specific Agent (Windsurf)", test_specific_agent_windsurf),
        ("Specific Agent (Roo)", test_specific_agent_roo),
        ("Plan Data Extraction", test_plan_data_extraction),
        ("Template Usage", test_template_usage),
        ("Update Existing Agent", test_update_existing_agent),
        ("No Plan File", test_no_plan_file),
        ("Invalid Agent Type", test_invalid_agent_type),
        ("Multiple Agent Types", test_multiple_agent_types),
        ("Technology Stack Formatting", test_technology_stack_formatting),
        ("Directory Structure Detection", test_directory_structure_detection),
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
