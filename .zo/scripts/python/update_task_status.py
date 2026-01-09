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

# Configure logging with debug mode support
if os.environ.get('DEBUG') or os.environ.get('ZO_DEBUG'):
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
logger = logging.getLogger(__name__)


def get_workspace_path() -> str:
    """Get the workspace root path from environment or current directory."""
    pwd = os.environ.get('PWD', '')
    workspace = os.environ.get('WORKSPACE', os.environ.get('HOME', ''))
    
    if pwd and os.path.exists(pwd):
        return os.path.abspath(pwd)
    
    return os.path.abspath(os.getcwd())


def normalize_task_id(task_id: str) -> str:
    """
    Normalize task ID to standard format TXXX.
    
    Handles common variations:
    - [T001] -> T001
    - task_T001 -> T001
    - T001 -> T001
    
    Args:
        task_id: Raw task ID input
    
    Returns:
        Normalized task ID in format T001
    """
    original = task_id
    
    # Remove brackets if present: [T001] -> T001
    task_id = task_id.strip()
    if task_id.startswith('[') and task_id.endswith(']'):
        task_id = task_id[1:-1]
    
    # Remove 'task_' prefix if present: task_T001 -> T001
    if task_id.lower().startswith('task_'):
        task_id = task_id[5:]
    
    # Ensure uppercase T prefix
    if not task_id.startswith('T') and re.match(r'^\d{3}$', task_id):
        task_id = 'T' + task_id
    
    if original != task_id:
        logger.debug(f"Normalized task ID: '{original}' -> '{task_id}'")
    
    return task_id


def strip_duplicate_workspace_prefix(task_file: str, workspace: str) -> str:
    """
    Strip duplicate workspace prefix from path.
    
    Handles cases like:
    /Users/xxx/Documents/zaob-dev/glean-v2/Users/xxx/Documents/zaob-dev/glean-v2/specs/...
    
    Args:
        task_file: The input file path
        workspace: The workspace root path
    
    Returns:
        Path with duplicate prefix stripped if detected
    """
    # Check for doubled workspace path (e.g., /path/to/workspace/path/to/workspace/...)
    doubled_pattern = workspace + workspace
    if task_file.startswith(doubled_pattern):
        corrected = task_file[len(workspace):]
        logger.warning(f"Detected doubled workspace path, corrected: {task_file[:50]}... -> {corrected[:50]}...")
        return corrected
    
    # Check if path starts with workspace + '/Users/xxx/...' pattern
    if task_file.startswith(workspace):
        after_workspace = task_file[len(workspace):].lstrip('/')
        
        if after_workspace.startswith('Users/') or after_workspace.startswith('User/'):
            second_occurrence = task_file.find(after_workspace)
            if second_occurrence > len(workspace):
                corrected = '/' + after_workspace
                logger.warning(f"Detected duplicate workspace segment, corrected: {task_file[:50]}... -> {corrected}")
                return corrected
    
    return task_file


def resolve_path(task_file: str) -> str:
    """
    Resolve task file path, handling common AI mistakes.
    
    This function handles:
    1. Double workspace path (AI mistakenly prepends workspace twice)
    2. Non-existent paths from wrong CWD (tries common locations)
    3. Relative paths from different directories
    
    Args:
        task_file: The input file path (possibly incorrect)
    
    Returns:
        Resolved absolute path to the file, or original if not found
    """
    workspace = get_workspace_path()
    original_path = task_file
    
    # Case A: Strip duplicate workspace prefix
    task_file = strip_duplicate_workspace_prefix(task_file, workspace)
    
    # Case B: Try multiple locations if file doesn't exist
    if not os.path.exists(task_file):
        possible_paths = []
        
        # Original path (just in case)
        possible_paths.append(task_file)
        
        # Try relative to workspace
        ws_relative = os.path.join(workspace, task_file)
        possible_paths.append(ws_relative)
        
        # Try with 'specs/' prefix if not already present
        basename = os.path.basename(task_file)
        possible_paths.append(os.path.join(workspace, 'specs', basename))
        
        # Try with 'specs/' prefix for full path
        if not task_file.startswith('specs/'):
            possible_paths.append(os.path.join(workspace, 'specs', task_file))
        
        # Try parent directories (for when AI assumes wrong CWD)
        parts = task_file.split(os.sep)
        if len(parts) > 1:
            possible_paths.append(os.path.join(workspace, parts[-1]))
        
        # Try current working directory
        cwd = os.getcwd()
        if cwd != workspace:
            possible_paths.append(os.path.join(cwd, task_file))
            possible_paths.append(os.path.join(cwd, 'specs', os.path.basename(task_file)))
        
        # Find the first existing path
        for path in possible_paths:
            if os.path.exists(path):
                abs_path = os.path.abspath(path)
                if abs_path != original_path:
                    logger.warning(f"Path not found at '{original_path}', resolved to: {abs_path}")
                return abs_path
        
        # If file exists after normalization, use it
        if os.path.exists(task_file):
            return os.path.abspath(task_file)
    
    # Return absolute path if file exists
    if os.path.exists(task_file):
        return os.path.abspath(task_file)
    
    # Return original if nothing works (will fail at file check later)
    logger.warning(f"Could not resolve path, using original: {task_file}")
    return task_file


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
    resolved_path = resolve_path(args.tasks_file)
    
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
