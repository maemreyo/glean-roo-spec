"""
Comprehensive Test Suite for common.py

This module tests the core utility functions in .zo/scripts/python/common.py
including git operations, repository functions, path management, and validation.

Test Classes:
    TestGitOperations: Tests for git command execution and availability
    TestRepositoryFunctions: Tests for repository root and branch detection
    TestPathManagement: Tests for feature path retrieval and formatting
    TestValidationFunctions: Tests for file/directory validation
"""

import os
import sys
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Configure logging with debug mode support
if os.environ.get('DEBUG') or os.environ.get('ZO_DEBUG'):
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / '.zo' / 'scripts' / 'python'))

from common import (
    run_git_command,
    has_git,
    get_repo_root,
    get_current_branch,
    find_feature_dir_by_prefix,
    get_feature_dir,
    get_feature_paths,
    format_feature_paths_for_eval,
    check_feature_branch,
    check_file_exists,
    check_dir_exists,
    check_dir_exists_with_files,
    check_file,
    check_dir
)


class TestGitOperations(unittest.TestCase):
    """
    Test git command execution and availability checks.
    
    Tests the behavior of run_git_command() and has_git() functions,
    including success cases, error handling, and edge cases.
    """

    def setUp(self):
        """Set up test fixtures for git operations."""
        self.original_dir = os.getcwd()

    def tearDown(self):
        """Clean up after tests."""
        os.chdir(self.original_dir)

    @patch('common.subprocess.run')
    def test_run_git_command_success(self, mock_run):
        """
        Test that run_git_command returns output on successful execution.
        
        Given: A git command that will succeed
        When: The command is executed
        Then: The stdout output is returned, stripped of whitespace
        """
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='  test-output  \n',
            stderr=''
        )

        result = run_git_command(['status'])

        self.assertEqual(result, 'test-output')
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        self.assertEqual(call_args[1]['timeout'], 5)
        self.assertTrue(call_args[1]['capture_output'])
        self.assertTrue(call_args[1]['text'])

    @patch('common.subprocess.run')
    def test_run_git_command_failure_returns_none(self, mock_run):
        """
        Test that run_git_command returns None when command fails.
        
        Given: A git command that will fail (non-zero exit code)
        When: The command is executed
        Then: None is returned
        """
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='fatal: not a git repository'
        )

        result = run_git_command(['status'])

        self.assertIsNone(result)

    @patch('common.subprocess.run')
    def test_run_git_command_timeout_returns_none(self, mock_run):
        """
        Test that run_git_command returns None on timeout.
        
        Given: A git command that times out
        When: The command is executed
        Then: None is returned
        """
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('git', 5)

        result = run_git_command(['status'])

        self.assertIsNone(result)

    @patch('common.subprocess.run')
    def test_run_git_command_git_not_found_returns_none(self, mock_run):
        """
        Test that run_git_command returns None when git is not found.
        
        Given: A system without git installed
        When: Any git command is executed
        Then: None is returned
        """
        mock_run.side_effect = FileNotFoundError('git not found')

        result = run_git_command(['status'])

        self.assertIsNone(result)

    @patch('common.run_git_command')
    def test_has_git_returns_true_when_git_available(self, mock_run_git):
        """
        Test that has_git returns True when git is available.
        
        Given: A system with git installed and in a git repository
        When: has_git is called
        Then: True is returned
        """
        mock_run_git.return_value = '/path/to/repo'

        result = has_git()

        self.assertTrue(result)
        mock_run_git.assert_called_once_with(['rev-parse', '--show-toplevel'])

    @patch('common.run_git_command')
    def test_has_git_returns_false_when_git_unavailable(self, mock_run_git):
        """
        Test that has_git returns False when git is not available.
        
        Given: A system without git or not in a git repository
        When: has_git is called
        Then: False is returned
        """
        mock_run_git.return_value = None

        result = has_git()

        self.assertFalse(result)


class TestRepositoryFunctions(unittest.TestCase):
    """
    Test repository detection and branch functions.
    
    Tests get_repo_root(), get_current_branch(), and find_feature_dir_by_prefix()
    with various scenarios including git repositories and non-git environments.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.original_dir = os.getcwd()
        self.temp_dir = tempfile.mkdtemp(prefix='test_common_')

    def tearDown(self):
        """Clean up temporary directories."""
        os.chdir(self.original_dir)
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('common.run_git_command')
    def test_get_repo_root_returns_git_root(self, mock_run_git):
        """
        Test that get_repo_root returns git repository root when available.
        
        Given: Inside a git repository
        When: get_repo_root is called
        Then: The git repository root path is returned
        """
        mock_run_git.return_value = '/path/to/git/root'

        result = get_repo_root()

        self.assertEqual(result, '/path/to/git/root')
        mock_run_git.assert_called_once_with(['rev-parse', '--show-toplevel'])

    @patch('common.run_git_command')
    def test_get_repo_root_fallback_to_script_location(self, mock_run_git):
        """
        Test that get_repo_root falls back to script location when no git.
        
        Given: Not in a git repository
        When: get_repo_root is called
        Then: A path based on script location is returned
        """
        mock_run_git.return_value = None

        result = get_repo_root()

        # Should resolve to a path based on common.py's location
        self.assertIsInstance(result, str)
        self.assertTrue(os.path.isabs(result))

    @patch.dict(os.environ, {'SPECIFY_FEATURE': '001-test-feature'})
    @patch('common.run_git_command')
    def test_get_current_branch_from_env_var(self, mock_run_git):
        """
        Test that get_current_branch reads from SPECIFY_FEATURE environment variable.
        
        Given: SPECIFY_FEATURE environment variable is set
        When: get_current_branch is called
        Then: The value from the environment variable is returned
        """
        result = get_current_branch()

        self.assertEqual(result, '001-test-feature')
        mock_run_git.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch('common.run_git_command')
    def test_get_current_branch_from_git(self, mock_run_git):
        """
        Test that get_current_branch gets branch name from git.
        
        Given: In a git repository with current branch 'feature-001'
        When: get_current_branch is called
        Then: The git branch name is returned
        """
        mock_run_git.return_value = 'feature-001'

        result = get_current_branch()

        self.assertEqual(result, 'feature-001')
        mock_run_git.assert_called_once_with(['rev-parse', '--abbrev-ref', 'HEAD'])

    @patch.dict(os.environ, {}, clear=True)
    @patch('common.run_git_command')
    def test_get_current_branch_fallback_to_main(self, mock_run_git):
        """
        Test that get_current_branch returns 'main' when no git and no specs directory.
        
        Given: Not in git and no specs directory exists
        When: get_current_branch is called
        Then: 'main' is returned as fallback
        """
        mock_run_git.return_value = None

        # Create a temporary directory structure without specs
        os.chdir(self.temp_dir)

        result = get_current_branch()

        self.assertEqual(result, 'main')

    @patch.dict(os.environ, {}, clear=True)
    @patch('common.run_git_command')
    @patch('common.get_repo_root')
    def test_get_current_branch_finds_latest_feature_directory(self, mock_get_repo_root, mock_run_git):
        """
        Test that get_current_branch finds the latest feature directory from specs.
        
        Given: Not in git, but specs directory has feature directories
        When: get_current_branch is called
        Then: The highest numbered feature directory name is returned
        """
        mock_run_git.return_value = None
        mock_get_repo_root.return_value = self.temp_dir

        # Create specs directory with feature directories
        specs_dir = Path(self.temp_dir) / 'specs'
        specs_dir.mkdir()
        (specs_dir / '001-first-feature').mkdir()
        (specs_dir / '003-third-feature').mkdir()
        (specs_dir / '002-second-feature').mkdir()

        os.chdir(self.temp_dir)

        result = get_current_branch()

        self.assertEqual(result, '003-third-feature')

    def test_find_feature_dir_by_prefix_with_numeric_prefix(self):
        """
        Test finding feature directory by numeric prefix.
        
        Given: A specs directory with feature directories
        When: find_feature_dir_by_prefix is called with a numeric prefix
        Then: The matching feature directory path is returned
        """
        # Create specs directory structure
        specs_dir = Path(self.temp_dir) / 'specs'
        specs_dir.mkdir()
        (specs_dir / '001-test-feature').mkdir()

        result = find_feature_dir_by_prefix(self.temp_dir, '001-something')

        expected_path = str(specs_dir / '001-test-feature')
        self.assertEqual(result, expected_path)

    def test_find_feature_dir_by_prefix_no_match(self):
        """
        Test find_feature_dir_by_prefix when no matching directory exists.
        
        Given: A specs directory without matching feature directory
        When: find_feature_dir_by_prefix is called with a non-existent prefix
        Then: A path with the branch name is returned (will fail later)
        """
        # Create specs directory without the specific feature
        specs_dir = Path(self.temp_dir) / 'specs'
        specs_dir.mkdir()

        result = find_feature_dir_by_prefix(self.temp_dir, '999-nonexistent')

        expected_path = str(specs_dir / '999-nonexistent')
        self.assertEqual(result, expected_path)

    def test_find_feature_dir_by_prefix_no_numeric_prefix(self):
        """
        Test find_feature_dir_by_prefix with branch without numeric prefix.
        
        Given: A branch name without numeric prefix
        When: find_feature_dir_by_prefix is called
        Then: The path is constructed using exact branch name match
        """
        # Create specs directory
        specs_dir = Path(self.temp_dir) / 'specs'
        specs_dir.mkdir()
        (specs_dir / 'main').mkdir()

        result = find_feature_dir_by_prefix(self.temp_dir, 'main')

        expected_path = str(specs_dir / 'main')
        self.assertEqual(result, expected_path)

    def test_find_feature_dir_by_prefix_multiple_matches(self):
        """
        Test find_feature_dir_by_prefix when multiple directories match prefix.
        
        Given: Multiple feature directories with same numeric prefix
        When: find_feature_dir_by_prefix is called
        Then: The branch name path is returned (error logged but no exception)
        """
        # Create specs directory with duplicate prefixes
        specs_dir = Path(self.temp_dir) / 'specs'
        specs_dir.mkdir()
        (specs_dir / '001-first').mkdir()
        (specs_dir / '001-second').mkdir()

        # Should log error but still return a path
        result = find_feature_dir_by_prefix(self.temp_dir, '001-test')

        # Returns the branch name path as fallback
        expected_path = str(specs_dir / '001-test')
        self.assertEqual(result, expected_path)


class TestPathManagement(unittest.TestCase):
    """
    Test feature path retrieval and formatting functions.
    
    Tests get_feature_paths() and format_feature_paths_for_eval() to ensure
    proper path construction and bash-compatible formatting.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.original_dir = os.getcwd()

    def tearDown(self):
        """Clean up after tests."""
        os.chdir(self.original_dir)

    @patch('common.get_current_branch')
    @patch('common.get_repo_root')
    @patch('common.has_git')
    @patch('common.find_feature_dir_by_prefix')
    def test_get_feature_paths_returns_all_paths(self, mock_find_dir, mock_has_git, mock_repo_root, mock_branch):
        """
        Test that get_feature_paths returns dictionary with all expected paths.
        
        Given: A repository with git available
        When: get_feature_paths is called
        Then: A dictionary with all expected path keys is returned
        """
        mock_repo_root.return_value = '/test/repo'
        mock_branch.return_value = '001-test-feature'
        mock_has_git.return_value = True
        mock_find_dir.return_value = '/test/repo/specs/001-test-feature'

        result = get_feature_paths()

        # Check all expected keys are present
        expected_keys = [
            'REPO_ROOT', 'CURRENT_BRANCH', 'HAS_GIT', 'FEATURE_DIR',
            'FEATURE_SPEC', 'IMPL_PLAN', 'TASKS', 'RESEARCH', 'DATA_MODEL',
            'QUICKSTART', 'CONTRACTS_DIR', 'DESIGN_FILE', 'GLOBAL_DESIGN_SYSTEM'
        ]

        for key in expected_keys:
            self.assertIn(key, result)

        # Check specific values
        self.assertEqual(result['REPO_ROOT'], '/test/repo')
        self.assertEqual(result['CURRENT_BRANCH'], '001-test-feature')
        self.assertEqual(result['HAS_GIT'], 'true')
        self.assertEqual(result['FEATURE_DIR'], '/test/repo/specs/001-test-feature')
        self.assertEqual(result['FEATURE_SPEC'], '/test/repo/specs/001-test-feature/spec.md')
        self.assertEqual(result['GLOBAL_DESIGN_SYSTEM'], '/test/repo/.zo/design-system.md')

    @patch('common.get_feature_paths')
    def test_format_feature_paths_for_eval_formatting(self, mock_get_paths):
        """
        Test bash eval formatting of feature paths.
        
        Given: Feature paths dictionary
        When: format_feature_paths_for_eval is called
        Then: Properly formatted bash variable assignments are returned
        """
        mock_get_paths.return_value = {
            'REPO_ROOT': '/test/repo',
            'CURRENT_BRANCH': '001-test',
            'HAS_GIT': 'true',
            'FEATURE_DIR': '/test/repo/specs/001-test',
            'FEATURE_SPEC': '/test/repo/specs/001-test/spec.md',
            'IMPL_PLAN': '/test/repo/specs/001-test/plan.md',
            'TASKS': '/test/repo/specs/001-test/tasks.md',
            'RESEARCH': '/test/repo/specs/001-test/research.md',
            'DATA_MODEL': '/test/repo/specs/001-test/data-model.md',
            'QUICKSTART': '/test/repo/specs/001-test/quickstart.md',
            'CONTRACTS_DIR': '/test/repo/specs/001-test/contracts',
            'DESIGN_FILE': '/test/repo/specs/001-test/design.md',
        }

        result = format_feature_paths_for_eval()

        # Check that result is a string with proper bash assignments
        self.assertIsInstance(result, str)
        self.assertIn("REPO_ROOT='/test/repo'", result)
        self.assertIn("CURRENT_BRANCH='001-test'", result)
        self.assertIn("HAS_GIT='true'", result)

        # Check that lines are separated by newlines
        lines = result.strip().split('\n')
        self.assertEqual(len(lines), 12)


class TestValidationFunctions(unittest.TestCase):
    """
    Test file and directory validation functions.
    
    Tests check_feature_branch(), check_file_exists(), check_dir_exists(),
    check_dir_exists_with_files(), check_file(), and check_dir().
    """

    def setUp(self):
        """Set up test fixtures with temporary files and directories."""
        self.original_dir = os.getcwd()
        self.temp_dir = tempfile.mkdtemp(prefix='test_validation_')

    def tearDown(self):
        """Clean up temporary files and directories."""
        os.chdir(self.original_dir)
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_check_feature_branch_valid_with_git(self):
        """
        Test check_feature_branch with valid branch pattern and git.
        
        Given: A branch name matching ###-* pattern and git is available
        When: check_feature_branch is called
        Then: (True, None) is returned
        """
        is_valid, error = check_feature_branch('001-test-feature', has_git_repo=True)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_check_feature_branch_invalid_pattern(self):
        """
        Test check_feature_branch with invalid branch pattern.
        
        Given: A branch name not matching ###-* pattern
        When: check_feature_branch is called with git available
        Then: (False, error_message) is returned
        """
        is_valid, error = check_feature_branch('main', has_git_repo=True)

        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn('Not on a feature branch', error)
        self.assertIn('001-feature-name', error)

    def test_check_feature_branch_valid_without_git(self):
        """
        Test check_feature_branch passes when git is not available.
        
        Given: Any branch name but git is not available
        When: check_feature_branch is called
        Then: (True, None) is returned (validation skipped for non-git)
        """
        is_valid, error = check_feature_branch('any-branch', has_git_repo=False)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_check_file_exists_with_existing_file(self):
        """
        Test check_file_exists returns True for existing file.
        
        Given: A file that exists on the filesystem
        When: check_file_exists is called with that path
        Then: True is returned
        """
        # Create a test file
        test_file = Path(self.temp_dir) / 'test.txt'
        test_file.write_text('content')

        result = check_file_exists(str(test_file))

        self.assertTrue(result)

    def test_check_file_exists_with_nonexistent_file(self):
        """
        Test check_file_exists returns False for non-existent file.
        
        Given: A file path that does not exist
        When: check_file_exists is called
        Then: False is returned
        """
        result = check_file_exists('/nonexistent/file.txt')

        self.assertFalse(result)

    def test_check_file_exists_with_directory(self):
        """
        Test check_file_exists returns False for directory path.
        
        Given: A path to a directory (not a file)
        When: check_file_exists is called
        Then: False is returned
        """
        result = check_file_exists(self.temp_dir)

        self.assertFalse(result)

    def test_check_dir_exists_with_existing_directory(self):
        """
        Test check_dir_exists returns True for existing directory.
        
        Given: A directory that exists on the filesystem
        When: check_dir_exists is called with that path
        Then: True is returned
        """
        result = check_dir_exists(self.temp_dir)

        self.assertTrue(result)

    def test_check_dir_exists_with_nonexistent_directory(self):
        """
        Test check_dir_exists returns False for non-existent directory.
        
        Given: A directory path that does not exist
        When: check_dir_exists is called
        Then: False is returned
        """
        result = check_dir_exists('/nonexistent/directory')

        self.assertFalse(result)

    def test_check_dir_exists_with_file(self):
        """
        Test check_dir_exists returns False for file path.
        
        Given: A path to a file (not a directory)
        When: check_dir_exists is called
        Then: False is returned
        """
        # Create a test file
        test_file = Path(self.temp_dir) / 'test.txt'
        test_file.write_text('content')

        result = check_dir_exists(str(test_file))

        self.assertFalse(result)

    def test_check_dir_exists_with_files_has_content(self):
        """
        Test check_dir_exists_with_files returns True for directory with files.
        
        Given: A directory containing files
        When: check_dir_exists_with_files is called
        Then: True is returned
        """
        # Create a directory with a file
        test_dir = Path(self.temp_dir) / 'with_files'
        test_dir.mkdir()
        (test_dir / 'file.txt').write_text('content')

        result = check_dir_exists_with_files(str(test_dir))

        self.assertTrue(result)

    def test_check_dir_exists_with_files_empty_directory(self):
        """
        Test check_dir_exists_with_files returns False for empty directory.
        
        Given: An empty directory
        When: check_dir_exists_with_files is called
        Then: False is returned
        """
        # Create an empty directory
        test_dir = Path(self.temp_dir) / 'empty'
        test_dir.mkdir()

        result = check_dir_exists_with_files(str(test_dir))

        self.assertFalse(result)

    def test_check_dir_exists_with_files_nonexistent_directory(self):
        """
        Test check_dir_exists_with_files returns False for non-existent directory.
        
        Given: A directory path that does not exist
        When: check_dir_exists_with_files is called
        Then: False is returned
        """
        result = check_dir_exists_with_files('/nonexistent/directory')

        self.assertFalse(result)

    def test_check_file_returns_checkmark_for_existing_file(self):
        """
        Test check_file returns formatted string with checkmark for existing file.
        
        Given: A file that exists
        When: check_file is called
        Then: A string with checkmark and display name is returned
        """
        # Create a test file
        test_file = Path(self.temp_dir) / 'test.txt'
        test_file.write_text('content')

        result = check_file(str(test_file), 'Test File')

        self.assertEqual(result, '  ✓ Test File')

    def test_check_file_returns_x_mark_for_missing_file(self):
        """
        Test check_file returns formatted string with X mark for missing file.
        
        Given: A file that does not exist
        When: check_file is called
        Then: A string with X mark and display name is returned
        """
        result = check_file('/nonexistent/file.txt', 'Missing File')

        self.assertEqual(result, '  ✗ Missing File')

    def test_check_dir_returns_checkmark_for_directory_with_files(self):
        """
        Test check_dir returns formatted string with checkmark for directory with files.
        
        Given: A directory containing files
        When: check_dir is called
        Then: A string with checkmark and display name is returned
        """
        # Create a directory with a file
        test_dir = Path(self.temp_dir) / 'with_files'
        test_dir.mkdir()
        (test_dir / 'file.txt').write_text('content')

        result = check_dir(str(test_dir), 'Test Directory')

        self.assertEqual(result, '  ✓ Test Directory')

    def test_check_dir_returns_x_mark_for_empty_or_missing_directory(self):
        """
        Test check_dir returns formatted string with X mark for empty/missing directory.
        
        Given: An empty or non-existent directory
        When: check_dir is called
        Then: A string with X mark and display name is returned
        """
        # Create an empty directory
        test_dir = Path(self.temp_dir) / 'empty'
        test_dir.mkdir()

        result = check_dir(str(test_dir), 'Empty Directory')

        self.assertEqual(result, '  ✗ Empty Directory')


if __name__ == '__main__':
    unittest.main()
