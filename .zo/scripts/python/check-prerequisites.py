#!/usr/bin/env python3
"""
Consolidated prerequisite checking script for Spec-Driven Development workflow.

This script provides unified prerequisite checking for Spec-Driven Development workflow.
It replaces the functionality previously spread across multiple bash scripts.

Usage: python check-prerequisites.py [OPTIONS]

OPTIONS:
  --json              Output in JSON format
  --require-tasks     Require tasks.md to exist (for implementation phase)
  --include-tasks     Include tasks.md in AVAILABLE_DOCS list
  --paths-only        Only output path variables (no validation)
  --help, -h          Show help message

OUTPUTS:
  JSON mode: {"FEATURE_DIR":"...", "AVAILABLE_DOCS":["..."]}
  Text mode: FEATURE_DIR:... \n AVAILABLE_DOCS: \n ✓/✗ file.md
  Paths only: REPO_ROOT: ... \n BRANCH: ... \n FEATURE_DIR: ... \n GLOBAL_DESIGN_SYSTEM: ...
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Utility Functions (ported from common.sh)
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


def has_git() -> bool:
    """
    Check if git is available and this is a git repository.
    
    Returns:
        True if git is available, False otherwise
    """
    return run_git_command(['rev-parse', '--show-toplevel']) is not None


def check_feature_branch(branch: str, has_git_repo: bool) -> tuple[bool, Optional[str]]:
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
            f"Not on a feature branch. Current branch: {branch}\n"
            f"Feature branches should be named like: 001-feature-name"
        )
        return (False, error_msg)
    
    return (True, None)


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
        'GLOBAL_DESIGN_SYSTEM': os.path.join(repo_root, '.zo/design-system.md'),
    }


def check_file_exists(file_path: str) -> bool:
    """
    Check if a file exists.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file exists, False otherwise
    """
    return os.path.isfile(file_path)


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


# ============================================================================
# Output Functions
# ============================================================================

def format_json_paths(paths: dict) -> str:
    """
    Format paths as JSON for paths-only mode.
    
    Args:
        paths: Dictionary of path variables
        
    Returns:
        JSON formatted string
    """
    return json.dumps({
        'REPO_ROOT': paths['REPO_ROOT'],
        'BRANCH': paths['CURRENT_BRANCH'],
        'FEATURE_DIR': paths['FEATURE_DIR'],
        'FEATURE_SPEC': paths['FEATURE_SPEC'],
        'IMPL_PLAN': paths['IMPL_PLAN'],
        'TASKS': paths['TASKS'],
        'GLOBAL_DESIGN_SYSTEM': paths['GLOBAL_DESIGN_SYSTEM'],
    }, indent=2)


def format_json_result(feature_dir: str, available_docs: list) -> str:
    """
    Format result as JSON.
    
    Args:
        feature_dir: Feature directory path
        available_docs: List of available document names
        
    Returns:
        JSON formatted string
    """
    result = {
        'FEATURE_DIR': feature_dir,
        'AVAILABLE_DOCS': available_docs,
    }
    return json.dumps(result, indent=2)


def check_file_status(file_path: str, display_name: str) -> str:
    """
    Check file status and return formatted string.
    
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


def check_dir_status(dir_path: str, display_name: str) -> str:
    """
    Check directory status and return formatted string.
    
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


def print_help():
    """Print help message."""
    help_text = """Usage: check-prerequisites.py [OPTIONS]

Consolidated prerequisite checking for Spec-Driven Development workflow.

OPTIONS:
  --json              Output in JSON format
  --require-tasks     Require tasks.md to exist (for implementation phase)
  --include-tasks     Include tasks.md in AVAILABLE_DOCS list
  --paths-only        Only output path variables (no prerequisite validation)
  --help, -h          Show this help message

EXAMPLES:
  # Check task prerequisites (plan.md required)
  python check-prerequisites.py --json
  
  # Check implementation prerequisites (plan.md + tasks.md required)
  python check-prerequisites.py --json --require-tasks --include-tasks
  
  # Get feature paths only (no validation)
  python check-prerequisites.py --paths-only
"""
    print(help_text)


# ============================================================================
# Main Logic
# ============================================================================

def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--require-tasks', action='store_true', help='Require tasks.md to exist')
    parser.add_argument('--include-tasks', action='store_true', help='Include tasks.md in AVAILABLE_DOCS list')
    parser.add_argument('--paths-only', action='store_true', help='Only output path variables (no validation)')
    parser.add_argument('--help', '-h', action='store_true', help='Show help message')
    
    args = parser.parse_args()
    
    # Handle help flag
    if args.help:
        print_help()
        sys.exit(0)
    
    logger.debug("Starting prerequisite check")
    
    # Get feature paths and validate branch
    paths = get_feature_paths()
    logger.debug(f"Feature paths: {paths}")
    
    is_valid, error_msg = check_feature_branch(
        paths['CURRENT_BRANCH'], 
        paths['HAS_GIT'] == 'true'
    )
    
    if not is_valid:
        print(f"ERROR: {error_msg}", file=sys.stderr)
        sys.exit(1)
    
    # If paths-only mode, output paths and exit
    if args.paths_only:
        if args.json:
            print(format_json_paths(paths))
        else:
            print(f"REPO_ROOT: {paths['REPO_ROOT']}")
            print(f"BRANCH: {paths['CURRENT_BRANCH']}")
            print(f"FEATURE_DIR: {paths['FEATURE_DIR']}")
            print(f"FEATURE_SPEC: {paths['FEATURE_SPEC']}")
            print(f"IMPL_PLAN: {paths['IMPL_PLAN']}")
            print(f"TASKS: {paths['TASKS']}")
            print(f"GLOBAL_DESIGN_SYSTEM: {paths['GLOBAL_DESIGN_SYSTEM']}")
        sys.exit(0)
    
    # Validate required directories and files
    if not os.path.isdir(paths['FEATURE_DIR']):
        print(f"ERROR: Feature directory not found: {paths['FEATURE_DIR']}", file=sys.stderr)
        print("Run /zo.zo first to create the feature structure.", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isfile(paths['IMPL_PLAN']):
        print(f"ERROR: plan.md not found in {paths['FEATURE_DIR']}", file=sys.stderr)
        print("Run /zo.plan first to create the implementation plan.", file=sys.stderr)
        sys.exit(1)
    
    # Check for tasks.md if required
    if args.require_tasks and not os.path.isfile(paths['TASKS']):
        print(f"ERROR: tasks.md not found in {paths['FEATURE_DIR']}", file=sys.stderr)
        print("Run /zo.tasks first to create the task list.", file=sys.stderr)
        sys.exit(1)
    
    # Build list of available documents
    available_docs = []
    
    # Always check these optional docs
    if check_file_exists(paths['RESEARCH']):
        available_docs.append('research.md')
    if check_file_exists(paths['DATA_MODEL']):
        available_docs.append('data-model.md')
    if check_file_exists(paths['DESIGN_FILE']):
        available_docs.append('design.md')
    
    # Check contracts directory (only if it exists and has files)
    if check_dir_exists_with_files(paths['CONTRACTS_DIR']):
        available_docs.append('contracts/')
    
    if check_file_exists(paths['QUICKSTART']):
        available_docs.append('quickstart.md')
    
    # Include tasks.md if requested and it exists
    if args.include_tasks and check_file_exists(paths['TASKS']):
        available_docs.append('tasks.md')
    
    # Output results
    if args.json:
        print(format_json_result(paths['FEATURE_DIR'], available_docs))
    else:
        # Text output
        print(f"FEATURE_DIR:{paths['FEATURE_DIR']}")
        print("AVAILABLE_DOCS:")
        
        # Show status of each potential document
        print(check_file_status(paths['RESEARCH'], 'research.md'))
        print(check_file_status(paths['DATA_MODEL'], 'data-model.md'))
        print(check_file_status(paths['DESIGN_FILE'], 'design.md'))
        print(check_dir_status(paths['CONTRACTS_DIR'], 'contracts/'))
        print(check_file_status(paths['QUICKSTART'], 'quickstart.md'))
        
        if args.include_tasks:
            print(check_file_status(paths['TASKS'], 'tasks.md'))
    
    logger.debug("Prerequisite check completed successfully")
    sys.exit(0)


if __name__ == '__main__':
    main()
