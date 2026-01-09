"""
Test Suite for setup-brainstorm.py

This module tests the brainstorm session initialization script.
Tests cover filename generation, argument parsing, template handling,
and end-to-end script execution.

Test Classes:
    TestSlugify: Test the slugify function for filename generation
    TestParseArgs: Test command-line argument parsing
    TestScriptExecution: Test end-to-end script execution
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts directory to path for imports
script_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.zo', 'scripts', 'python')
sys.path.insert(0, script_dir)

# Import fixtures and helpers
fixtures_dir = os.path.join(os.path.dirname(__file__), '..', 'fixtures')
helpers_dir = os.path.join(os.path.dirname(__file__), '..', 'helpers')
if fixtures_dir not in sys.path:
    sys.path.insert(0, fixtures_dir)
if helpers_dir not in sys.path:
    sys.path.insert(0, helpers_dir)

from file_fixtures import TempDirectoryFixture, TemplateFixture
from assertion_helpers import assert_file_exists, assert_json_output
from output_helpers import run_python_script, parse_json_output


class TestSlugify(unittest.TestCase):
    """
    Test the slugify function for generating safe filenames.

    Tests ensure that:
    - Text is converted to lowercase
    - Non-alphanumeric characters are replaced with hyphens
    - Leading and trailing hyphens are removed
    - Multiple consecutive hyphens are NOT collapsed (matches bash behavior)
    """

    def setUp(self):
        """Set up test environment."""
        # Import the module to test using importlib due to hyphen in filename
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "setup_brainstorm",
            os.path.join(script_dir, "setup-brainstorm.py")
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_simple_text_lowercase(self):
        """Test that simple text is converted to lowercase."""
        result = self.module.slugify('Hello World')
        self.assertEqual(result, 'hello-world')

    def test_special_characters_become_hyphens(self):
        """Test that special characters become individual hyphens."""
        result = self.module.slugify('test@example.com')
        # Each non-alphanumeric char becomes a hyphen
        self.assertEqual(result, 'test-example-com')

    def test_multiple_special_chars_no_collapse(self):
        """Test that multiple consecutive special chars each become hyphens."""
        # Bash behavior: sed 's/[^a-z0-9]/-/g' replaces EACH char with '-'
        # macOS sed doesn't collapse them
        result = self.module.slugify('test!!!file')
        self.assertEqual(result, 'test---file')

    def test_leading_trailing_hyphens_removed(self):
        """Test that leading and trailing hyphens are removed."""
        result = self.module.slugify('---test---')
        self.assertEqual(result, 'test')

    def test_numbers_preserved(self):
        """Test that numbers are preserved in the slug."""
        result = self.module.slugify('Feature 123 Test')
        self.assertEqual(result, 'feature-123-test')

    def test_spaces_and_punctuation(self):
        """Test handling of spaces and punctuation."""
        result = self.module.slugify('What is this?')
        # Space, 'i', 's', space become hyphens, '?' becomes hyphen
        self.assertEqual(result, 'what-is-this-')

    def test_empty_string(self):
        """Test that empty string returns empty result."""
        result = self.module.slugify('')
        self.assertEqual(result, '')

    def test_only_special_chars(self):
        """Test string with only special characters."""
        result = self.module.slugify('!!!')
        self.assertEqual(result, '')

    def test_mixed_case(self):
        """Test that mixed case is converted to lowercase."""
        result = self.module.slugify('HeLLo WoRLd')
        self.assertEqual(result, 'hello-world')

    def test_underscores_and_hyphens(self):
        """Test that underscores and hyphens are replaced."""
        result = self.module.slugify('test_file-name')
        self.assertEqual(result, 'test-file-name')


class TestParseArgs(unittest.TestCase):
    """
    Test command-line argument parsing for setup-brainstorm.py.

    Tests ensure that:
    - --json flag is parsed correctly
    - --help flag is parsed correctly
    - Positional topic argument is captured
    - Unknown arguments are appended to topic (bash compatibility)
    """

    def setUp(self):
        """Set up test environment."""
        import setup_brainstorm
        self.module = setup_brainstorm

    def test_no_arguments(self):
        """Test parsing with no arguments."""
        with patch('sys.argv', ['setup-brainstorm.py']):
            args = self.module.parse_args()
            self.assertFalse(args.json)
            self.assertFalse(args.help)
            self.assertEqual(args.topic, '')

    def test_json_flag(self):
        """Test parsing --json flag."""
        with patch('sys.argv', ['setup-brainstorm.py', '--json']):
            args = self.module.parse_args()
            self.assertTrue(args.json)
            self.assertFalse(args.help)

    def test_help_flag_short(self):
        """Test parsing -h flag."""
        with patch('sys.argv', ['setup-brainstorm.py', '-h']):
            args = self.module.parse_args()
            self.assertTrue(args.help)
            self.assertFalse(args.json)

    def test_help_flag_long(self):
        """Test parsing --help flag."""
        with patch('sys.argv', ['setup-brainstorm.py', '--help']):
            args = self.module.parse_args()
            self.assertTrue(args.help)

    def test_topic_argument(self):
        """Test parsing topic argument."""
        with patch('sys.argv', ['setup-brainstorm.py', 'improve login flow']):
            args = self.module.parse_args()
            self.assertEqual(args.topic, 'improve login flow')

    def test_json_and_topic(self):
        """Test parsing --json with topic."""
        with patch('sys.argv', ['setup-brainstorm.py', '--json', 'add dark mode']):
            args = self.module.parse_args()
            self.assertTrue(args.json)
            self.assertEqual(args.topic, 'add dark mode')

    def test_unknown_args_appended_to_topic(self):
        """Test that unknown arguments are appended to topic."""
        with patch('sys.argv', ['setup-brainstorm.py', '--json', 'my', 'topic', 'here']):
            args = self.module.parse_args()
            self.assertTrue(args.json)
            # Unknown args should be appended to topic
            self.assertIn('my', args.topic)
            self.assertIn('topic', args.topic)
            self.assertIn('here', args.topic)


class TestScriptExecution(TempDirectoryFixture):
    """
    Test end-to-end execution of setup-brainstorm.py.

    Tests ensure that:
    - Brainstorm directory is created
    - Files are created with correct naming
    - Templates are copied with placeholder replacement
    - JSON and text output formats work
    - Missing templates are handled gracefully
    """

    def setUp(self):
        """Set up test environment with temporary directory."""
        super().setUp()
        # Import the module
        import setup_brainstorm
        self.module = setup_brainstorm

        # Create .zo directory structure
        self.zo_dir = self.create_directory('.zo')
        self.templates_dir = self.create_directory('.zo/templates')
        self.brainstorms_dir = self.create_directory('.zo/brainstorms')

        # Create a sample brainstorm template
        self.template_content = """# Brainstorm Session: {{FEATURE}}

Date: {{DATE}}

## Topic
{{FEATURE}}

## Notes
- Start brainstorming here...
"""
        self.template_path = self.create_file(
            '.zo/templates/brainstorm-template.md',
            self.template_content
        )

    @patch('setup_brainstorm.get_repo_root')
    def test_creates_brainstorm_with_custom_topic(self, mock_get_repo_root):
        """Test creating a brainstorm file with custom topic."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm.py', 'improve login flow']):
            self.module.main()

        # Check that file was created
        files = os.listdir(self.brainstorms_dir)
        self.assertEqual(len(files), 1)

        # Check filename format
        filename = files[0]
        self.assertTrue(filename.startswith('improve-login-flow-'))
        self.assertTrue(filename.endswith('.md'))

    @patch('setup_brainstorm.get_repo_root')
    def test_creates_brainstorm_without_topic(self, mock_get_repo_root):
        """Test creating a brainstorm file without topic uses default."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm.py']):
            self.module.main()

        # Check that file was created with default name
        files = os.listdir(self.brainstorms_dir)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].startswith('brainstorm-session-'))

    @patch('setup_brainstorm.get_repo_root')
    def test_template_placeholders_replaced(self, mock_get_repo_root):
        """Test that template placeholders are replaced correctly."""
        mock_get_repo_root.return_value = self.temp_dir

        topic = 'add dark mode'
        with patch('sys.argv', ['setup-brainstorm.py', topic]):
            self.module.main()

        # Get the created file
        files = os.listdir(self.brainstorms_dir)
        filepath = os.path.join(self.brainstorms_dir, files[0])

        # Read content
        with open(filepath, 'r') as f:
            content = f.read()

        # Check placeholders were replaced
        self.assertNotIn('{{FEATURE}}', content)
        self.assertNotIn('{{DATE}}', content)
        self.assertIn('add-dark-mode', content)

    @patch('setup_brainstorm.get_repo_root')
    @patch('sys.stdout')
    def test_json_output_format(self, mock_stdout, mock_get_repo_root):
        """Test JSON output format."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm.py', '--json', 'test topic']):
            self.module.main()

        # Get the output
        output = mock_stdout.write.call_args_list
        output_text = ''.join(str(call) for call in output)

        # Should contain valid JSON
        try:
            data = json.loads(output_text)
            self.assertIn('OUTPUT_FILE', data)
            self.assertIn('BRAINSTORM_DIR', data)
            self.assertIn('TOPIC', data)
        except json.JSONDecodeError:
            # Output might be in multiple calls, try to find JSON
            for call in output:
                try:
                    data = json.loads(str(call))
                    self.assertIn('OUTPUT_FILE', data)
                    break
                except json.JSONDecodeError:
                    pass
            else:
                raise

    @patch('setup_brainstorm.get_repo_root')
    def test_text_output_format(self, mock_get_repo_root):
        """Test text output format (default)."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm.py', 'test']):
            # Capture stdout
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()

                # Check that output was written
                self.assertTrue(mock_stdout.write.called)
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                self.assertIn('OUTPUT_FILE:', output)

    @patch('setup_brainstorm.get_repo_root')
    def test_missing_template_creates_empty_file(self, mock_get_repo_root):
        """Test that missing template creates empty file."""
        mock_get_repo_root.return_value = self.temp_dir

        # Remove the template
        os.remove(self.template_path)

        with patch('sys.argv', ['setup-brainstorm.py', 'test']):
            self.module.main()

        # Check that file was created
        files = os.listdir(self.brainstorms_dir)
        self.assertEqual(len(files), 1)

        # File should exist but be empty
        filepath = os.path.join(self.brainstorms_dir, files[0])
        with open(filepath, 'r') as f:
            content = f.read()
        self.assertEqual(content, '')

    @patch('setup_brainstorm.get_repo_root')
    def test_help_exits_with_zero(self, mock_get_repo_root):
        """Test that --help exits with code 0."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm.py', '--help']):
            with self.assertRaises(SystemExit) as context:
                self.module.main()

        self.assertEqual(context.exception.code, 0)

    @patch('setup_brainstorm.get_repo_root')
    def test_directory_creation(self, mock_get_repo_root):
        """Test that brainstorm directory is created if it doesn't exist."""
        # Remove the brainstorms directory
        import shutil
        shutil.rmtree(self.brainstorms_dir)

        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm.py', 'test']):
            self.module.main()

        # Directory should be created
        brainstorms_path = os.path.join(self.temp_dir, '.zo', 'brainstorms')
        self.assertTrue(os.path.isdir(brainstorms_path))

    @patch('setup_brainstorm.get_repo_root')
    def test_multiple_runs_create_unique_files(self, mock_get_repo_root):
        """Test that multiple runs create files with unique timestamps."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm.py', 'test']):
            self.module.main()

        with patch('sys.argv', ['setup-brainstorm.py', 'test']):
            self.module.main()

        # Should have two different files
        files = os.listdir(self.brainstorms_dir)
        self.assertEqual(len(files), 2)

        # Filenames should be different (different timestamps)
        self.assertNotEqual(files[0], files[1])

    @patch('setup_brainstorm.get_repo_root')
    def test_topic_with_special_characters(self, mock_get_repo_root):
        """Test topic with special characters is slugified correctly."""
        mock_get_repo_root.return_value = self.temp_dir

        topic = 'What about this feature?'
        with patch('sys.argv', ['setup-brainstorm.py', topic]):
            self.module.main()

        # Check filename
        files = os.listdir(self.brainstorms_dir)
        filename = files[0]
        # Special chars should be converted to hyphens
        self.assertIn('what-about-this-feature', filename)

    @patch('setup_brainstorm.get_repo_root')
    def test_topic_with_numbers(self, mock_get_repo_root):
        """Test topic with numbers preserves them in slug."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm.py', 'Version 2.0 features']):
            self.module.main()

        # Check filename
        files = os.listdir(self.brainstorms_dir)
        filename = files[0]
        self.assertIn('2-0', filename)


if __name__ == '__main__':
    unittest.main()
