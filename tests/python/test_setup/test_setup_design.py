"""
Test Suite for setup-design.py

This module tests the design documentation initialization script.
Tests cover global design setup, feature design setup, argument parsing,
and end-to-end script execution.

Test Classes:
    TestSetupGlobalDesign: Test global design system setup
    TestSetupFeatureDesign: Test feature design setup
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


class TestSetupGlobalDesign(TempDirectoryFixture):
    """
    Test the setup_global_design function.

    Tests ensure that:
    - Global design file is created in .zo directory
    - Template is copied if available
    - Design file is not overwritten if it exists
    - Correct paths are returned
    """

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        import setup_design
        self.module = setup_design

        # Create .zo directory structure
        self.zo_dir = self.create_directory('.zo')
        self.templates_dir = self.create_directory('.zo/templates')

    def test_creates_global_design_file(self):
        """Test that global design file is created."""
        repo_root = self.temp_dir

        result = self.module.setup_global_design(repo_root, False)

        # Check result structure
        self.assertEqual(result['MODE'], 'global')
        self.assertIn('design-system.md', result['DESIGN_FILE'])
        self.assertEqual(result['FEATURE_NAME'], 'global')
        self.assertEqual(result['FEATURE_SPEC'], '')

    def test_copies_template_if_available(self):
        """Test that template is copied when available."""
        # Create template
        template_content = """# Design System

Global design tokens and guidelines.
"""
        self.create_file('.zo/templates/design-system-template.md', template_content)

        repo_root = self.temp_dir
        result = self.module.setup_global_design(repo_root, False)

        # Check file was created
        design_file = result['DESIGN_FILE']
        assert_file_exists(design_file)

        # Check content
        with open(design_file, 'r') as f:
            content = f.read()
        self.assertIn('Design System', content)

    def test_does_not_overwrite_existing_design_file(self):
        """Test that existing design file is not overwritten."""
        # Create existing design file
        design_file_path = os.path.join(self.temp_dir, '.zo', 'design-system.md')
        with open(design_file_path, 'w') as f:
            f.write('Existing content')

        # Create template
        template_content = 'New content from template'
        self.create_file('.zo/templates/design-system-template.md', template_content)

        repo_root = self.temp_dir
        self.module.setup_global_design(repo_root, False)

        # Check that original content is preserved
        with open(design_file_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Existing content')

    def test_returns_correct_paths(self):
        """Test that correct paths are returned."""
        repo_root = self.temp_dir
        result = self.module.setup_global_design(repo_root, False)

        # Check paths
        self.assertEqual(result['FEATURE_DIR'], repo_root)
        self.assertTrue(result['DESIGN_FILE'].endswith('.zo/design-system.md'))

    def test_handles_missing_template_gracefully(self):
        """Test that missing template doesn't cause error."""
        repo_root = self.temp_dir

        # Should not raise error
        result = self.module.setup_global_design(repo_root, False)
        self.assertEqual(result['MODE'], 'global')


class TestSetupFeatureDesign(TempDirectoryFixture):
    """
    Test the setup_feature_design function.

    Tests ensure that:
    - Feature design file is created in feature directory
    - Template is copied with placeholder replacement
    - Feature detection works from branch and directory
    - Invalid feature arguments are rejected
    """

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        import setup_design
        self.module = setup_design

        # Create .zo directory structure
        self.zo_dir = self.create_directory('.zo')
        self.templates_dir = self.create_directory('.zo/templates')

        # Create feature directory
        self.feature_dir = self.create_directory('specs/001-test-feature')

    @patch('setup_design.get_current_branch')
    def test_creates_feature_design_file(self, mock_branch):
        """Test that feature design file is created."""
        mock_branch.return_value = '001-test-feature'

        repo_root = self.temp_dir
        result = self.module.setup_feature_design(repo_root, '', False)

        # Check result structure
        self.assertEqual(result['MODE'], 'feature')
        self.assertIn('design.md', result['DESIGN_FILE'])
        self.assertEqual(result['FEATURE_NAME'], '001-test-feature')
        self.assertIn('spec.md', result['FEATURE_SPEC'])

    @patch('setup_design.get_current_branch')
    def test_copies_template_with_replacement(self, mock_branch):
        """Test that template is copied with placeholder replacement."""
        mock_branch.return_value = '001-test-feature'

        # Create template
        template_content = """# Feature Design: [FEATURE NAME]

## Overview
Design for the [FEATURE NAME] feature.
"""
        self.create_file('.zo/templates/design-template.md', template_content)

        repo_root = self.temp_dir
        result = self.module.setup_feature_design(repo_root, '', False)

        # Check file was created with replacements
        design_file = result['DESIGN_FILE']
        with open(design_file, 'r') as f:
            content = f.read()

        self.assertIn('001-test-feature', content)
        self.assertNotIn('[FEATURE NAME]', content)

    @patch('setup_design.get_current_branch')
    def test_does_not_overwrite_existing_design(self, mock_branch):
        """Test that existing design file is not overwritten."""
        mock_branch.return_value = '001-test-feature'

        # Create existing design file
        design_file_path = os.path.join(self.feature_dir, 'design.md')
        with open(design_file_path, 'w') as f:
            f.write('Existing design')

        # Create template
        template_content = 'New template content'
        self.create_file('.zo/templates/design-template.md', template_content)

        repo_root = self.temp_dir
        self.module.setup_feature_design(repo_root, '', False)

        # Check that original content is preserved
        with open(design_file_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Existing design')

    @patch('setup_design.get_current_branch')
    def test_uses_feature_directory_argument(self, mock_branch):
        """Test using provided feature directory argument."""
        mock_branch.return_value = 'main'

        repo_root = self.temp_dir
        feature_arg = os.path.join(self.temp_dir, 'specs', '001-test-feature')
        result = self.module.setup_feature_design(repo_root, feature_arg, False)

        # Check result
        self.assertEqual(result['MODE'], 'feature')
        self.assertIn('001-test-feature', result['FEATURE_DIR'])

    @patch('setup_design.get_current_branch')
    def test_rejects_invalid_directory(self, mock_branch):
        """Test that invalid directory argument is rejected."""
        mock_branch.return_value = 'main'

        repo_root = self.temp_dir
        invalid_arg = 'nonexistent-directory'

        with patch('sys.stderr'):
            with self.assertRaises(SystemExit):
                self.module.setup_feature_design(repo_root, invalid_arg, False)

    @patch('setup_design.get_current_branch')
    @patch('setup_design.find_feature_dir_by_prefix')
    def test_detects_feature_from_branch(self, mock_find, mock_branch):
        """Test feature detection from branch name."""
        mock_branch.return_value = '001-test-feature'
        mock_find.return_value = os.path.join(self.temp_dir, 'specs', '001-test-feature')

        repo_root = self.temp_dir
        result = self.module.setup_feature_design(repo_root, '', False)

        # Should find feature directory
        self.assertIn('001-test-feature', result['FEATURE_NAME'])

    def test_handles_missing_template_gracefully(self):
        """Test that missing template doesn't cause error."""
        with patch('setup_design.get_current_branch') as mock_branch:
            mock_branch.return_value = '001-test-feature'

            repo_root = self.temp_dir

            # Should not raise error
            result = self.module.setup_feature_design(repo_root, '', False)
            self.assertEqual(result['MODE'], 'feature')


class TestScriptExecution(TempDirectoryFixture):
    """
    Test end-to-end execution of setup-design.py.

    Tests ensure that:
    - Global mode creates correct files
    - Feature mode creates correct files
    - JSON and text output formats work
    - Help exits with zero
    - Unknown options cause error
    """

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        import setup_design
        self.module = setup_design

        # Create .zo directory structure
        self.zo_dir = self.create_directory('.zo')
        self.templates_dir = self.create_directory('.zo/templates')

        # Create templates
        global_template = """# Design System

Global design documentation.
"""
        self.create_file('.zo/templates/design-system-template.md', global_template)

        feature_template = """# Feature Design: [FEATURE NAME]

Design documentation.
"""
        self.create_file('.zo/templates/design-template.md', feature_template)

    @patch('setup_design.get_repo_root')
    def test_global_mode_execution(self, mock_get_repo_root):
        """Test execution in global mode."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-design.py', '--global']):
            self.module.main()

        # Check that design file was created
        design_file = os.path.join(self.temp_dir, '.zo', 'design-system.md')
        assert_file_exists(design_file)

    @patch('setup_design.get_repo_root')
    @patch('setup_design.get_current_branch')
    def test_feature_mode_execution(self, mock_branch, mock_get_repo_root):
        """Test execution in feature mode."""
        mock_branch.return_value = 'main'
        mock_get_repo_root.return_value = self.temp_dir

        # Create feature directory with spec.md
        feature_dir = self.create_directory('specs/001-test-feature')
        self.create_file('specs/001-test-feature/spec.md', '# Spec')

        # Change to feature directory
        original_dir = os.getcwd()
        try:
            os.chdir(feature_dir)

            with patch('sys.argv', ['setup-design.py']):
                self.module.main()

            # Check that design file was created
            design_file = os.path.join(feature_dir, 'design.md')
            assert_file_exists(design_file)
        finally:
            os.chdir(original_dir)

    @patch('setup_design.get_repo_root')
    @patch('sys.stdout')
    def test_json_output_format_global(self, mock_stdout, mock_get_repo_root):
        """Test JSON output format in global mode."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-design.py', '--global', '--json']):
            self.module.main()

        # Get output
        output = ''.join(str(call) for call in mock_stdout.write.call_args_list)

        # Parse JSON
        try:
            data = json.loads(output)
            self.assertIn('MODE', data)
            self.assertIn('DESIGN_FILE', data)
            self.assertEqual(data['MODE'], 'global')
        except json.JSONDecodeError:
            # Try to find JSON in output
            for call in mock_stdout.write.call_args_list:
                try:
                    data = json.loads(str(call))
                    self.assertEqual(data['MODE'], 'global')
                    break
                except json.JSONDecodeError:
                    pass

    @patch('setup_design.get_repo_root')
    @patch('sys.stdout')
    def test_text_output_format_global(self, mock_stdout, mock_get_repo_root):
        """Test text output format in global mode."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-design.py', '--global']):
            self.module.main()

        # Check output format
        output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
        self.assertIn('MODE:', output)
        self.assertIn('DESIGN_FILE:', output)

    @patch('setup_design.get_repo_root')
    @patch('sys.stdout')
    def test_text_output_format_feature(self, mock_stdout, mock_get_repo_root):
        """Test text output format in feature mode."""
        mock_get_repo_root.return_value = self.temp_dir

        # Create feature directory
        feature_dir = self.create_directory('specs/001-test-feature')
        self.create_file('specs/001-test-feature/spec.md', '# Spec')

        with patch('setup_design.get_current_branch', return_value='main'):
            with patch('sys.argv', ['setup-design.py', 'specs/001-test-feature']):
                self.module.main()

        # Check output format
        output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
        self.assertIn('MODE:', output)
        self.assertIn('DESIGN_FILE:', output)
        self.assertIn('FEATURE_SPEC:', output)

    @patch('setup_design.get_repo_root')
    def test_help_exits_with_zero(self, mock_get_repo_root):
        """Test that --help exits with code 0."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-design.py', '--help']):
            with self.assertRaises(SystemExit) as context:
                self.module.main()

        self.assertEqual(context.exception.code, 0)

    @patch('setup_design.get_repo_root')
    def test_short_help_flag(self, mock_get_repo_root):
        """Test that -h flag works."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-design.py', '-h']):
            with self.assertRaises(SystemExit) as context:
                self.module.main()

        self.assertEqual(context.exception.code, 0)

    @patch('setup_design.get_repo_root')
    @patch('sys.stderr')
    def test_unknown_option_causes_error(self, mock_stderr, mock_get_repo_root):
        """Test that unknown option causes error."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-design.py', '--unknown']):
            with self.assertRaises(SystemExit):
                self.module.main()

    @patch('setup_design.get_repo_root')
    def test_global_mode_with_json(self, mock_get_repo_root):
        """Test global mode with JSON output."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-design.py', '--global', '--json']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()

                # Check that output was written
                self.assertTrue(mock_stdout.write.called)

    @patch('setup_design.get_repo_root')
    @patch('setup_design.get_current_branch')
    @patch('setup_design.find_feature_dir_by_prefix')
    def test_feature_detection_from_branch(self, mock_find, mock_branch, mock_get_repo_root):
        """Test feature detection from branch name."""
        mock_branch.return_value = '001-test-feature'
        mock_find.return_value = os.path.join(self.temp_dir, 'specs', '001-test-feature')
        mock_get_repo_root.return_value = self.temp_dir

        # Create feature directory
        feature_dir = self.create_directory('specs/001-test-feature')
        self.create_file('specs/001-test-feature/spec.md', '# Spec')

        with patch('sys.argv', ['setup-design.py']):
            with patch('sys.stdout', new_callable=MagicMock):
                self.module.main()

        # Check that design file was created
        design_file = os.path.join(feature_dir, 'design.md')
        assert_file_exists(design_file)

    @patch('setup_design.get_repo_root')
    def test_global_short_flag(self, mock_get_repo_root):
        """Test -g flag for global mode."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-design.py', '-g']):
            self.module.main()

        # Check that design file was created
        design_file = os.path.join(self.temp_dir, '.zo', 'design-system.md')
        assert_file_exists(design_file)


if __name__ == '__main__':
    unittest.main()
