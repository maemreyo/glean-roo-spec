#!/usr/bin/env python3
"""
Update task status in tasks.md files.

This script marks a task as completed by changing `- [ ]` to `- [x]` 
for the specified task ID in a markdown tasks file.

Usage:
    python3 update_task_status.py <tasks_file> <task_id>
    python3 update_task_status.py /path/to/tasks.md T001

Examples:
    python3 update_task_status.py specs/001-feature/tasks.md T001
    python3 update_task_status.py tasks.md T005 --verbose
    python3 update_task_status.py tasks.md [T001] --verbose  # Bracket format
    python3 update_task_status.py tasks.md task_T001 --verbose  # task_ prefix

Options:
    --dry-run    Show what would be changed without modifying file
    --verbose    Show detailed output
    --help, -h   Show this help message
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

# Import shared utilities from common module
from common import (
    get_workspace_path,
    validate_execution_environment,
    normalize_task_id,
    strip_duplicate_workspace_prefix,
    resolve_path as common_resolve_path
)

# Configure logging with debug mode support
if os.environ.get('DEBUG') or os.environ.get('ZO_DEBUG'):
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Update task status in tasks.md files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 update_task_status.py tasks.md T001
  python3 update_task_status.py specs/001-feature/tasks.md T005 --dry-run
  python3 update_task_status.py tasks.md T012 --verbose
  python3 update_task_status.py tasks.md [T001] --verbose  # bracket format
  python3 update_task_status.py tasks.md task_T001 --verbose  # task_ prefix
        '''
    )
    parser.add_argument(
        'tasks_file',
        help='Path to the tasks.md file'
    )
    parser.add_argument(
        'task_id',
        help='Task ID to mark as completed (e.g., T001, [T001], task_T001)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    return parser.parse_args()


def validate_task_id(task_id: str) -> bool:
    """Validate task ID format (e.g., T001, T123)."""
    pattern = r'^T\d{3}$'
    return bool(re.match(pattern, task_id))


def find_task_line(content: str, task_id: str) -> Optional[int]:
    """
    Find the line number of a task by its ID.
    
    Args:
        content: File content as string
        task_id: Task ID to find (e.g., 'T001')
    
    Returns:
        Line number if found, None otherwise
    """
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Match task pattern: - [ ] T001 or - [x] T001
        # Also handles: - [ ] [T001] for bracket-wrapped IDs
        task_pattern = rf'- \[([ xX])\] ?\[?{re.escape(task_id)}\]?'
        if re.search(task_pattern, line):
            return i
    return None


def update_task_status(content: str, task_id: str) -> Tuple[str, bool]:
    """
    Update task status from incomplete to complete.
    
    Args:
        content: File content as string
        task_id: Task ID to mark as completed
    
    Returns:
        Tuple of (updated_content, was_modified)
    """
    lines = content.split('\n')
    modified = False
    
    task_pattern = rf'^(- \[)([ xX])(\] ?\[?{re.escape(task_id)}\]?.*)$'
    
    for i, line in enumerate(lines):
        match = re.match(task_pattern, line)
        if match:
            # Check if task is already completed
            if match.group(2).lower() == 'x':
                logger.debug(f"Task {task_id} already completed")
                return content, False
            
            # Update from - [ ] to - [x]
            new_line = f"{match.group(1)}x{match.group(3)}"
            lines[i] = new_line
            modified = True
            logger.debug(f"Updated line {i+1}: {line} -> {new_line}")
    
    return '\n'.join(lines), modified


def update_task_status_bracket(content: str, task_id: str) -> Tuple[str, bool]:
    """
    Update task status for bracket-wrapped task IDs (e.g., [T001]).
    
    Args:
        content: File content as string
        task_id: Task ID to mark as completed
    
    Returns:
        Tuple of (updated_content, was_modified)
    """
    lines = content.split('\n')
    modified = False
    
    # Match: - [ ] [T001] or - [x] [T001]
    task_pattern = rf'^(- \[)([ xX])(\] ?\[{re.escape(task_id)}\].*)$'
    
    for i, line in enumerate(lines):
        match = re.match(task_pattern, line)
        if match:
            # Check if task is already completed
            if match.group(2).lower() == 'x':
                logger.debug(f"Task {task_id} already completed")
                return content, False
            
            # Update from - [ ] to - [x]
            new_line = f"{match.group(1)}x{match.group(3)}"
            lines[i] = new_line
            modified = True
            logger.debug(f"Updated line {i+1}: {line} -> {new_line}")
    
    return '\n'.join(lines), modified


def main():
    """Main entry point."""
    # Validate execution environment first
    if not validate_execution_environment():
        logger.error("Execution environment validation failed. Please check the workspace path.")
        sys.exit(1)
    
    args = parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Normalize task ID (handle [T001], task_T001, etc.)
    normalized_task_id = normalize_task_id(args.task_id)
    
    # Validate task ID format
    if not validate_task_id(normalized_task_id):
        logger.error(f"Invalid task ID format: {normalized_task_id}")
        logger.error("Task ID must match pattern T001, T002, etc.")
        sys.exit(1)
    
    # Resolve path (handle common AI path mistakes)
    resolved_path = common_resolve_path(args.tasks_file)
    
    # Check if tasks file exists
    if not os.path.isfile(resolved_path):
        logger.error(f"Tasks file not found: {args.tasks_file}")
        logger.error(f"Resolved path: {resolved_path}")
        sys.exit(1)
    
    # Read file content
    try:
        with open(resolved_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except IOError as e:
        logger.error(f"Failed to read tasks file: {e}")
        sys.exit(1)
    
    # Find the task line
    line_num = find_task_line(content, normalized_task_id)
    if line_num is None:
        logger.error(f"Task {normalized_task_id} not found in {resolved_path}")
        sys.exit(1)
    
    # Get the task line for display
    lines = content.split('\n')
    task_line = lines[line_num]
    logger.debug(f"Found task at line {line_num + 1}: {task_line.strip()}")
    
    # Update task status
    updated_content, modified = update_task_status(content, normalized_task_id)
    
    # Try bracket-wrapped format if not found
    if not modified:
        updated_content, modified = update_task_status_bracket(content, normalized_task_id)
    
    # Report results
    if not modified:
        logger.info(f"Task {normalized_task_id} already marked as completed")
        sys.exit(0)
    
    if args.dry_run:
        logger.info(f"[DRY RUN] Would mark task {normalized_task_id} as completed")
        logger.debug(f"Line {line_num + 1}: {task_line}")
        # Show what would change
        new_lines = updated_content.split('\n')
        logger.debug(f"Would change to: {new_lines[line_num]}")
    else:
        # Write updated content
        try:
            with open(resolved_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            logger.info(f"✓ Task {normalized_task_id} marked as completed")
        except IOError as e:
            logger.error(f"Failed to write tasks file: {e}")
            sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
