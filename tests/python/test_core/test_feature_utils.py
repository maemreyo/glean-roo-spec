"""
Comprehensive Test Suite for feature_utils.py

This module tests the feature creation utility functions in .zo/scripts/python/feature_utils.py
including repository detection, branch number management, branch name generation, and git operations.

Test Classes:
    TestRepositoryDetection: Tests for git operations and repository root finding
    TestBranchNumberManagement: Tests for branch number detection and validation
    TestBranchNameGeneration: Tests for branch name generation and cleaning
    TestGitOperations: Tests for git branch creation
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / '.zo' / 'scripts' / 'python'))

from feature_utils import (
    run_git_command,
    has_git,
    find_repo_root,
    get_repo_root,
    get_highest_from_specs,
    get_highest_from_branches,
    check_existing_branches,
    clean_branch_name,
    generate_branch_name,
    truncate_branch_name,
    create_git_branch,
    STOP_WORDS,
    MAX_BRANCH_LENGTH
)


class TestRepositoryDetection(unittest.TestCase):
    """
    Test repository detection and git availability checks.
    
    Tests run_git_command(), has_git(), find_repo_root(), and get_repo_root()
    with various scenarios including git repositories and non-git environments.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.original_dir = os.getcwd()

    def tearDown(self):
        """Clean up after tests."""
        os.chdir(self.original_dir)

    @patch('feature_utils.subprocess.run')
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
        self.assertEqual(call_args[1]['timeout'], 30)
        self.assertTrue(call_args[1]['capture_output'])
        self.assertTrue(call_args[1]['text'])

    @patch('feature_utils.subprocess.run')
    def test_run_git_command_with_cwd(self, mock_run):
        """
        Test that run_git_command accepts custom working directory.
        
        Given: A git command with a specific working directory
        When: The command is executed
        Then: The command is run in the specified directory
        """
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='output',
            stderr=''
        )

        result = run_git_command(['status'], cwd='/custom/path')

        self.assertEqual(result, 'output')
        call_args = mock_run.call_args
        self.assertEqual(call_args[1]['cwd'], '/custom/path')

    @patch('feature_utils.subprocess.run')
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

    @patch('feature_utils.subprocess.run')
    def test_run_git_command_timeout_returns_none(self, mock_run):
        """
        Test that run_git_command returns None on timeout.
        
        Given: A git command that times out
        When: The command is executed
        Then: None is returned
        """
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('git', 30)

        result = run_git_command(['status'])

        self.assertIsNone(result)

    @patch('feature_utils.subprocess.run')
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

    @patch('feature_utils.run_git_command')
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
        mock_run_git.assert_called_once_with(['rev-parse', '--show-toplevel'], cwd=None)

    @patch('feature_utils.run_git_command')
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

    @patch('feature_utils.run_git_command')
    def test_has_git_with_custom_repo_root(self, mock_run_git):
        """
        Test that has_git accepts custom repository root.
        
        Given: A custom repository root path
        When: has_git is called with repo_root parameter
        Then: The git command is run in the specified directory
        """
        mock_run_git.return_value = '/custom/repo'

        result = has_git(repo_root='/custom/repo')

        self.assertTrue(result)
        mock_run_git.assert_called_once_with(['rev-parse', '--show-toplevel'], cwd='/custom/repo')

    def test_find_repo_root_with_git_directory(self):
        """
        Test find_repo_root finds repository with .git directory.
        
        Given: A directory structure with .git directory
        When: find_repo_root is called from within the repository
        Then: The path containing .git is returned
        """
        # Create a temporary directory with .git
        with tempfile.TemporaryDirectory(prefix='test_repo_') as temp_dir:
            repo_path = Path(temp_dir) / 'project'
            repo_path.mkdir()
            (repo_path / '.git').mkdir()

            # Change to a subdirectory
            subdir = repo_path / 'subdir'
            subdir.mkdir()
            os.chdir(subdir)

            result = find_repo_root(str(subdir))

            # Compare resolved paths (macOS uses symlinks for /var)
            self.assertEqual(result, str(repo_path.resolve()))

    def test_find_repo_root_with_zo_directory(self):
        """
        Test find_repo_root finds repository with .zo directory.
        
        Given: A directory structure with .zo directory (no .git)
        When: find_repo_root is called from within the repository
        Then: The path containing .zo is returned
        """
        # Create a temporary directory with .zo
        with tempfile.TemporaryDirectory(prefix='test_repo_') as temp_dir:
            repo_path = Path(temp_dir) / 'project'
            repo_path.mkdir()
            (repo_path / '.zo').mkdir()

            # Change to a subdirectory
            subdir = repo_path / 'subdir'
            subdir.mkdir()
            os.chdir(subdir)

            result = find_repo_root(str(subdir))

            # Compare resolved paths (macOS uses symlinks for /var)
            self.assertEqual(result, str(repo_path.resolve()))

    def test_find_repo_root_not_found(self):
        """
        Test find_repo_root returns None when no repository marker found.
        
        Given: A directory without .git or .zo directories
        When: find_repo_root is called
        Then: None is returned
        """
        # Create a temporary directory without .git or .zo
        with tempfile.TemporaryDirectory(prefix='test_no_repo_') as temp_dir:
            result = find_repo_root(temp_dir)

            self.assertIsNone(result)

    def test_find_repo_root_with_defaults_to_cwd(self):
        """
        Test find_repo_root uses current directory when start_dir is None.
        
        Given: In a directory with .git or .zo
        When: find_repo_root is called without start_dir parameter
        Then: The repository root is found from current directory
        """
        with tempfile.TemporaryDirectory(prefix='test_repo_') as temp_dir:
            repo_path = Path(temp_dir) / 'project'
            repo_path.mkdir()
            (repo_path / '.git').mkdir()

            os.chdir(repo_path)

            result = find_repo_root()

            # Compare resolved paths (macOS uses symlinks for /var)
            self.assertEqual(result, str(repo_path.resolve()))

    @patch('feature_utils.find_repo_root')
    def test_get_repo_root_success(self, mock_find):
        """
        Test get_repo_root returns repository root when found.
        
        Given: A repository can be found from script location
        When: get_repo_root is called
        Then: The repository root path is returned
        """
        mock_find.return_value = '/path/to/repo'

        result = get_repo_root()

        self.assertEqual(result, '/path/to/repo')

    @patch('feature_utils.find_repo_root')
    @patch('feature_utils.sys.exit')
    def test_get_repo_root_exits_when_not_found(self, mock_exit, mock_find):
        """
        Test get_repo_root exits when repository root cannot be found.
        
        Given: No repository root can be determined
        When: get_repo_root is called
        Then: The function prints error and exits with code 1
        """
        mock_find.return_value = None

        get_repo_root()

        mock_exit.assert_called_once_with(1)


class TestBranchNumberManagement(unittest.TestCase):
    """
    Test branch number detection and validation functions.
    
    Tests get_highest_from_specs(), get_highest_from_branches(), and
    check_existing_branches() with various scenarios.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp(prefix='test_branch_numbers_')

    def tearDown(self):
        """Clean up temporary directories."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_get_highest_from_specs_with_numbered_directories(self):
        """
        Test get_highest_from_specs returns highest number from spec directories.
        
        Given: A specs directory with numbered feature directories (001-, 002-, etc.)
        When: get_highest_from_specs is called
        Then: The highest numeric prefix is returned
        """
        # Create specs directory with numbered features
        specs_dir = Path(self.temp_dir) / 'specs'
        specs_dir.mkdir()
        (specs_dir / '001-first-feature').mkdir()
        (specs_dir / '003-third-feature').mkdir()
        (specs_dir / '002-second-feature').mkdir()

        result = get_highest_from_specs(str(specs_dir))

        self.assertEqual(result, 3)

    def test_get_highest_from_specs_with_leading_zeros(self):
        """
        Test get_highest_from_specs handles leading zeros correctly.
        
        Given: Spec directories with leading zeros (001, 002, 003)
        When: get_highest_from_specs is called
        Then: Numbers are parsed as decimal (not octal)
        """
        specs_dir = Path(self.temp_dir) / 'specs'
        specs_dir.mkdir()
        (specs_dir / '001-feature').mkdir()
        (specs_dir / '008-feature').mkdir()  # Would be invalid octal
        (specs_dir / '010-feature').mkdir()

        result = get_highest_from_specs(str(specs_dir))

        self.assertEqual(result, 10)

    def test_get_highest_from_specs_empty_directory(self):
        """
        Test get_highest_from_specs returns 0 for empty directory.
        
        Given: An empty specs directory
        When: get_highest_from_specs is called
        Then: 0 is returned
        """
        specs_dir = Path(self.temp_dir) / 'specs'
        specs_dir.mkdir()

        result = get_highest_from_specs(str(specs_dir))

        self.assertEqual(result, 0)

    def test_get_highest_from_specs_nonexistent_directory(self):
        """
        Test get_highest_from_specs returns 0 for non-existent directory.
        
        Given: A specs directory path that does not exist
        When: get_highest_from_specs is called
        Then: 0 is returned
        """
        result = get_highest_from_specs('/nonexistent/specs')

        self.assertEqual(result, 0)

    def test_get_highest_from_specs_ignores_non_numbered_directories(self):
        """
        Test get_highest_from_specs ignores directories without numeric prefix.
        
        Given: A specs directory with mixed numbered and non-numbered directories
        When: get_highest_from_specs is called
        Then: Only numbered directories are considered
        """
        specs_dir = Path(self.temp_dir) / 'specs'
        specs_dir.mkdir()
        (specs_dir / '001-feature').mkdir()
        (specs_dir / 'random-dir').mkdir()
        (specs_dir / '005-feature').mkdir()
        (specs_dir / 'another-dir').mkdir()

        result = get_highest_from_specs(str(specs_dir))

        self.assertEqual(result, 5)

    @patch('feature_utils.run_git_command')
    def test_get_highest_from_branches_with_feature_branches(self, mock_run_git):
        """
        Test get_highest_from_branches returns highest number from git branches.
        
        Given: Git branches with numeric prefixes (001-, 002-, etc.)
        When: get_highest_from_branches is called
        Then: The highest numeric prefix is returned
        """
        mock_run_git.return_value = '''  main
* 001-first-feature
  003-third-feature
  002-second-feature
  remotes/origin/004-remote-feature'''

        result = get_highest_from_branches()

        self.assertEqual(result, 4)

    @patch('feature_utils.run_git_command')
    def test_get_highest_from_branches_empty(self, mock_run_git):
        """
        Test get_highest_from_branches returns 0 when no branches found.
        
        Given: No feature branches exist
        When: get_highest_from_branches is called
        Then: 0 is returned
        """
        mock_run_git.return_value = '  main\n* develop'

        result = get_highest_from_branches()

        self.assertEqual(result, 0)

    @patch('feature_utils.run_git_command')
    def test_get_highest_from_branches_no_git_output(self, mock_run_git):
        """
        Test get_highest_from_branches returns 0 when git command fails.
        
        Given: Git command returns None (failure)
        When: get_highest_from_branches is called
        Then: 0 is returned
        """
        mock_run_git.return_value = None

        result = get_highest_from_branches()

        self.assertEqual(result, 0)

    @patch('feature_utils.run_git_command')
    def test_get_highest_from_branches_handles_remotes(self, mock_run_git):
        """
        Test get_highest_from_branches correctly parses remote branches.
        
        Given: Both local and remote feature branches
        When: get_highest_from_branches is called
        Then: The highest number from all branches is returned
        """
        mock_run_git.return_value = '''  main
* 001-local
  remotes/origin/002-remote
  remotes/upstream/005-upstream'''

        result = get_highest_from_branches()

        self.assertEqual(result, 5)

    @patch('feature_utils.get_highest_from_specs')
    @patch('feature_utils.get_highest_from_branches')
    @patch('feature_utils.run_git_command')
    def test_check_existing_branches_returns_next_number(self, mock_run_git, mock_highest_branches, mock_highest_specs):
        """
        Test check_existing_branches returns next available feature number.
        
        Given: Existing specs and branches with numbers up to 5
        When: check_existing_branches is called
        Then: 6 is returned (max + 1)
        """
        mock_highest_branches.return_value = 5
        mock_highest_specs.return_value = 3

        result = check_existing_branches('/path/to/specs')

        self.assertEqual(result, 6)

    @patch('feature_utils.get_highest_from_specs')
    @patch('feature_utils.get_highest_from_branches')
    @patch('feature_utils.run_git_command')
    def test_check_existing_branches_fetches_remotes(self, mock_run_git, mock_highest_branches, mock_highest_specs):
        """
        Test check_existing_branches fetches all remotes before checking.
        
        Given: check_existing_branches is called
        When: The function executes
        Then: Git fetch --all --prune is called first
        """
        mock_highest_branches.return_value = 1
        mock_highest_specs.return_value = 1

        check_existing_branches('/path/to/specs')

        # Check that fetch was called
        fetch_calls = [call for call in mock_run_git.call_args_list
                      if len(call[0]) > 0 and 'fetch' in call[0][0]]
        self.assertTrue(len(fetch_calls) > 0)

    @patch('feature_utils.get_highest_from_specs')
    @patch('feature_utils.get_highest_from_branches')
    @patch('feature_utils.run_git_command')
    def test_check_existing_branches_with_relative_path(self, mock_run_git, mock_highest_branches, mock_highest_specs):
        """
        Test check_existing_branches handles relative specs path.
        
        Given: A relative path to specs directory
        When: check_existing_branches is called
        Then: The path is resolved correctly
        """
        mock_highest_branches.return_value = 0
        mock_highest_specs.return_value = 0

        # Create actual specs directory
        specs_dir = Path(self.temp_dir) / 'specs'
        specs_dir.mkdir()

        # Change to temp directory
        original_dir = os.getcwd()
        os.chdir(self.temp_dir)

        try:
            result = check_existing_branches('specs')
            self.assertEqual(result, 1)  # 0 + 1
        finally:
            os.chdir(original_dir)


class TestBranchNameGeneration(unittest.TestCase):
    """
    Test branch name generation and cleaning functions.
    
    Tests clean_branch_name(), generate_branch_name(), and truncate_branch_name()
    with various inputs including edge cases and stop words.
    """

    def test_clean_branch_name_lowercase(self):
        """
        Test clean_branch_name converts to lowercase.
        
        Given: A branch name with uppercase letters
        When: clean_branch_name is called
        Then: All letters are converted to lowercase
        """
        result = clean_branch_name('TEST-Feature-Name')

        self.assertEqual(result, 'test-feature-name')

    def test_clean_branch_name_replaces_special_chars(self):
        """
        Test clean_branch_name replaces special characters with hyphens.
        
        Given: A branch name with special characters
        When: clean_branch_name is called
        Then: Each special character is replaced with a hyphen
        """
        result = clean_branch_name('test@feature#name$with%special')

        self.assertEqual(result, 'test-feature-name-with-special')

    def test_clean_branch_name_trims_hyphens(self):
        """
        Test clean_branch_name trims leading and trailing hyphens.
        
        Given: A branch name with leading/trailing hyphens or special chars
        When: clean_branch_name is called
        Then: Leading and trailing hyphens are removed
        """
        result = clean_branch_name('---test---feature---')

        # Note: The function doesn't collapse consecutive hyphens, only trims
        self.assertEqual(result, 'test---feature')

    def test_clean_branch_name_consecutive_special_chars(self):
        """
        Test clean_branch_name handles consecutive special characters.
        
        Given: A branch name with consecutive special characters
        When: clean_branch_name is called
        Then: Each special character becomes a hyphen (no collapsing)
        """
        result = clean_branch_name('test!!!feature')

        self.assertEqual(result, 'test---feature')

    def test_clean_branch_name_preserves_alphanumeric(self):
        """
        Test clean_branch_name preserves alphanumeric characters.
        
        Given: A branch name with alphanumeric characters
        When: clean_branch_name is called
        Then: Alphanumeric characters are preserved
        """
        result = clean_branch_name('test123feature456')

        self.assertEqual(result, 'test123feature456')

    def test_clean_branch_name_empty_string(self):
        """
        Test clean_branch_name handles empty string.
        
        Given: An empty string
        When: clean_branch_name is called
        Then: An empty string is returned
        """
        result = clean_branch_name('')

        self.assertEqual(result, '')

    def test_generate_branch_name_filters_stop_words(self):
        """
        Test generate_branch_name filters out stop words.
        
        Given: A description containing common stop words
        When: generate_branch_name is called
        Then: Stop words are filtered from the result
        """
        result = generate_branch_name('I want to add a new feature')

        # Stop words filtered: 'i', 'want', 'to', 'add', 'a'
        # 'new' and 'feature' remain (note: 'new' is NOT in stop words)
        self.assertEqual(result, 'new-feature')

    def test_generate_branch_name_uses_meaningful_words(self):
        """
        Test generate_branch_name uses first 3-4 meaningful words.
        
        Given: A description with multiple meaningful words
        When: generate_branch_name is called
        Then: The first 3 meaningful words are used
        """
        result = generate_branch_name('Implement user authentication system with OAuth')

        self.assertIn('user', result)
        self.assertIn('authentication', result)

    def test_generate_branch_name_with_acronyms(self):
        """
        Test generate_branch_name preserves short uppercase acronyms.
        
        Given: A description with short uppercase words
        When: generate_branch_name is called
        Then: Short uppercase words are preserved as acronyms
        """
        result = generate_branch_name('Add API support for JSON and XML')

        # Should preserve API and JSON as they're uppercase
        self.assertIn('api', result.lower())

    def test_generate_branch_name_fallback_to_cleaned(self):
        """
        Test generate_branch_name falls back to cleaned description when no meaningful words.
        
        Given: A description with only stop words
        When: generate_branch_name is called
        Then: A cleaned version of the description is returned
        """
        result = generate_branch_name('I want the')

        # Should fallback to cleaned description
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_generate_branch_name_with_four_meaningful_words(self):
        """
        Test generate_branch_name uses 4 words when exactly 4 available.
        
        Given: A description with exactly 4 meaningful words
        When: generate_branch_name is called
        Then: All 4 meaningful words are used
        """
        result = generate_branch_name('Implement user authentication system with')

        # Should use 4 words when exactly 4 meaningful words exist
        words = result.split('-')
        self.assertEqual(len(words), 4)

    def test_generate_branch_name_with_more_than_four_words(self):
        """
        Test generate_branch_name limits to 3 words when more than 4 available.
        
        Given: A description with more than 4 meaningful words
        When: generate_branch_name is called
        Then: Only the first 3 meaningful words are used
        """
        result = generate_branch_name('Implement user authentication system with OAuth provider support')

        # Should limit to 3 words when more than 4 available
        words = result.split('-')
        self.assertLessEqual(len(words), 3)

    def test_generate_branch_name_handles_special_characters(self):
        """
        Test generate_branch_name handles descriptions with special characters.
        
        Given: A description with punctuation and special characters
        When: generate_branch_name is called
        Then: Special characters are handled properly
        """
        result = generate_branch_name('Add user-friendly, fast interface!')

        self.assertIsInstance(result, str)
        self.assertNotIn(',', result)
        self.assertNotIn('!', result)

    def test_truncate_branch_name_within_limit(self):
        """
        Test truncate_branch_name returns original when within limit.
        
        Given: A branch name within GitHub's 244-byte limit
        When: truncate_branch_name is called
        Then: The original branch name is returned unchanged
        """
        short_name = '001-short-branch'

        with patch('feature_utils.sys.stderr'):
            result = truncate_branch_name(short_name)

        self.assertEqual(result, short_name)

    def test_truncate_branch_name_exceeds_limit(self):
        """
        Test truncate_branch_name truncates when exceeding limit.
        
        Given: A branch name exceeding GitHub's 244-byte limit
        When: truncate_branch_name is called
        Then: The branch name is truncated and warning is printed
        """
        # Create a very long branch name
        long_suffix = 'a' * 300
        long_name = f'001-{long_suffix}'

        with patch('feature_utils.sys.stderr'):
            result = truncate_branch_name(long_name)

        # Should be truncated
        self.assertLess(len(result.encode('utf-8')), MAX_BRANCH_LENGTH + 1)
        self.assertTrue(result.startswith('001-'))

    def test_truncate_branch_name_preserves_prefix(self):
        """
        Test truncate_branch_name preserves numeric prefix.
        
        Given: A branch name that needs truncation
        When: truncate_branch_name is called
        Then: The numeric prefix (e.g., '001-') is preserved
        """
        long_suffix = 'b' * 300
        long_name = f'123-{long_suffix}'

        with patch('feature_utils.sys.stderr'):
            result = truncate_branch_name(long_name)

        self.assertTrue(result.startswith('123-'))

    def test_truncate_branch_name_removes_trailing_hyphen(self):
        """
        Test truncate_branch_name removes trailing hyphen after truncation.
        
        Given: A branch name that truncates at a hyphen boundary
        When: truncate_branch_name is called
        Then: Trailing hyphen is removed
        """
        # Create a name that will truncate at a hyphen
        long_suffix = 'word-' + 'c' * 250
        long_name = f'001-{long_suffix}'

        with patch('feature_utils.sys.stderr'):
            result = truncate_branch_name(long_name)

        # Should not end with hyphen
        self.assertFalse(result.endswith('-'))

    def test_truncate_branch_name_with_multibyte_characters(self):
        """
        Test truncate_branch_name handles multibyte UTF-8 characters.
        
        Given: A branch name with multibyte UTF-8 characters
        When: truncate_branch_name is called
        Then: Byte length is correctly calculated and truncated
        """
        # Use emoji which are multibyte
        long_suffix = '😀' * 100  # Each emoji is 4 bytes in UTF-8
        long_name = f'001-{long_suffix}'

        with patch('feature_utils.sys.stderr'):
            result = truncate_branch_name(long_name)

        # Should be within byte limit
        self.assertLessEqual(len(result.encode('utf-8')), MAX_BRANCH_LENGTH)


class TestGitOperations(unittest.TestCase):
    """
    Test git branch creation operations.
    
    Tests create_git_branch() with various scenarios including
    success, failure, and missing git.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp(prefix='test_git_ops_')

    def tearDown(self):
        """Clean up temporary directories."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('feature_utils.has_git')
    @patch('feature_utils.run_git_command')
    def test_create_git_branch_success(self, mock_run_git, mock_has_git):
        """
        Test create_git_branch creates branch successfully.
        
        Given: A git repository and valid branch name
        When: create_git_branch is called
        Then: Branch is created and True is returned
        """
        mock_has_git.return_value = True
        mock_run_git.return_value = ''

        result = create_git_branch('001-test-feature', self.temp_dir)

        self.assertTrue(result)
        mock_run_git.assert_called_once_with(['checkout', '-b', '001-test-feature'], cwd=self.temp_dir)

    @patch('feature_utils.has_git')
    def test_create_git_branch_no_git(self, mock_has_git):
        """
        Test create_git_branch handles missing git gracefully.
        
        Given: No git repository available
        When: create_git_branch is called
        Then: Warning is printed and False is returned
        """
        mock_has_git.return_value = False

        with patch('feature_utils.sys.stderr'):
            result = create_git_branch('001-test-feature', self.temp_dir)

        self.assertFalse(result)

    @patch('feature_utils.has_git')
    @patch('feature_utils.run_git_command')
    def test_create_git_branch_command_fails(self, mock_run_git, mock_has_git):
        """
        Test create_git_branch handles command failure.
        
        Given: Git checkout command fails
        When: create_git_branch is called
        Then: False is returned
        """
        mock_has_git.return_value = True
        mock_run_git.return_value = None  # Indicates failure

        result = create_git_branch('001-test-feature', self.temp_dir)

        self.assertFalse(result)

    @patch('feature_utils.has_git')
    @patch('feature_utils.run_git_command')
    def test_create_git_branch_with_complex_name(self, mock_run_git, mock_has_git):
        """
        Test create_git_branch with complex branch name.
        
        Given: A branch name with multiple words and special characters
        When: create_git_branch is called
        Then: Branch is created with the exact name provided
        """
        mock_has_git.return_value = True
        mock_run_git.return_value = ''

        branch_name = '001-add-user-authentication-with-oauth'
        result = create_git_branch(branch_name, self.temp_dir)

        self.assertTrue(result)
        mock_run_git.assert_called_once_with(['checkout', '-b', branch_name], cwd=self.temp_dir)


if __name__ == '__main__':
    unittest.main()
