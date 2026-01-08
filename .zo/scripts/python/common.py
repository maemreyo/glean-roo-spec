#!/usr/bin/env python3
"""
Common utility functions for Spec-Driven Development workflow.

This module provides shared utility functions that can be used by other
Python scripts in the .zo/scripts/python directory. It ports functionality
from .zo/scripts/bash/common.sh for use in Python-based scripts.

Usage:
    # Import functions
    from common import get_repo_root, get_current_branch, has_git
    
    # Get feature paths for bash sourcing
    import subprocess
    result = subprocess.run(['python', 'common.py'], capture_output=True, text=True)
    # Then eval the output in bash: eval $(python common.py)

Functions:
    has_git() - Check if git is available
    get_repo_root() - Get repository root path
    get_current_branch() - Get current git branch
    get_feature_paths() - Get all feature-related paths (eval-style output)
    check_feature_branch() - Validate feature branch naming
    check_file() - Check if file exists and print status
    check_dir() - Check if directory exists and print status
    check_file_exists() - Check if file exists (return bool)
    check_dir_exists() - Check if directory exists (return bool)
    check_dir_exists_with_files() - Check if directory has files (return bool)
    find_feature_dir_by_prefix() - Find feature directory by numeric prefix
    get_feature_dir() - Get feature directory path
"""

import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Git Utility Functions
# ============================================================================

def run_git_command(args: list) -> Optional[str]:
    """
    Run a git command and return output, or None if git not available.
    
    Args:
        args: List of git command arguments
        
    Returns:
        Command output as string, or None if command fails
    """
    try:
        result = subprocess.run(
            ['git'] + args,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def has_git() -> bool:
    """
    Check if git is available and this is a git repository.
    
    Returns:
        True if git is available, False otherwise
    """
    return run_git_command(['rev-parse', '--show-toplevel']) is not None


# ============================================================================
# Repository and Branch Functions
# ============================================================================

def get_repo_root() -> str:
    """
    Get repository root, with fallback for non-git repositories.
    
    Returns:
        Path to repository root directory
    """
    # Try git first
    git_root = run_git_command(['rev-parse', '--show-toplevel'])
    if git_root:
        return git_root
    
    # Fall back to script location for non-git repos
    script_dir = Path(__file__).parent.resolve()
    # Go up 3 levels: python -> scripts -> .zo -> project
    repo_root = script_dir.parent.parent.parent
    return str(repo_root.resolve())


def get_current_branch() -> str:
    """
    Get current branch, with fallback for non-git repositories.
    
    Returns:
        Current branch name or feature directory name
    """
    # First check if SPECIFY_FEATURE environment variable is set
    specify_feature = os.environ.get('SPECIFY_FEATURE', '')
    if specify_feature:
        logger.debug(f"Using SPECIFY_FEATURE env var: {specify_feature}")
        return specify_feature
    
    # Then check git if available
    git_branch = run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
    if git_branch:
        logger.debug(f"Using git branch: {git_branch}")
        return git_branch
    
    # For non-git repos, try to find the latest feature directory
    repo_root = get_repo_root()
    specs_dir = Path(repo_root) / 'specs'
    
    if not specs_dir.exists():
        logger.debug("No specs directory found, using 'main' as fallback")
        return 'main'
    
    latest_feature = None
    highest = 0
    
    try:
        for entry in specs_dir.iterdir():
            if entry.is_dir():
                dirname = entry.name
                match = re.match(r'^(\d{3})-(.+)$', dirname)
                if match:
                    number = int(match.group(1))
                    if number > highest:
                        highest = number
                        latest_feature = dirname
    except OSError as e:
        logger.warning(f"Error reading specs directory: {e}")
    
    if latest_feature:
        logger.debug(f"Found latest feature directory: {latest_feature}")
        return latest_feature
    
    logger.debug("No feature directories found, using 'main' as fallback")
    return 'main'


def get_feature_dir(repo_root: str, branch_name: str) -> str:
    """
    Get the feature directory path for a given branch.
    
    Args:
        repo_root: Repository root path
        branch_name: Current branch name
        
    Returns:
        Path to feature directory
    """
    return find_feature_dir_by_prefix(repo_root, branch_name)


def find_feature_dir_by_prefix(repo_root: str, branch_name: str) -> str:
    """
    Find feature directory by numeric prefix instead of exact branch match.
    This allows multiple branches to work on the same spec.
    
    Args:
        repo_root: Repository root path
        branch_name: Current branch name
        
    Returns:
        Path to feature directory
    """
    specs_dir = Path(repo_root) / 'specs'
    
    # Extract numeric prefix from branch (e.g., "004" from "004-whatever")
    match = re.match(r'^(\d{3})-(.+)$', branch_name)
    if not match:
        # If branch doesn't have numeric prefix, fall back to exact match
        logger.debug(f"Branch '{branch_name}' doesn't match prefix pattern, using exact match")
        return str(specs_dir / branch_name)
    
    prefix = match.group(1)
    
    # Search for directories in specs/ that start with this prefix
    matches = []
    if specs_dir.exists():
        try:
            for entry in specs_dir.iterdir():
                if entry.is_dir() and entry.name.startswith(f'{prefix}-'):
                    matches.append(entry.name)
        except OSError as e:
            logger.warning(f"Error searching specs directory: {e}")
    
    # Handle results
    if len(matches) == 0:
        # No match found - return the branch name path (will fail later with clear error)
        logger.debug(f"No matching directories found for prefix '{prefix}'")
        return str(specs_dir / branch_name)
    elif len(matches) == 1:
        # Exactly one match - perfect!
        logger.debug(f"Found single matching directory: {matches[0]}")
        return str(specs_dir / matches[0])
    else:
        # Multiple matches - this shouldn't happen with proper naming convention
        error_msg = (
            f"Multiple spec directories found with prefix '{prefix}': {', '.join(matches)}\n"
            f"Please ensure only one spec directory exists per numeric prefix."
        )
        logger.error(error_msg)
        return str(specs_dir / branch_name)


# ============================================================================
# Feature Paths Functions
# ============================================================================

def get_feature_paths() -> dict:
    """
    Get all feature-related paths as a dictionary.
    
    Returns:
        Dictionary containing all path variables
    """
    repo_root = get_repo_root()
    current_branch = get_current_branch()
    has_git_repo = has_git()
    
    # Use prefix-based lookup to support multiple branches per spec
    feature_dir = find_feature_dir_by_prefix(repo_root, current_branch)
    
    return {
        'REPO_ROOT': repo_root,
        'CURRENT_BRANCH': current_branch,
        'HAS_GIT': 'true' if has_git_repo else 'false',
        'FEATURE_DIR': feature_dir,
        'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
        'IMPL_PLAN': os.path.join(feature_dir, 'plan.md'),
        'TASKS': os.path.join(feature_dir, 'tasks.md'),
        'RESEARCH': os.path.join(feature_dir, 'research.md'),
        'DATA_MODEL': os.path.join(feature_dir, 'data-model.md'),
        'QUICKSTART': os.path.join(feature_dir, 'quickstart.md'),
        'CONTRACTS_DIR': os.path.join(feature_dir, 'contracts'),
        'DESIGN_FILE': os.path.join(feature_dir, 'design.md'),
        'GLOBAL_DESIGN_SYSTEM': os.path.join(repo_root, '.zo', 'design-system.md'),
    }


def format_feature_paths_for_eval() -> str:
    """
    Format feature paths as bash eval-compatible output.
    
    Returns:
        String with bash variable assignments (eval style)
    """
    paths = get_feature_paths()
    
    lines = [
        f"REPO_ROOT='{paths['REPO_ROOT']}'",
        f"CURRENT_BRANCH='{paths['CURRENT_BRANCH']}'",
        f"HAS_GIT='{paths['HAS_GIT']}'",
        f"FEATURE_DIR='{paths['FEATURE_DIR']}'",
        f"FEATURE_SPEC='{paths['FEATURE_SPEC']}'",
        f"IMPL_PLAN='{paths['IMPL_PLAN']}'",
        f"TASKS='{paths['TASKS']}'",
        f"RESEARCH='{paths['RESEARCH']}'",
        f"DATA_MODEL='{paths['DATA_MODEL']}'",
        f"QUICKSTART='{paths['QUICKSTART']}'",
        f"CONTRACTS_DIR='{paths['CONTRACTS_DIR']}'",
        f"DESIGN_FILE='{paths['DESIGN_FILE']}'",
    ]
    
    return '\n'.join(lines)


# ============================================================================
# Feature Branch Validation Functions
# ============================================================================

def check_feature_branch(branch: str, has_git_repo: bool) -> Tuple[bool, Optional[str]]:
    """
    Check if the current branch is a valid feature branch.
    
    Args:
        branch: Current branch name
        has_git_repo: Whether git repository is available
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # For non-git repos, we can't enforce branch naming but still provide output
    if not has_git_repo:
        return (True, None)
    
    # Check if branch matches feature branch pattern (e.g., 001-feature-name)
    if not re.match(r'^\d{3}-', branch):
        error_msg = (
            f"ERROR: Not on a feature branch. Current branch: {branch}\n"
            f"Feature branches should be named like: 001-feature-name"
        )
        return (False, error_msg)
    
    return (True, None)


# ============================================================================
# File and Directory Check Functions
# ============================================================================

def check_file_exists(file_path: str) -> bool:
    """
    Check if a file exists.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file exists, False otherwise
    """
    return os.path.isfile(file_path)


def check_dir_exists(dir_path: str) -> bool:
    """
    Check if a directory exists.
    
    Args:
        dir_path: Path to directory
        
    Returns:
        True if directory exists, False otherwise
    """
    return os.path.isdir(dir_path)


def check_dir_exists_with_files(dir_path: str) -> bool:
    """
    Check if a directory exists and contains files.
    
    Args:
        dir_path: Path to directory
        
    Returns:
        True if directory exists and has files, False otherwise
    """
    if not os.path.isdir(dir_path):
        return False
    try:
        # Check if directory has any files/subdirectories
        return any(os.scandir(dir_path))
    except OSError:
        return False


def check_file(file_path: str, display_name: str) -> str:
    """
    Check if file exists and return formatted status string.
    
    Args:
        file_path: Path to file
        display_name: Name to display
        
    Returns:
        Formatted status string with checkmark or cross
    """
    if check_file_exists(file_path):
        return f"  ✓ {display_name}"
    else:
        return f"  ✗ {display_name}"


def check_dir(dir_path: str, display_name: str) -> str:
    """
    Check if directory exists with files and return formatted status string.
    
    Args:
        dir_path: Path to directory
        display_name: Name to display
        
    Returns:
        Formatted status string with checkmark or cross
    """
    if check_dir_exists_with_files(dir_path):
        return f"  ✓ {display_name}"
    else:
        return f"  ✗ {display_name}"


# ============================================================================
# Main Entry Point (for bash sourcing)
# ============================================================================

def main():
    """Main entry point for bash sourcing mode."""
    print(format_feature_paths_for_eval())


if __name__ == '__main__':
    main()
