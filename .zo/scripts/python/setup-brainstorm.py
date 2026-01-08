#!/usr/bin/env python3
"""
setup-brainstorm.py
Initialize a brainstorm session in .zo/brainstorms/ directory.

Usage:
    ./setup-brainstorm.py [--json] [brainstorm topic]

Options:
    --json    Output results in JSON format
    --help    Show this help message

Examples:
    ./setup-brainstorm.py "improve login flow"
    ./setup-brainstorm.py --json "add dark mode"

Output:
    JSON object with:
    - OUTPUT_FILE: Path to the brainstorm file created
    - BRAINSTORM_DIR: Path to the brainstorms directory
    - TOPIC: The topic slug used for the file
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import common module
script_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(script_dir))

from common import get_repo_root


def slugify(text: str) -> str:
    """
    Convert text to a slug-safe filename.
    
    Args:
        text: Text to slugify
        
    Returns:
        Slugified string
    """
    # Convert to lowercase
    text = text.lower()
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r'[^a-z0-9]', '-', text)
    # Remove duplicate hyphens
    text = re.sub(r'-+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Initialize a brainstorm session in .zo/brainstorms/ directory',
        add_help=False  # We'll handle --help manually
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    
    parser.add_argument(
        '--help',
        '-h',
        action='store_true',
        help='Show this help message'
    )
    
    parser.add_argument(
        'topic',
        nargs='?',
        default='',
        help='Brainstorm topic (optional)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Handle help
    if args.help:
        print(__doc__)
        sys.exit(0)
    
    # Get repository root
    repo_root = get_repo_root()
    
    # Determine output directory
    brainstorm_dir = os.path.join(repo_root, '.zo', 'brainstorms')
    os.makedirs(brainstorm_dir, exist_ok=True)
    
    # Generate filename
    date_str = datetime.now().strftime('%Y-%m-%d-%H%M')
    topic_input = args.topic
    
    if topic_input:
        # Slugify the input topic
        topic_slug = slugify(topic_input)
        # Create filename with date for uniqueness
        filename = f"{topic_slug}-{date_str}.md"
        name_tag = topic_slug
    else:
        # Fallback if no topic provided
        filename = f"brainstorm-session-{date_str}.md"
        name_tag = "General Session"
    
    output_file = os.path.join(brainstorm_dir, filename)
    
    # Use template if available
    template_path = os.path.join(repo_root, '.zo', 'templates', 'brainstorm-template.md')
    
    if os.path.isfile(template_path):
        # Read template
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Replace placeholders
        content = content.replace('{{DATE}}', date_str)
        content = content.replace('{{FEATURE}}', name_tag)
        
        # Write output file
        with open(output_file, 'w') as f:
            f.write(content)
    else:
        # Fallback to empty file if template missing
        Path(output_file).touch()
    
    # Output results
    if args.json:
        result = {
            'OUTPUT_FILE': output_file,
            'BRAINSTORM_DIR': brainstorm_dir,
            'TOPIC': name_tag
        }
        print(json.dumps(result))
    else:
        print(f"OUTPUT_FILE: {output_file}")


if __name__ == '__main__':
    main()
