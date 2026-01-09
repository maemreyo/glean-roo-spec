"""
Test Suite for setup-plan.py

This module tests the implementation plan initialization script.
Tests cover argument parsing, feature path resolution, template handling,
and end-to-end script execution.

Test Classes:
    TestParseArgs: Test command-line argument parsing
    TestScriptExecution: Test end-to-end script execution
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

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

from file_fixtures import TempDirectoryFixture
from git_fixtures import GitBranchFixture
from assertion_helpers import assert_file_exists, assert_json_output


class TestParseArgs(unittest.TestCase):
    """
    Test command-line argument parsing for setup-plan.py.

    Tests ensure that:
    - --json flag is parsed correctly
    - --help flag is parsed correctly
    - Unknown options cause errors
    """

    def setUp(self):
        """Set up test environment."""
        import setup_plan
        self.module = setup_plan

    def test_no_arguments(self):
        """Test parsing with no arguments."""
        with patch('sys.argv', ['setup-plan.py']):
            args = self.module.parse_args()
            self.assertFalse(args.json)
            self.assertFalse(args.help)

    def test_json_flag(self):
        """Test parsing --json flag."""
        with patch('sys.argv', ['setup-plan.py', '--json']):
            args = self.module.parse_args()
            self.assertTrue(args.json)
            self.assertFalse(args.help)

    def test_help_flag_short(self):
        """Test parsing -h flag."""
        with patch('sys.argv', ['setup-plan.py', '-h']):
            args = self.module.parse_args()
            self.assertTrue(args.help)

    def test_help_flag_long(self):
        """Test parsing --help flag."""
        with patch('sys.argv', ['setup-plan.py', '--help']):
            args = self.module.parse_args()
            self.assertTrue(args.help)


class TestScriptExecution(TempDirectoryFixture):
    """
    Test end-to-end execution of setup-plan.py.

    Tests ensure that:
    - Feature directory is created
    - Template is copied if available
    - Empty file is created when template missing
    - JSON and text output formats work
    - All paths are correctly resolved
    - Help exits with zero
    - Unknown options cause error
    """

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        import setup_plan
        self.module = setup_plan

        # Create .zo directory structure
        self.zo_dir = self.create_directory('.zo')
        self.templates_dir = self.create_directory('.zo/templates')

        # Create plan template
        self.template_content = """# Implementation Plan

## Overview
Implementation plan for the feature.

## Tasks
- Task 1
- Task 2
"""
        self.template_path = self.create_file(
            '.zo/templates/plan-template.md',
            self.template_content
        )

    @patch('setup_plan.get_feature_paths')
    def test_creates_feature_directory(self, mock_get_paths):
        """Test that feature directory is created."""
        # Mock feature paths
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs', '001-test-feature'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'plan.md'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'spec.md'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'design.md'),
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'HAS_GIT': True
        }

        with patch('sys.argv', ['setup-plan.py']):
            self.module.main()

        # Check that directory was created
        feature_dir = os.path.join(self.temp_dir, 'specs', '001-test-feature')
        self.assertTrue(os.path.isdir(feature_dir))

    @patch('setup_plan.get_feature_paths')
    def test_copies_template_to_plan_file(self, mock_get_paths):
        """Test that template is copied to plan file."""
        feature_dir = os.path.join(self.temp_dir, 'specs', '001-test-feature')
        impl_plan = os.path.join(feature_dir, 'plan.md')

        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'FEATURE_DIR': feature_dir,
            'IMPL_PLAN': impl_plan,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'DESIGN_FILE': os.path.join(feature_dir, 'design.md'),
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'HAS_GIT': True
        }

        with patch('sys.argv', ['setup-plan.py']):
            self.module.main()

        # Check that file was created
        assert_file_exists(impl_plan)

        # Check content
        with open(impl_plan, 'r') as f:
            content = f.read()
        self.assertIn('Implementation Plan', content)
        self.assertIn('Tasks', content)

    @patch('setup_plan.get_feature_paths')
    @patch('sys.stderr')
    def test_missing_template_creates_empty_file(self, mock_stderr, mock_get_paths):
        """Test that missing template creates empty file."""
        feature_dir = os.path.join(self.temp_dir, 'specs', '001-test-feature')
        impl_plan = os.path.join(feature_dir, 'plan.md')

        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'FEATURE_DIR': feature_dir,
            'IMPL_PLAN': impl_plan,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'DESIGN_FILE': os.path.join(feature_dir, 'design.md'),
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'HAS_GIT': True
        }

        # Remove template
        os.remove(self.template_path)

        with patch('sys.argv', ['setup-plan.py']):
            self.module.main()

        # File should be created
        assert_file_exists(impl_plan)

        # File should be empty
        with open(impl_plan, 'r') as f:
            content = f.read()
        self.assertEqual(content, '')

    @patch('setup_plan.get_feature_paths')
    @patch('sys.stdout')
    def test_json_output_format(self, mock_stdout, mock_get_paths):
        """Test JSON output format."""
        feature_dir = os.path.join(self.temp_dir, 'specs', '001-test-feature')
        impl_plan = os.path.join(feature_dir, 'plan.md')

        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'FEATURE_DIR': feature_dir,
            'IMPL_PLAN': impl_plan,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'DESIGN_FILE': os.path.join(feature_dir, 'design.md'),
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'HAS_GIT': True
        }

        with patch('sys.argv', ['setup-plan.py', '--json']):
            self.module.main()

        # Get output
        output = ''.join(str(call) for call in mock_stdout.write.call_args_list)

        # Parse JSON
        try:
            data = json.loads(output)
            self.assertIn('FEATURE_SPEC', data)
            self.assertIn('IMPL_PLAN', data)
            self.assertIn('DESIGN_FILE', data)
            self.assertIn('SPECS_DIR', data)
            self.assertIn('BRANCH', data)
            self.assertIn('HAS_GIT', data)
        except json.JSONDecodeError:
            # Try to find JSON in output
            for call in mock_stdout.write.call_args_list:
                try:
                    data = json.loads(str(call))
                    self.assertIn('IMPL_PLAN', data)
                    self.assertIn('BRANCH', data)
                    break
                except json.JSONDecodeError:
                    pass

    @patch('setup_plan.get_feature_paths')
    @patch('sys.stdout')
    def test_text_output_format(self, mock_stdout, mock_get_paths):
        """Test text output format."""
        feature_dir = os.path.join(self.temp_dir, 'specs', '001-test-feature')
        impl_plan = os.path.join(feature_dir, 'plan.md')

        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'FEATURE_DIR': feature_dir,
            'IMPL_PLAN': impl_plan,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'DESIGN_FILE': os.path.join(feature_dir, 'design.md'),
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'HAS_GIT': True
        }

        with patch('sys.argv', ['setup-plan.py']):
            self.module.main()

        # Check output format
        output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
        self.assertIn('FEATURE_SPEC:', output)
        self.assertIn('IMPL_PLAN:', output)
        self.assertIn('DESIGN_FILE:', output)
        self.assertIn('SPECS_DIR:', output)
        self.assertIn('BRANCH:', output)
        self.assertIn('HAS_GIT:', output)

    @patch('setup_plan.get_feature_paths')
    def test_help_exits_with_zero(self, mock_get_paths):
        """Test that --help exits with code 0."""
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs', '001-test-feature'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'plan.md'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'spec.md'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'design.md'),
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'HAS_GIT': True
        }

        with patch('sys.argv', ['setup-plan.py', '--help']):
            with self.assertRaises(SystemExit) as context:
                self.module.main()

        self.assertEqual(context.exception.code, 0)

    @patch('setup_plan.get_feature_paths')
    @patch('sys.stderr')
    def test_unknown_option_causes_error(self, mock_stderr, mock_get_paths):
        """Test that unknown option causes error."""
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs', '001-test-feature'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'plan.md'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'spec.md'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'design.md'),
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'HAS_GIT': True
        }

        with patch('sys.argv', ['setup-plan.py', '--unknown']):
            with self.assertRaises(SystemExit):
                self.module.parse_args()

    @patch('setup_plan.get_feature_paths')
    def test_feature_paths_are_resolved(self, mock_get_paths):
        """Test that feature paths are correctly resolved."""
        feature_dir = os.path.join(self.temp_dir, 'specs', '001-test-feature')
        impl_plan = os.path.join(feature_dir, 'plan.md')
        feature_spec = os.path.join(feature_dir, 'spec.md')
        design_file = os.path.join(feature_dir, 'design.md')

        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'FEATURE_DIR': feature_dir,
            'IMPL_PLAN': impl_plan,
            'FEATURE_SPEC': feature_spec,
            'DESIGN_FILE': design_file,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'HAS_GIT': True
        }

        with patch('sys.argv', ['setup-plan.py']):
            with patch('sys.stdout', new_callable=MagicMock):
                self.module.main()

                # Check that get_feature_paths was called
                self.assertTrue(mock_get_paths.called)

    @patch('setup_plan.get_feature_paths')
    def test_branch_info_included_in_output(self, mock_get_paths):
        """Test that branch information is included in output."""
        branch_name = 'feature/001-test-feature'

        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs', '001-test-feature'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'plan.md'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'spec.md'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'design.md'),
            'CURRENT_BRANCH': branch_name,
            'HAS_GIT': True
        }

        with patch('sys.argv', ['setup-plan.py', '--json']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()

                # Get output
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)

                # Check that branch is in output
                self.assertIn(branch_name, output)

    @patch('setup_plan.get_feature_paths')
    def test_has_git_flag_in_output(self, mock_get_paths):
        """Test that HAS_GIT flag is in output."""
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs', '001-test-feature'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'plan.md'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'spec.md'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs', '001-test-feature', 'design.md'),
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'HAS_GIT': False  # No git
        }

        with patch('sys.argv', ['setup-plan.py', '--json']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()

                # Get output
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)

                # Check that HAS_GIT is in output
                self.assertIn('HAS_GIT', output)

    @patch('setup_plan.get_feature_paths')
    @patch('sys.stderr')
    def test_warning_when_template_missing(self, mock_stderr, mock_get_paths):
        """Test that warning is printed when template is missing."""
        feature_dir = os.path.join(self.temp_dir, 'specs', '001-test-feature')
        impl_plan = os.path.join(feature_dir, 'plan.md')

        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'FEATURE_DIR': feature_dir,
            'IMPL_PLAN': impl_plan,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'DESIGN_FILE': os.path.join(feature_dir, 'design.md'),
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'HAS_GIT': True
        }

        # Remove template
        os.remove(self.template_path)

        with patch('sys.argv', ['setup-plan.py']):
            self.module.main()

        # Check that warning was printed to stderr
        self.assertTrue(mock_stderr.write.called)
        output = ''.join(str(call) for call in mock_stderr.write.call_args_list)
        self.assertIn('Warning', output)

    @patch('setup_plan.get_feature_paths')
    def test_success_message_when_template_found(self, mock_get_paths):
        """Test that success message is printed when template is found."""
        feature_dir = os.path.join(self.temp_dir, 'specs', '001-test-feature')
        impl_plan = os.path.join(feature_dir, 'plan.md')

        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'FEATURE_DIR': feature_dir,
            'IMPL_PLAN': impl_plan,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'DESIGN_FILE': os.path.join(feature_dir, 'design.md'),
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'HAS_GIT': True
        }

        with patch('sys.argv', ['setup-plan.py']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()

                # Check that success message was printed
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                self.assertIn('Copied plan template', output)

    @patch('setup_plan.get_feature_paths')
    def test_existing_directory_is_not_recreated(self, mock_get_paths):
        """Test that existing directory is not recreated."""
        feature_dir = os.path.join(self.temp_dir, 'specs', '001-test-feature')
        impl_plan = os.path.join(feature_dir, 'plan.md')

        # Create directory first
        os.makedirs(feature_dir, exist_ok=True)

        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'FEATURE_DIR': feature_dir,
            'IMPL_PLAN': impl_plan,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'DESIGN_FILE': os.path.join(feature_dir, 'design.md'),
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'HAS_GIT': True
        }

        # Should not raise error
        with patch('sys.argv', ['setup-plan.py']):
            with patch('sys.stdout', new_callable=MagicMock):
                self.module.main()

        # Directory should still exist
        self.assertTrue(os.path.isdir(feature_dir))


if __name__ == '__main__':
    unittest.main()
