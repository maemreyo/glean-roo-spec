"""
Test suite for create-new-feature.py script.

This module tests the create-new-feature.py script which creates
feature branches from user descriptions.

Test Classes:
    TestParseArguments: Tests command-line argument parsing
    TestDetermineBranchNumber: Tests branch number detection logic
    TestScriptExecution: Tests end-to-end script execution
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Add script directory to path
script_dir = Path(__file__).parent.parent.parent / '.zo' / 'scripts' / 'python'
sys.path.insert(0, str(script_dir))

from tests.python.fixtures.git_fixtures import GitBranchFixture
from tests.python.fixtures.file_fixtures import TempDirectoryFixture
from tests.python.helpers.assertion_helpers import (
    assert_file_exists,
    assert_directory_exists,
    assert_json_output,
    assert_file_contains
)
from tests.python.helpers.output_helpers import (
    run_python_script,
    parse_json_output,
    ProcessResult
)


class TestParseArguments(unittest.TestCase):
    """Test argument parsing for create-new-feature.py."""

    def setUp(self):
        """Set up test fixtures."""
        # Import the module to test
        with patch('sys.argv', ['create-new-feature.py']):
            from create_new_feature import parse_arguments
            self.parse_arguments = parse_arguments

    def test_parse_arguments_with_description_only(self):
        """Test parsing with only a feature description."""
        with patch('sys.argv', ['create-new-feature.py', 'Add user auth']):
            args = self.parse_arguments()
            self.assertEqual(args.feature_description, ['Add', 'user', 'auth'])
            self.assertFalse(args.json)
            self.assertEqual(args.short_name, '')
            self.assertEqual(args.number, '')

    def test_parse_arguments_with_json_flag(self):
        """Test parsing with --json flag."""
        with patch('sys.argv', ['create-new-feature.py', '--json', 'Test feature']):
            args = self.parse_arguments()
            self.assertTrue(args.json)
            self.assertEqual(args.feature_description, ['Test', 'feature'])

    def test_parse_arguments_with_short_name(self):
        """Test parsing with --short-name argument."""
        with patch('sys.argv', ['create-new-feature.py', '--short-name', 'user-auth', 'description']):
            args = self.parse_arguments()
            self.assertEqual(args.short_name, 'user-auth')

    def test_parse_arguments_with_number(self):
        """Test parsing with --number argument."""
        with patch('sys.argv', ['create-new-feature.py', '--number', '5', 'description']):
            args = self.parse_arguments()
            self.assertEqual(args.number, '5')

    def test_parse_arguments_with_all_options(self):
        """Test parsing with all options provided."""
        with patch('sys.argv', [
            'create-new-feature.py',
            '--json',
            '--short-name', 'test-feature',
            '--number', '10',
            'Add authentication system'
        ]):
            args = self.parse_arguments()
            self.assertTrue(args.json)
            self.assertEqual(args.short_name, 'test-feature')
            self.assertEqual(args.number, '10')
            self.assertEqual(args.feature_description, ['Add', 'authentication', 'system'])

    @patch('sys.exit')
    def test_parse_arguments_help_flag(self, mock_exit):
        """Test that --help flag displays help and exits."""
        with patch('sys.argv', ['create-new-feature.py', '--help']):
            with patch('builtins.print') as mock_print:
                self.parse_arguments()
                mock_exit.assert_called_with(0)
                mock_print.assert_called()

    @patch('sys.exit')
    def test_parse_arguments_missing_description(self, mock_exit):
        """Test that missing feature description causes exit with code 1."""
        with patch('sys.argv', ['create-new-feature.py']):
            with patch('builtins.print'):
                self.parse_arguments()
                mock_exit.assert_called_with(1)

    @patch('sys.exit')
    def test_parse_arguments_unknown_option(self, mock_exit):
        """Test that unknown options cause exit with code 1."""
        with patch('sys.argv', ['create-new-feature.py', '--unknown', 'description']):
            with patch('builtins.print'):
                self.parse_arguments()
                mock_exit.assert_called_with(1)


class TestDetermineBranchNumber(unittest.TestCase):
    """Test branch number detection logic."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('sys.argv', ['create-new-feature.py']):
            from create_new_feature import determine_branch_number
            self.determine_branch_number = determine_branch_number

    def test_determine_branch_number_with_user_provided(self):
        """Test branch number when user provides --number."""
        result = self.determine_branch_number('5', '/fake/specs', False)
        self.assertEqual(result, 5)

    def test_determine_branch_number_with_leading_zeros(self):
        """Test that leading zeros are stripped from user-provided number."""
        result = self.determine_branch_number('005', '/fake/specs', False)
        self.assertEqual(result, 5)

    def test_determine_branch_number_with_decimal_string(self):
        """Test that decimal strings are converted correctly."""
        result = self.determine_branch_number('42', '/fake/specs', False)
        self.assertEqual(result, 42)

    @patch('create_new_feature.feature_utils')
    def test_determine_branch_number_with_git(self, mock_utils):
        """Test branch number detection with git repository."""
        mock_utils.check_existing_branches.return_value = 10
        result = self.determine_branch_number('', '/fake/specs', True)
        self.assertEqual(result, 10)
        mock_utils.check_existing_branches.assert_called_once_with('/fake/specs')

    @patch('create_new_feature.feature_utils')
    def test_determine_branch_number_without_git(self, mock_utils):
        """Test branch number detection without git repository."""
        mock_utils.get_highest_from_specs.return_value = 7
        result = self.determine_branch_number('', '/fake/specs', False)
        self.assertEqual(result, 8)
        mock_utils.get_highest_from_specs.assert_called_once_with('/fake/specs')


class TestScriptExecution(TempDirectoryFixture):
    """Test end-to-end script execution."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Create required directory structure
        self.templates_dir = self.create_directory('.zo/templates')
        self.specs_dir = self.create_directory('specs')
        
        # Create a template file (spec-template.md for create-new-feature)
        self.template_content = """# Feature Specification

## Overview
{{OVERVIEW}}

## Requirements
{{REQUIREMENTS}}

## Implementation Notes
{{IMPLEMENTATION}}
"""
        self.create_file('.zo/templates/spec-template.md', self.template_content)
        
        # Store original directory
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        super().tearDown()

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.create_git_branch')
    @patch('create_new_feature.feature_utils.generate_branch_name')
    @patch('create_new_feature.feature_utils.check_existing_branches')
    def test_script_creates_feature_with_git(
        self, mock_check_branches, mock_generate, mock_create_branch, mock_has_git
    ):
        """Test script creates feature directory and files with git."""
        # Arrange
        mock_has_git.return_value = True
        mock_check_branches.return_value = 1
        mock_generate.return_value = 'user-authentication'
        mock_create_branch.return_value = None
        
        # Act
        result = run_python_script(
            str(script_dir / 'create-new-feature.py'),
            ['Add user authentication system'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        assert_directory_exists(os.path.join(self.temp_dir, 'specs', '001-user-authentication'))
        assert_file_exists(os.path.join(self.temp_dir, 'specs', '001-user-authentication', 'spec.md'))
        mock_create_branch.assert_called_once()
        
        # Check output format
        lines = result.stdout.strip().split('\n')
        self.assertIn('BRANCH_NAME:', lines[0])
        self.assertIn('001-user-authentication', lines[0])

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.get_highest_from_specs')
    @patch('create_new_feature.feature_utils.generate_branch_name')
    def test_script_creates_feature_without_git(
        self, mock_generate, mock_get_highest, mock_has_git
    ):
        """Test script creates feature directory without git."""
        # Arrange
        mock_has_git.return_value = False
        mock_get_highest.return_value = 2
        mock_generate.return_value = 'test-feature'
        
        # Act
        result = run_python_script(
            str(script_dir / 'create-new-feature.py'),
            ['Test feature description'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        assert_directory_exists(os.path.join(self.temp_dir, 'specs', '003-test-feature'))
        assert_file_exists(os.path.join(self.temp_dir, 'specs', '003-test-feature', 'spec.md'))

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.create_git_branch')
    @patch('create_new_feature.feature_utils.check_existing_branches')
    @patch('sys.argv', ['create-new-feature.py', '--json', 'Test feature'])
    def test_script_json_output(self, mock_check, mock_create, mock_has_git):
        """Test script outputs JSON format when --json flag is used."""
        # Arrange
        mock_has_git.return_value = True
        mock_check.return_value = 0
        mock_create.return_value = None
        
        # Act
        result = run_python_script(
            str(script_dir / 'create-new-feature.py'),
            ['--json', 'Test feature'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        data = parse_json_output(result.stdout)
        self.assertIn('BRANCH_NAME', data)
        self.assertIn('SPEC_FILE', data)
        self.assertIn('FEATURE_NUM', data)
        self.assertEqual(data['FEATURE_NUM'], '001')

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.create_git_branch')
    @patch('create_new_feature.feature_utils.clean_branch_name')
    @patch('create_new_feature.feature_utils.check_existing_branches')
    def test_script_with_short_name(
        self, mock_check, mock_clean, mock_create, mock_has_git
    ):
        """Test script uses --short-name argument."""
        # Arrange
        mock_has_git.return_value = True
        mock_check.return_value = 0
        mock_clean.return_value = 'custom-name'
        mock_create.return_value = None
        
        # Act
        result = run_python_script(
            str(script_dir / 'create-new-feature.py'),
            ['--short-name', 'custom-name', 'Long description here'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        assert_directory_exists(os.path.join(self.temp_dir, 'specs', '001-custom-name'))
        mock_clean.assert_called_once_with('custom-name')

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.create_git_branch')
    @patch('create_new_feature.feature_utils.check_existing_branches')
    def test_script_with_number_override(self, mock_check, mock_create, mock_has_git):
        """Test script respects --number argument."""
        # Arrange
        mock_has_git.return_value = True
        mock_check.return_value = 10  # Would normally return 10
        mock_create.return_value = None
        
        # Act
        result = run_python_script(
            str(script_dir / 'create-new-feature.py'),
            ['--number', '5', 'Test feature'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        # Should use number 5, not auto-detected 10
        self.assertIn('005', result.stdout)
        assert_directory_exists(os.path.join(self.temp_dir, 'specs', '005-test-feature'))

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.create_git_branch')
    @patch('create_new_feature.feature_utils.check_existing_branches')
    @patch('create_new_feature.feature_utils.truncate_branch_name')
    def test_script_truncates_long_branch_name(
        self, mock_truncate, mock_check, mock_create, mock_has_git
    ):
        """Test script truncates branch name if too long."""
        # Arrange
        mock_has_git.return_value = True
        mock_check.return_value = 0
        mock_create.return_value = None
        long_name = '001-' + 'very-long-branch-name-' * 10
        mock_truncate.return_value = '001-shortened'
        
        # Act
        result = run_python_script(
            str(script_dir / 'create-new-feature.py'),
            ['Test feature'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        mock_truncate.assert_called_once()

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.create_git_branch')
    @patch('create_new_feature.feature_utils.check_existing_branches')
    def test_script_copies_template(self, mock_check, mock_create, mock_has_git):
        """Test script copies template to spec file."""
        # Arrange
        mock_has_git.return_value = True
        mock_check.return_value = 0
        mock_create.return_value = None
        
        # Act
        result = run_python_script(
            str(script_dir / 'create-new-feature.py'),
            ['Test feature'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        spec_file = os.path.join(self.temp_dir, 'specs', '001-test-feature', 'spec.md')
        assert_file_contains(spec_file, 'Feature Specification')

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.create_git_branch')
    @patch('create_new_feature.feature_utils.check_existing_branches')
    def test_script_creates_empty_file_when_template_missing(
        self, mock_check, mock_create, mock_has_git
    ):
        """Test script creates empty spec file when template is missing."""
        # Arrange
        mock_has_git.return_value = True
        mock_check.return_value = 0
        mock_create.return_value = None
        
        # Remove template
        os.remove(os.path.join(self.temp_dir, '.zo/templates/spec-template.md'))
        
        # Act
        result = run_python_script(
            str(script_dir / 'create-new-feature.py'),
            ['Test feature'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        spec_file = os.path.join(self.temp_dir, 'specs', '001-test-feature', 'spec.md')
        assert_file_exists(spec_file)
        # File should be empty or very small
        with open(spec_file, 'r') as f:
            content = f.read()
            self.assertEqual(len(content), 0)

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.create_git_branch')
    @patch('create_new_feature.feature_utils.check_existing_branches')
    @patch('create_new_feature.feature_utils.generate_branch_name')
    def test_script_sets_environment_variable(
        self, mock_generate, mock_check, mock_create, mock_has_git
    ):
        """Test script sets SPECIFY_FEATURE environment variable."""
        # Arrange
        mock_has_git.return_value = True
        mock_check.return_value = 0
        mock_generate.return_value = 'test-feature'
        mock_create.return_value = None
        
        with patch('os.putenv') as mock_putenv:
            # Act
            result = run_python_script(
                str(script_dir / 'create-new-feature.py'),
                ['Test feature'],
                cwd=self.temp_dir
            )
            
            # Assert
            self.assertTrue(result.success)
            mock_putenv.assert_called_once_with('SPECIFY_FEATURE', '001-test-feature')

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.create_git_branch')
    @patch('create_new_feature.feature_utils.check_existing_branches')
    @patch('create_new_feature.feature_utils.generate_branch_name')
    def test_script_creates_specs_directory_if_missing(
        self, mock_generate, mock_check, mock_create, mock_has_git
    ):
        """Test script creates specs directory if it doesn't exist."""
        # Arrange
        mock_has_git.return_value = True
        mock_check.return_value = 0
        mock_generate.return_value = 'test-feature'
        mock_create.return_value = None
        
        # Remove specs directory
        shutil.rmtree(os.path.join(self.temp_dir, 'specs'))
        
        # Act
        result = run_python_script(
            str(script_dir / 'create-new-feature.py'),
            ['Test feature'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        assert_directory_exists(os.path.join(self.temp_dir, 'specs'))

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.create_git_branch')
    @patch('create_new_feature.feature_utils.check_existing_branches')
    @patch('create_new_feature.feature_utils.generate_branch_name')
    def test_script_with_multiword_description(
        self, mock_generate, mock_check, mock_create, mock_has_git
    ):
        """Test script handles multi-word descriptions correctly."""
        # Arrange
        mock_has_git.return_value = True
        mock_check.return_value = 0
        mock_generate.return_value = 'multi-word-feature-name'
        mock_create.return_value = None
        
        # Act
        result = run_python_script(
            str(script_dir / 'create-new-feature.py'),
            ['Implement', 'OAuth2', 'authentication', 'for', 'API'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        mock_generate.assert_called_once_with('Implement OAuth2 authentication for API')

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.create_git_branch')
    @patch('create_new_feature.feature_utils.check_existing_branches')
    @patch('create_new_feature.feature_utils.generate_branch_name')
    def test_script_creates_spec_from_spec_template(
        self, mock_generate, mock_check, mock_create, mock_has_git
    ):
        """Test script uses spec-template.md instead of spec-from-idea.md."""
        # Arrange
        mock_has_git.return_value = True
        mock_check.return_value = 0
        mock_generate.return_value = 'test-feature'
        mock_create.return_value = None
        
        # Create both templates with different content
        self.create_file('.zo/templates/spec-from-idea.md', 'From Idea Template')
        self.create_file('.zo/templates/spec-template.md', 'Spec Template Content')
        
        # Act
        result = run_python_script(
            str(script_dir / 'create-new-feature.py'),
            ['Test feature'],
            cwd=self.temp_dir
        )
        
        # Assert - should use spec-template.md
        self.assertTrue(result.success)
        spec_file = os.path.join(self.temp_dir, 'specs', '001-test-feature', 'spec.md')
        with open(spec_file, 'r') as f:
            content = f.read()
            self.assertIn('Spec Template Content', content)
            self.assertNotIn('From Idea Template', content)

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.create_git_branch')
    @patch('create_new_feature.feature_utils.check_existing_branches')
    @patch('create_new_feature.feature_utils.generate_branch_name')
    def test_script_with_special_characters_in_description(
        self, mock_generate, mock_check, mock_create, mock_has_git
    ):
        """Test script handles descriptions with special characters."""
        # Arrange
        mock_has_git.return_value = True
        mock_check.return_value = 0
        mock_generate.return_value = 'api-integration'
        mock_create.return_value = None
        
        # Act
        result = run_python_script(
            str(script_dir / 'create-new-feature.py'),
            ['Add API integration (v2) & testing'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        assert_directory_exists(os.path.join(self.temp_dir, 'specs', '001-api-integration'))

    @patch('create_new_feature.feature_utils.has_git')
    @patch('create_new_feature.feature_utils.create_git_branch')
    @patch('create_new_feature.feature_utils.check_existing_branches')
    @patch('create_new_feature.feature_utils.generate_branch_name')
    def test_script_with_unicode_description(
        self, mock_generate, mock_check, mock_create, mock_has_git
    ):
        """Test script handles unicode characters in description."""
        # Arrange
        mock_has_git.return_value = True
        mock_check.return_value = 0
        mock_generate.return_value = 'feature-name'
        mock_create.return_value = None
        
        # Act
        result = run_python_script(
            str(script_dir / 'create-new-feature.py'),
            ['Add feature with émojis 🎉 and spëcial çharacters'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        assert_directory_exists(os.path.join(self.temp_dir, 'specs', '001-feature-name'))


if __name__ == '__main__':
    unittest.main()
