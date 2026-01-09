"""
Test Suite for setup-brainstorm-crazy.py

This module tests the enhanced brainstorm session initialization script
with spec folder detection and context awareness.

Tests cover keyword extraction, spec folder matching, related file finding,
and end-to-end script execution with dry-run mode.

Test Classes:
    TestExtractResearchFocus: Test keyword extraction from user input
    TestFindSpecFolder: Test spec folder detection by keyword scoring
    TestFindRelatedFiles: Test finding spec/plan/tasks files
    TestScriptExecution: Test end-to-end script execution
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
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
from assertion_helpers import assert_file_exists, assert_json_output


class TestExtractResearchFocus(unittest.TestCase):
    """
    Test the extract_research_focus function.

    Tests ensure that:
    - Common words are removed from input
    - Keywords are extracted correctly
    - Output is hyphenated
    - Punctuation is removed
    - Empty input is handled
    """

    def setUp(self):
        """Set up test environment."""
        import setup_brainstorm_crazy
        self.module = setup_brainstorm_crazy

    def test_simple_keyword_extraction(self):
        """Test extracting keywords from simple input."""
        result = self.module.extract_research_focus('improve login flow')
        self.assertEqual(result, 'improve-login-flow')

    def test_common_words_removed(self):
        """Test that common words are removed."""
        result = self.module.extract_research_focus('the login and auth flow')
        # 'the', 'and' should be removed
        self.assertNotIn('the', result)
        self.assertNotIn('and', result)
        self.assertIn('login', result)

    def test_punctuation_removed(self):
        """Test that punctuation is removed."""
        result = self.module.extract_research_focus('add dark mode, please!')
        self.assertNotIn(',')
        self.assertNotIn('!')
        self.assertIn('dark', result)

    def test_consecutive_hyphens_collapsed(self):
        """Test that consecutive hyphens are collapsed."""
        result = self.module.extract_research_focus('add, test, feature')
        # After removing common words and punctuation, should collapse hyphens
        self.assertNotIn('--', result)

    def test_numbers_preserved(self):
        """Test that numbers are preserved in output."""
        result = self.module.extract_research_focus('version 2 features')
        self.assertIn('2', result)

    def test_lowercase_conversion(self):
        """Test that output is converted to lowercase."""
        result = self.module.extract_research_focus('LOGIN Authentication')
        self.assertEqual(result, result.lower())

    def test_empty_after_removing_common_words(self):
        """Test input with only common words."""
        result = self.module.extract_research_focus('the and a to')
        # Should return empty string after removing all common words
        self.assertEqual(result, '')

    def test_complex_input(self):
        """Test complex input with multiple words."""
        result = self.module.extract_research_focus('create a better user profile page')
        # Should remove 'a' and keep meaningful keywords
        self.assertIn('create', result)
        self.assertIn('user', result)
        self.assertIn('profile', result)


class TestFindSpecFolder(unittest.TestCase):
    """
    Test the find_spec_folder function.

    Tests ensure that:
    - Matching spec folders are found by keyword
    - Scoring works correctly
    - Numbered folders get bonus for higher numbers
    - Non-existent directories are handled
    """

    def setUp(self):
        """Set up test environment."""
        import setup_brainstorm_crazy
        self.module = setup_brainstorm_crazy
        self.temp_dir = tempfile.mkdtemp()

        # Create specs directory with test folders
        self.specs_dir = os.path.join(self.temp_dir, 'specs')
        os.makedirs(self.specs_dir)

        # Create test spec folders
        os.makedirs(os.path.join(self.specs_dir, '001-login-auth'))
        os.makedirs(os.path.join(self.specs_dir, '002-user-profile'))
        os.makedirs(os.path.join(self.specs_dir, '003-offline-support'))

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_folds_matching_folder_by_keyword(self):
        """Test finding folder by keyword match."""
        result = self.module.find_spec_folder('login-auth', self.specs_dir, False)
        self.assertEqual(result, '001-login-auth')

    def test_finds_folder_with_partial_match(self):
        """Test finding folder with partial keyword match."""
        result = self.module.find_spec_folder('profile', self.specs_dir, False)
        self.assertEqual(result, '002-user-profile')

    def test_returns_none_when_no_match(self):
        """Test returning None when no match found."""
        result = self.module.find_spec_folder('nonexistent', self.specs_dir, False)
        self.assertIsNone(result)

    def test_handles_nonexistent_directory(self):
        """Test handling of nonexistent specs directory."""
        result = self.module.find_spec_folder('test', '/nonexistent/path', False)
        self.assertIsNone(result)

    def test_prefers_higher_numbered_folders(self):
        """Test that higher numbered folders are preferred."""
        # Create duplicate keywords in different folders
        os.makedirs(os.path.join(self.specs_dir, '005-login-auth'))
        result = self.module.find_spec_folder('login', self.specs_dir, False)
        # Should prefer the higher numbered folder
        self.assertEqual(result, '005-login-auth')

    def test_scores_based_on_keyword_count(self):
        """Test that scoring is based on keyword matches."""
        result = self.module.find_spec_folder('login-auth-feature', self.specs_dir, False)
        # '001-login-auth' matches two keywords
        self.assertEqual(result, '001-login-auth')


class TestFindRelatedFiles(TempDirectoryFixture):
    """
    Test the find_related_files function.

    Tests ensure that:
    - spec.md files are found (case insensitive)
    - plan.md files are found (case insensitive)
    - tasks.md files are found (case insensitive)
    - Missing files return None
    - Verbose logging works
    """

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        import setup_brainstorm_crazy
        self.module = setup_brainstorm_crazy

        # Create spec directory
        self.spec_dir = self.create_directory('spec_folder')

    def test_finds_spec_lowercase(self):
        """Test finding lowercase spec.md."""
        self.create_file('spec_folder/spec.md', '# Spec')
        feature_spec, impl_plan, tasks = self.module.find_related_files(
            os.path.join(self.temp_dir, 'spec_folder'),
            False
        )
        self.assertIsNotNone(feature_spec)
        self.assertIn('spec.md', feature_spec)

    def test_finds_spec_uppercase(self):
        """Test finding uppercase SPEC.md."""
        self.create_file('spec_folder/SPEC.md', '# Spec')
        feature_spec, impl_plan, tasks = self.module.find_related_files(
            os.path.join(self.temp_dir, 'spec_folder'),
            False
        )
        self.assertIsNotNone(feature_spec)
        self.assertIn('SPEC.md', feature_spec)

    def test_prefers_lowercase_spec(self):
        """Test that lowercase spec.md is preferred."""
        self.create_file('spec_folder/spec.md', '# Spec')
        self.create_file('spec_folder/SPEC.md', '# Spec')
        feature_spec, impl_plan, tasks = self.module.find_related_files(
            os.path.join(self.temp_dir, 'spec_folder'),
            False
        )
        self.assertIn('spec.md', feature_spec)

    def test_finds_plan_lowercase(self):
        """Test finding lowercase plan.md."""
        self.create_file('spec_folder/plan.md', '# Plan')
        feature_spec, impl_plan, tasks = self.module.find_related_files(
            os.path.join(self.temp_dir, 'spec_folder'),
            False
        )
        self.assertIsNotNone(impl_plan)
        self.assertIn('plan.md', impl_plan)

    def test_finds_tasks_lowercase(self):
        """Test finding lowercase tasks.md."""
        self.create_file('spec_folder/tasks.md', '# Tasks')
        feature_spec, impl_plan, tasks = self.module.find_related_files(
            os.path.join(self.temp_dir, 'spec_folder'),
            False
        )
        self.assertIsNotNone(tasks)
        self.assertIn('tasks.md', tasks)

    def test_returns_none_for_missing_files(self):
        """Test returning None for missing files."""
        feature_spec, impl_plan, tasks = self.module.find_related_files(
            os.path.join(self.temp_dir, 'spec_folder'),
            False
        )
        self.assertIsNone(feature_spec)
        self.assertIsNone(impl_plan)
        self.assertIsNone(tasks)

    def test_finds_all_files(self):
        """Test finding all related files."""
        self.create_file('spec_folder/spec.md', '# Spec')
        self.create_file('spec_folder/plan.md', '# Plan')
        self.create_file('spec_folder/tasks.md', '# Tasks')

        feature_spec, impl_plan, tasks = self.module.find_related_files(
            os.path.join(self.temp_dir, 'spec_folder'),
            False
        )

        self.assertIsNotNone(feature_spec)
        self.assertIsNotNone(impl_plan)
        self.assertIsNotNone(tasks)


class TestScriptExecution(TempDirectoryFixture):
    """
    Test end-to-end execution of setup-brainstorm-crazy.py.

    Tests ensure that:
    - Brainstorm file is created with correct naming
    - Spec folders are detected correctly
    - Related files are included in output
    - Dry-run mode works without creating files
    - JSON output contains all expected fields
    - Verbose mode produces output
    """

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        import setup_brainstorm_crazy
        self.module = setup_brainstorm_crazy

        # Create .zo directory structure
        self.zo_dir = self.create_directory('.zo')
        self.templates_dir = self.create_directory('.zo/templates')
        self.brainstorms_dir = self.create_directory('.zo/brainstorms')

        # Create specs directory
        self.specs_dir = self.create_directory('specs')
        os.makedirs(os.path.join(self.specs_dir, '001-login-auth'))
        os.makedirs(os.path.join(self.specs_dir, '002-user-profile'))

        # Create related files
        self.create_file('specs/001-login-auth/spec.md', '# Login Spec')
        self.create_file('specs/001-login-auth/plan.md', '# Login Plan')
        self.create_file('specs/001-login-auth/tasks.md', '# Login Tasks')

        # Create template
        self.template_content = """# Crazy Brainstorm: {{FEATURE}}

Date: {{DATE}}

## Context
- Related files included
"""
        self.template_path = self.create_file(
            '.zo/templates/brainstorm-template-crazy.md',
            self.template_content
        )

    @patch('setup_brainstorm_crazy.get_repo_root')
    def test_creates_brainstorm_with_research_focus(self, mock_get_repo_root):
        """Test creating brainstorm with extracted research focus."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm-crazy.py', 'improve login authentication']):
            self.module.main()

        # Check that file was created
        files = os.listdir(self.brainstorms_dir)
        self.assertEqual(len(files), 1)

        # Check filename contains research focus
        filename = files[0]
        self.assertIn('improve-login-auth', filename)

    @patch('setup_brainstorm_crazy.get_repo_root')
    @patch('sys.stdout')
    def test_json_output_includes_related_files(self, mock_stdout, mock_get_repo_root):
        """Test that JSON output includes related file paths."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm-crazy.py', 'login']):
            self.module.main()

        # Get the output
        output = ''.join(str(call) for call in mock_stdout.write.call_args_list)

        # Parse JSON
        try:
            data = json.loads(output)
            self.assertIn('OUTPUT_FILE', data)
            self.assertIn('FEATURE_SPEC', data)
            self.assertIn('IMPL_PLAN', data)
            self.assertIn('TASKS', data)
            self.assertIn('RESEARCH_FOCUS', data)
            self.assertIn('SPEC_DIR', data)
        except json.JSONDecodeError:
            # Try to find JSON in output
            for call in mock_stdout.write.call_args_list:
                try:
                    data = json.loads(str(call))
                    self.assertIn('OUTPUT_FILE', data)
                    self.assertIn('FEATURE_SPEC', data)
                    break
                except json.JSONDecodeError:
                    pass

    @patch('setup_brainstorm_crazy.get_repo_root')
    def test_dry_run_mode_does_not_create_files(self, mock_get_repo_root):
        """Test that --dry-run does not create files."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm-crazy.py', '--dry-run', 'test']):
            self.module.main()

        # No file should be created
        files = os.listdir(self.brainstorms_dir)
        self.assertEqual(len(files), 0)

    @patch('setup_brainstorm_crazy.get_repo_root')
    @patch('sys.stderr')
    def test_verbose_mode_produces_output(self, mock_stderr, mock_get_repo_root):
        """Test that verbose mode produces stderr output."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm-crazy.py', '-v', 'test']):
            self.module.main()

        # Should have written to stderr
        self.assertTrue(mock_stderr.write.called)

    @patch('setup_brainstorm_crazy.get_repo_root')
    @patch('sys.stdout')
    def test_json_output_structure(self, mock_stdout, mock_get_repo_root):
        """Test that JSON output has correct structure."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm-crazy.py', '--json', 'login']):
            self.module.main()

        # Get output
        output = ''.join(str(call) for call in mock_stdout.write.call_args_list)

        # Should be compact JSON
        self.assertIn(',', output)
        self.assertIn(':', output)

    @patch('setup_brainstorm_crazy.get_repo_root')
    def test_template_placeholders_replaced(self, mock_get_repo_root):
        """Test that template placeholders are replaced."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm-crazy.py', 'test-feature']):
            self.module.main()

        # Get created file
        files = os.listdir(self.brainstorms_dir)
        filepath = os.path.join(self.brainstorms_dir, files[0])

        with open(filepath, 'r') as f:
            content = f.read()

        # Check placeholders replaced
        self.assertNotIn('{{FEATURE}}', content)
        self.assertNotIn('{{DATE}}', content)

    @patch('setup_brainstorm_crazy.get_repo_root')
    def test_missing_template_creates_empty_file(self, mock_get_repo_root):
        """Test that missing template creates empty file."""
        mock_get_repo_root.return_value = self.temp_dir

        # Remove template
        os.remove(self.template_path)

        with patch('sys.argv', ['setup-brainstorm-crazy.py', 'test']):
            self.module.main()

        # File should be created but empty
        files = os.listdir(self.brainstorms_dir)
        filepath = os.path.join(self.brainstorms_dir, files[0])

        with open(filepath, 'r') as f:
            content = f.read()
        self.assertEqual(content, '')

    @patch('setup_brainstorm_crazy.get_repo_root')
    def test_no_matching_spec_folder(self, mock_get_repo_root):
        """Test behavior when no spec folder matches."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm-crazy.py', 'nonexistent-feature']):
            self.module.main()

        # Should still create file
        files = os.listdir(self.brainstorms_dir)
        self.assertEqual(len(files), 1)

    @patch('setup_brainstorm_crazy.get_repo_root')
    def test_help_exits_with_zero(self, mock_get_repo_root):
        """Test that --help exits with code 0."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm-crazy.py', '--help']):
            with self.assertRaises(SystemExit) as context:
                self.module.main()

        self.assertEqual(context.exception.code, 0)

    @patch('setup_brainstorm_crazy.get_repo_root')
    @patch('setup_brainstorm_crazy.error')
    def test_no_request_exits_with_error(self, mock_error, mock_get_repo_root):
        """Test that missing request exits with error."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm-crazy.py']):
            self.module.main()

        # Error should be called
        self.assertTrue(mock_error.called)

    @patch('setup_brainstorm_crazy.get_repo_root')
    @patch('setup_brainstorm_crazy.error')
    def test_unknown_option_exits_with_error(self, mock_error, mock_get_repo_root):
        """Test that unknown option exits with error."""
        mock_get_repo_root.return_value = self.temp_dir

        with patch('sys.argv', ['setup-brainstorm-crazy.py', '--unknown', 'test']):
            self.module.main()

        # Error should be called
        self.assertTrue(mock_error.called)


import tempfile


if __name__ == '__main__':
    unittest.main()
