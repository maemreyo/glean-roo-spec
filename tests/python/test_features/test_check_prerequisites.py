"""
Test suite for check-prerequisites.py script.

This module tests the check-prerequisites.py script which validates
workflow prerequisites for Spec-Driven Development.

Test Classes:
    TestFormatFunctions: Tests JSON formatting functions
    TestCheckFileStatus: Tests file status checking
    TestCheckDirStatus: Tests directory status checking
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


class TestFormatFunctions(unittest.TestCase):
    """Test JSON formatting functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Import functions to test
        with patch('sys.argv', ['check-prerequisites.py']):
            from check_prerequisites import format_json_paths, format_json_result
            self.format_json_paths = format_json_paths
            self.format_json_result = format_json_result

    def test_format_json_paths(self):
        """Test formatting paths as JSON."""
        # Arrange
        paths = {
            'REPO_ROOT': '/path/to/repo',
            'CURRENT_BRANCH': '001-test-feature',
            'FEATURE_DIR': '/path/to/repo/specs/001-test-feature',
            'FEATURE_SPEC': '/path/to/repo/specs/001-test-feature/spec.md',
            'IMPL_PLAN': '/path/to/repo/specs/001-test-feature/plan.md',
            'TASKS': '/path/to/repo/specs/001-test-feature/tasks.md',
        }
        
        # Act
        result = self.format_json_paths(paths)
        
        # Assert
        data = json.loads(result)
        self.assertEqual(data['REPO_ROOT'], '/path/to/repo')
        self.assertEqual(data['CURRENT_BRANCH'], '001-test-feature')
        self.assertEqual(data['FEATURE_DIR'], '/path/to/repo/specs/001-test-feature')
        # Verify compact JSON (no spaces)
        self.assertNotIn(' ', result)

    def test_format_json_result(self):
        """Test formatting result as JSON."""
        # Arrange
        feature_dir = '/path/to/specs/001-feature'
        available_docs = ['research.md', 'data-model.md', 'design.md']
        
        # Act
        result = self.format_json_result(feature_dir, available_docs)
        
        # Assert
        data = json.loads(result)
        self.assertEqual(data['FEATURE_DIR'], feature_dir)
        self.assertEqual(data['AVAILABLE_DOCS'], available_docs)
        # Verify compact JSON
        self.assertNotIn(' ', result)

    def test_format_json_result_with_empty_docs(self):
        """Test formatting result with no available documents."""
        # Act
        result = self.format_json_result('/path/to/feature', [])
        
        # Assert
        data = json.loads(result)
        self.assertEqual(data['AVAILABLE_DOCS'], [])


class TestCheckFileStatus(TempDirectoryFixture):
    """Test file status checking functions."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Import function to test
        with patch('sys.argv', ['check-prerequisites.py']):
            from check_prerequisites import check_file_status
            self.check_file_status = check_file_status

    def test_check_file_status_exists(self):
        """Test check_file_status returns checkmark for existing file."""
        # Arrange
        test_file = self.create_file('test.md', 'content')
        
        # Act
        result = self.check_file_status(test_file, 'test.md')
        
        # Assert
        self.assertIn('✓', result)
        self.assertIn('test.md', result)

    def test_check_file_status_not_exists(self):
        """Test check_file_status returns cross for non-existing file."""
        # Act
        result = self.check_file_status('/nonexistent/file.md', 'file.md')
        
        # Assert
        self.assertIn('✗', result)
        self.assertIn('file.md', result)


class TestCheckDirStatus(TempDirectoryFixture):
    """Test directory status checking functions."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Import function to test
        with patch('sys.argv', ['check-prerequisites.py']):
            from check_prerequisites import check_dir_status
            self.check_dir_status = check_dir_status

    def test_check_dir_status_with_files(self):
        """Test check_dir_status returns checkmark for directory with files."""
        # Arrange
        dir_path = self.create_directory('contracts')
        self.create_file('contracts/test.md', 'content')
        
        # Act
        result = self.check_dir_status(dir_path, 'contracts/')
        
        # Assert
        self.assertIn('✓', result)
        self.assertIn('contracts/', result)

    def test_check_dir_status_empty(self):
        """Test check_dir_status returns cross for empty directory."""
        # Arrange
        dir_path = self.create_directory('empty_dir')
        
        # Act
        result = self.check_dir_status(dir_path, 'empty_dir/')
        
        # Assert
        self.assertIn('✗', result)

    def test_check_dir_status_not_exists(self):
        """Test check_dir_status returns cross for non-existing directory."""
        # Act
        result = self.check_dir_status('/nonexistent/dir', 'dir/')
        
        # Assert
        self.assertIn('✗', result)


class TestScriptExecution(TempDirectoryFixture):
    """Test end-to-end script execution."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Create required directory structure
        self.specs_dir = self.create_directory('specs')
        self.feature_dir = self.create_directory('specs/001-test-feature')
        
        # Create required plan.md
        self.create_file('specs/001-test-feature/plan.md', '# Implementation Plan\n')
        
        # Store original directory
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        super().tearDown()

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_success_with_plan_only(self, mock_check_branch, mock_get_paths):
        """Test script succeeds when only plan.md exists."""
        # Arrange
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': '001-test-feature',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/001-test-feature/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/001-test-feature/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/001-test-feature/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/001-test-feature/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/001-test-feature/quickstart.md'),
            'CONTRACTS_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature/contracts'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/001-test-feature/design.md'),
        }
        mock_check_branch.return_value = (True, None)
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        self.assertIn('FEATURE_DIR:', result.stdout)
        self.assertIn('AVAILABLE_DOCS:', result.stdout)

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_json_output(self, mock_check_branch, mock_get_paths):
        """Test script outputs JSON format with --json flag."""
        # Arrange
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': '001-test-feature',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/001-test-feature/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/001-test-feature/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/001-test-feature/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/001-test-feature/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/001-test-feature/quickstart.md'),
            'CONTRACTS_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature/contracts'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/001-test-feature/design.md'),
        }
        mock_check_branch.return_value = (True, None)
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            ['--json'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        data = parse_json_output(result.stdout)
        self.assertIn('FEATURE_DIR', data)
        self.assertIn('AVAILABLE_DOCS', data)

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_with_available_docs(self, mock_check_branch, mock_get_paths):
        """Test script detects available optional documents."""
        # Arrange
        # Create optional documents
        self.create_file('specs/001-test-feature/research.md', '# Research\n')
        self.create_file('specs/001-test-feature/data-model.md', '# Data Model\n')
        
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': '001-test-feature',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/001-test-feature/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/001-test-feature/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/001-test-feature/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/001-test-feature/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/001-test-feature/quickstart.md'),
            'CONTRACTS_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature/contracts'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/001-test-feature/design.md'),
        }
        mock_check_branch.return_value = (True, None)
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            ['--json'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        data = parse_json_output(result.stdout)
        self.assertIn('research.md', data['AVAILABLE_DOCS'])
        self.assertIn('data-model.md', data['AVAILABLE_DOCS'])

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_with_tasks_required(self, mock_check_branch, mock_get_paths):
        """Test script requires tasks.md when --require-tasks is used."""
        # Arrange
        # Create tasks.md
        self.create_file('specs/001-test-feature/tasks.md', '# Tasks\n')
        
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': '001-test-feature',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/001-test-feature/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/001-test-feature/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/001-test-feature/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/001-test-feature/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/001-test-feature/quickstart.md'),
            'CONTRACTS_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature/contracts'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/001-test-feature/design.md'),
        }
        mock_check_branch.return_value = (True, None)
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            ['--require-tasks', '--json'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_fails_when_tasks_required_but_missing(self, mock_check_branch, mock_get_paths):
        """Test script fails when --require-tasks but tasks.md doesn't exist."""
        # Arrange
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': '001-test-feature',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/001-test-feature/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/001-test-feature/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/001-test-feature/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/001-test-feature/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/001-test-feature/quickstart.md'),
            'CONTRACTS_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature/contracts'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/001-test-feature/design.md'),
        }
        mock_check_branch.return_value = (True, None)
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            ['--require-tasks'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertFalse(result.success)
        self.assertIn('ERROR', result.stderr)

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_include_tasks_flag(self, mock_check_branch, mock_get_paths):
        """Test --include-tasks flag includes tasks.md in available docs."""
        # Arrange
        self.create_file('specs/001-test-feature/tasks.md', '# Tasks\n')
        
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': '001-test-feature',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/001-test-feature/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/001-test-feature/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/001-test-feature/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/001-test-feature/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/001-test-feature/quickstart.md'),
            'CONTRACTS_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature/contracts'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/001-test-feature/design.md'),
        }
        mock_check_branch.return_value = (True, None)
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            ['--include-tasks', '--json'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        data = parse_json_output(result.stdout)
        self.assertIn('tasks.md', data['AVAILABLE_DOCS'])

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_paths_only_mode(self, mock_check_branch, mock_get_paths):
        """Test --paths-only mode outputs only path variables."""
        # Arrange
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': '001-test-feature',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/001-test-feature/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/001-test-feature/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/001-test-feature/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/001-test-feature/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/001-test-feature/quickstart.md'),
            'CONTRACTS_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature/contracts'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/001-test-feature/design.md'),
        }
        mock_check_branch.return_value = (True, None)
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            ['--paths-only'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        self.assertIn('REPO_ROOT:', result.stdout)
        self.assertIn('BRANCH:', result.stdout)
        self.assertIn('FEATURE_DIR:', result.stdout)
        self.assertIn('FEATURE_SPEC:', result.stdout)
        self.assertIn('IMPL_PLAN:', result.stdout)
        self.assertIn('TASKS:', result.stdout)

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_paths_only_with_json(self, mock_check_branch, mock_get_paths):
        """Test --paths-only with --json outputs paths as JSON."""
        # Arrange
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': '001-test-feature',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/001-test-feature/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/001-test-feature/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/001-test-feature/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/001-test-feature/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/001-test-feature/quickstart.md'),
            'CONTRACTS_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature/contracts'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/001-test-feature/design.md'),
        }
        mock_check_branch.return_value = (True, None)
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            ['--paths-only', '--json'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        data = parse_json_output(result.stdout)
        self.assertIn('REPO_ROOT', data)
        self.assertIn('BRANCH', data)
        self.assertIn('FEATURE_DIR', data)
        self.assertIn('FEATURE_SPEC', data)
        self.assertIn('IMPL_PLAN', data)
        self.assertIn('TASKS', data)

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_validates_branch_pattern(self, mock_check_branch, mock_get_paths):
        """Test script validates feature branch naming pattern."""
        # Arrange
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'invalid-branch-name',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/invalid-branch-name'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/invalid-branch-name/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/invalid-branch-name/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/invalid-branch-name/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/invalid-branch-name/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/invalid-branch-name/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/invalid-branch-name/quickstart.md'),
            'CONTRACTS_DIR': os.path.join(self.temp_dir, 'specs/invalid-branch-name/contracts'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/invalid-branch-name/design.md'),
        }
        mock_check_branch.return_value = (False, 'Not on a feature branch')
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertFalse(result.success)
        self.assertIn('ERROR', result.stderr)

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_detects_contracts_directory(self, mock_check_branch, mock_get_paths):
        """Test script detects contracts/ directory with files."""
        # Arrange
        contracts_dir = self.create_directory('specs/001-test-feature/contracts')
        self.create_file('specs/001-test-feature/contracts/api.md', '# API Contract\n')
        
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': '001-test-feature',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/001-test-feature/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/001-test-feature/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/001-test-feature/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/001-test-feature/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/001-test-feature/quickstart.md'),
            'CONTRACTS_DIR': contracts_dir,
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/001-test-feature/design.md'),
        }
        mock_check_branch.return_value = (True, None)
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            ['--json'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        data = parse_json_output(result.stdout)
        self.assertIn('contracts/', data['AVAILABLE_DOCS'])

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_fails_when_feature_dir_missing(self, mock_check_branch, mock_get_paths):
        """Test script fails when feature directory doesn't exist."""
        # Arrange
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': '001-test-feature',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/001-test-feature/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/001-test-feature/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/001-test-feature/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/001-test-feature/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/001-test-feature/quickstart.md'),
            'CONTRACTS_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature/contracts'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/001-test-feature/design.md'),
        }
        mock_check_branch.return_value = (True, None)
        
        # Remove feature directory
        shutil.rmtree(os.path.join(self.temp_dir, 'specs/001-test-feature'))
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertFalse(result.success)
        self.assertIn('ERROR', result.stderr)
        self.assertIn('Feature directory not found', result.stderr)

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_fails_when_plan_missing(self, mock_check_branch, mock_get_paths):
        """Test script fails when plan.md doesn't exist."""
        # Arrange
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': '001-test-feature',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/001-test-feature/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/001-test-feature/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/001-test-feature/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/001-test-feature/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/001-test-feature/quickstart.md'),
            'CONTRACTS_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature/contracts'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/001-test-feature/design.md'),
        }
        mock_check_branch.return_value = (True, None)
        
        # Remove plan.md
        os.remove(os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'))
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertFalse(result.success)
        self.assertIn('ERROR', result.stderr)
        self.assertIn('plan.md not found', result.stderr)

    @patch('sys.exit')
    def test_script_help_flag(self, mock_exit):
        """Test --help flag displays help and exits."""
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            ['--help'],
            cwd=self.temp_dir
        )
        
        # Assert
        # Help should exit with code 0
        mock_exit.assert_called_with(0)

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_with_design_document(self, mock_check_branch, mock_get_paths):
        """Test script detects design.md document."""
        # Arrange
        self.create_file('specs/001-test-feature/design.md', '# Design\n')
        
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': '001-test-feature',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/001-test-feature/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/001-test-feature/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/001-test-feature/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/001-test-feature/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/001-test-feature/quickstart.md'),
            'CONTRACTS_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature/contracts'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/001-test-feature/design.md'),
        }
        mock_check_branch.return_value = (True, None)
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            ['--json'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        data = parse_json_output(result.stdout)
        self.assertIn('design.md', data['AVAILABLE_DOCS'])

    @patch('check_prerequisites.get_feature_paths')
    @patch('check_prerequisites.check_feature_branch')
    def test_script_with_quickstart_document(self, mock_check_branch, mock_get_paths):
        """Test script detects quickstart.md document."""
        # Arrange
        self.create_file('specs/001-test-feature/quickstart.md', '# Quick Start\n')
        
        mock_get_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': '001-test-feature',
            'HAS_GIT': 'true',
            'FEATURE_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'specs/001-test-feature/spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'specs/001-test-feature/plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'specs/001-test-feature/tasks.md'),
            'RESEARCH': os.path.join(self.temp_dir, 'specs/001-test-feature/research.md'),
            'DATA_MODEL': os.path.join(self.temp_dir, 'specs/001-test-feature/data-model.md'),
            'QUICKSTART': os.path.join(self.temp_dir, 'specs/001-test-feature/quickstart.md'),
            'CONTRACTS_DIR': os.path.join(self.temp_dir, 'specs/001-test-feature/contracts'),
            'DESIGN_FILE': os.path.join(self.temp_dir, 'specs/001-test-feature/design.md'),
        }
        mock_check_branch.return_value = (True, None)
        
        # Act
        result = run_python_script(
            str(script_dir / 'check-prerequisites.py'),
            ['--json'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        data = parse_json_output(result.stdout)
        self.assertIn('quickstart.md', data['AVAILABLE_DOCS'])


if __name__ == '__main__':
    unittest.main()
