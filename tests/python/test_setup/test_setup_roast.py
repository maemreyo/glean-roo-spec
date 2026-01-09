"""
Test Suite for setup-roast.py

This module tests the roast report initialization script.
Tests cover JSON input parsing, feature directory resolution,
roast report creation, and end-to-end script execution.

Test Classes:
    TestParseJsonInput: Test JSON input parsing from command line
    TestResolveFeatureDir: Test feature directory resolution logic
    TestCreateRoastReport: Test roast report file creation
    TestScriptExecution: Test end-to-end script execution
"""

import json
import os
import sys
import tempfile
import shutil
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

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

from file_fixtures import TempDirectoryFixture, FeatureDirectoryFixture
from assertion_helpers import assert_file_exists, assert_json_output, assert_file_contains
from output_helpers import run_python_script, parse_json_output


class TestParseJsonInput(unittest.TestCase):
    """
    Test the parse_json_input function for processing JSON input.

    Tests ensure that:
    -- --json= format is parsed correctly
    - Raw JSON objects are handled
    - --json flag without value returns empty dict
    - Invalid JSON is handled with appropriate error
    """

    def setUp(self):
        """Set up test environment."""
        # Import the module to test
        import setup_roast
        self.module = setup_roast

    def test_json_equals_format(self):
        """Test parsing --json= format with JSON data."""
        input_str = '--json={"commits":["abc123","def456"],"design_system":"/path/to/ds.md"}'
        result = self.module.parse_json_input(input_str)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['commits'], ['abc123', 'def456'])
        self.assertEqual(result['design_system'], '/path/to/ds.md')

    def test_raw_json_object(self):
        """Test parsing raw JSON object starting with {."""
        input_str = '{"commits":["abc123"],"design_system":"/ds.md"}'
        result = self.module.parse_json_input(input_str)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['commits'], ['abc123'])

    def test_json_flag_without_value(self):
        """Test --json flag without value returns empty dict."""
        result = self.module.parse_json_input('--json')
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})

    def test_json_with_commits_only(self):
        """Test JSON with only commits field."""
        input_str = '{"commits":["abc123","def456","ghi789"]}'
        result = self.module.parse_json_input(input_str)
        
        self.assertEqual(result['commits'], ['abc123', 'def456', 'ghi789'])
        self.assertNotIn('design_system', result)

    def test_json_with_design_system_only(self):
        """Test JSON with only design_system field."""
        input_str = '{"design_system":"/custom/path/design.md"}'
        result = self.module.parse_json_input(input_str)
        
        self.assertEqual(result['design_system'], '/custom/path/design.md')
        self.assertNotIn('commits', result)

    def test_invalid_json_exits(self):
        """Test that invalid JSON causes system exit."""
        input_str = '--json={invalid json}'
        
        with self.assertRaises(SystemExit) as context:
            self.module.parse_json_input(input_str)
        
        self.assertEqual(context.exception.code, 1)

    def test_empty_json_object(self):
        """Test empty JSON object."""
        input_str = '{}'
        result = self.module.parse_json_input(input_str)
        
        self.assertEqual(result, {})

    def test_json_with_multiple_commits(self):
        """Test JSON with multiple commit hashes."""
        input_str = '{"commits":["a","b","c","d","e"]}'
        result = self.module.parse_json_input(input_str)
        
        self.assertEqual(len(result['commits']), 5)
        self.assertEqual(result['commits'], ['a', 'b', 'c', 'd', 'e'])


class TestResolveFeatureDir(unittest.TestCase):
    """
    Test the resolve_feature_dir function for resolving feature directories.

    Tests ensure that:
    - Absolute paths are resolved correctly
    - Relative paths from current directory work
    - Relative paths from repo root work
    - Non-existent directories cause error
    - Feature name is extracted correctly
    """

    def setUp(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp(prefix='roast_test_')
        
        # Import the module
        import setup_roast
        self.module = setup_roast

    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_absolute_path_resolution(self):
        """Test resolving absolute path to feature directory."""
        feature_path = os.path.join(self.temp_dir, 'test-feature')
        os.makedirs(feature_path)
        
        result_dir, result_name = self.module.resolve_feature_dir(feature_path, self.temp_dir)
        
        self.assertEqual(result_dir, os.path.abspath(feature_path))
        self.assertEqual(result_name, 'test-feature')

    def test_relative_path_from_current_dir(self):
        """Test resolving relative path from current directory."""
        # Change to temp directory
        original_dir = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            feature_name = 'my-feature'
            os.makedirs(feature_name)
            
            result_dir, result_name = self.module.resolve_feature_dir(feature_name, self.temp_dir)
            
            self.assertTrue(os.path.isabs(result_dir))
            self.assertEqual(result_name, 'my-feature')
        finally:
            os.chdir(original_dir)

    def test_relative_path_from_repo_root(self):
        """Test resolving relative path from repository root."""
        feature_name = 'repo-feature'
        feature_path = os.path.join(self.temp_dir, feature_name)
        os.makedirs(feature_path)
        
        # Use just the feature name (relative to repo root)
        result_dir, result_name = self.module.resolve_feature_dir(feature_name, self.temp_dir)
        
        self.assertIn(feature_name, result_dir)
        self.assertEqual(result_name, 'repo-feature')

    def test_nonexistent_directory_exits(self):
        """Test that non-existent directory causes system exit."""
        nonexistent = 'nonexistent-feature'
        
        with self.assertRaises(SystemExit) as context:
            self.module.resolve_feature_dir(nonexistent, self.temp_dir)
        
        self.assertEqual(context.exception.code, 1)

    def test_feature_name_extraction(self):
        """Test that feature name is extracted correctly from path."""
        feature_path = os.path.join(self.temp_dir, '001-my-awesome-feature')
        os.makedirs(feature_path)
        
        result_dir, result_name = self.module.resolve_feature_dir(feature_path, self.temp_dir)
        
        self.assertEqual(result_name, '001-my-awesome-feature')

    def test_nested_feature_directory(self):
        """Test resolving nested feature directory."""
        nested_path = os.path.join(self.temp_dir, 'features', '001-test')
        os.makedirs(nested_path)
        
        result_dir, result_name = self.module.resolve_feature_dir(nested_path, self.temp_dir)
        
        self.assertEqual(result_name, '001-test')
        self.assertTrue(os.path.isabs(result_dir))


class TestCreateRoastReport(TempDirectoryFixture):
    """
    Test the create_roast_report function for roast report file creation.

    Tests ensure that:
    - Template is copied to report location
    - Metadata is appended when JSON data provided
    - Missing templates create empty file
    - Commits and design system are written correctly
    """

    def setUp(self):
        """Set up test environment with temporary directory."""
        super().setUp()
        
        # Import the module
        import setup_roast
        self.module = setup_roast

    def test_copies_template_to_report(self):
        """Test that template is copied to report file."""
        # Create template
        template_content = "# Roast Report Template\n\n## Review Points\n\n"
        template_path = self.create_file('.zo/templates/roast-template.md', template_content)
        
        # Create report
        report_path = os.path.join(self.temp_dir, 'roasts', 'test-report.md')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        json_data = {}
        self.module.create_roast_report(report_path, template_path, json_data)
        
        # Verify file exists and has template content
        assert_file_exists(report_path, expected_content='Roast Report Template')

    def test_appends_commits_metadata(self):
        """Test that commits metadata is appended to report."""
        template_content = "# Roast Report"
        template_path = self.create_file('.zo/templates/roast-template.md', template_content)
        
        report_path = os.path.join(self.temp_dir, 'roasts', 'test-report.md')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        json_data = {'commits': ['abc123', 'def456', 'ghi789']}
        self.module.create_roast_report(report_path, template_path, json_data)
        
        # Check that metadata is appended
        with open(report_path, 'r') as f:
            content = f.read()
        
        self.assertIn('<!--', content)
        self.assertIn('-->', content)
        self.assertIn('Commits: abc123,def456,ghi789', content)

    def test_appends_design_system_metadata(self):
        """Test that design system metadata is appended to report."""
        template_content = "# Roast Report"
        template_path = self.create_file('.zo/templates/roast-template.md', template_content)
        
        report_path = os.path.join(self.temp_dir, 'roasts', 'test-report.md')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        json_data = {'design_system': '/path/to/design-system.md'}
        self.module.create_roast_report(report_path, template_path, json_data)
        
        # Check that metadata is appended
        with open(report_path, 'r') as f:
            content = f.read()
        
        self.assertIn('Design System: /path/to/design-system.md', content)

    def test_appends_both_commits_and_design_system(self):
        """Test that both commits and design system are appended."""
        template_content = "# Roast Report"
        template_path = self.create_file('.zo/templates/roast-template.md', template_content)
        
        report_path = os.path.join(self.temp_dir, 'roasts', 'test-report.md')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        json_data = {
            'commits': ['abc123'],
            'design_system': '/ds.md'
        }
        self.module.create_roast_report(report_path, template_path, json_data)
        
        # Check both are present
        with open(report_path, 'r') as f:
            content = f.read()
        
        self.assertIn('Commits: abc123', content)
        self.assertIn('Design System: /ds.md', content)

    def test_missing_template_creates_empty_file(self):
        """Test that missing template creates empty file."""
        template_path = os.path.join(self.temp_dir, 'nonexistent', 'template.md')
        
        report_path = os.path.join(self.temp_dir, 'roasts', 'test-report.md')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        json_data = {}
        
        # Capture stderr to check for warning
        with patch('sys.stderr', new_callable=MagicMock) as mock_stderr:
            self.module.create_roast_report(report_path, template_path, json_data)
            
            # Check warning was printed
            self.assertTrue(mock_stderr.write.called)
        
        # File should exist
        assert_file_exists(report_path)
        
        # File should be empty (or just have metadata if provided)
        with open(report_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content, '')

    def test_no_metadata_when_json_empty(self):
        """Test that no metadata is appended when JSON data is empty."""
        template_content = "# Roast Report"
        template_path = self.create_file('.zo/templates/roast-template.md', template_content)
        
        report_path = os.path.join(self.temp_dir, 'roasts', 'test-report.md')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        json_data = {}
        self.module.create_roast_report(report_path, template_path, json_data)
        
        # Check no metadata block
        with open(report_path, 'r') as f:
            content = f.read()
        
        self.assertNotIn('<!--', content)
        self.assertNotIn('-->', content)

    def test_single_commit_formatting(self):
        """Test that single commit is formatted correctly."""
        template_content = "# Roast Report"
        template_path = self.create_file('.zo/templates/roast-template.md', template_content)
        
        report_path = os.path.join(self.temp_dir, 'roasts', 'test-report.md')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        json_data = {'commits': ['single-commit']}
        self.module.create_roast_report(report_path, template_path, json_data)
        
        # Check format
        with open(report_path, 'r') as f:
            content = f.read()
        
        self.assertIn('Commits: single-commit', content)


class TestScriptExecution(TempDirectoryFixture, FeatureDirectoryFixture):
    """
    Test end-to-end execution of setup-roast.py.

    Tests ensure that:
    - Roast directory is created inside feature directory
    - Report file follows naming pattern with timestamp
    - JSON and text output formats work
    - Main/master branch special handling works
    - Feature directory resolution from argument and branch
    - Default design system path is used when not provided
    """

    def setUp(self):
        """Set up test environment with temporary directory."""
        super().setUp()
        
        # Import the module
        import setup_roast
        self.module = setup_roast
        
        # Create .zo directory structure
        self.zo_dir = self.create_directory('.zo')
        self.templates_dir = self.create_directory('.zo/templates')
        
        # Create roast template
        self.template_content = """# Roast Report: {{FEATURE_NAME}}

Date: {{DATE}}

## Review Checklist
- [ ] Code quality
- [ ] Test coverage
- [ ] Documentation
"""
        self.template_path = self.create_file(
            '.zo/templates/roast-template.md',
            self.template_content
        )
        
        # Create design system file
        self.design_system_content = "# Design System\n\n## Colors\n\n..."
        self.design_system_path = self.create_file(
            '.zo/design-system.md',
            self.design_system_content
        )

    @patch('setup_roast.get_feature_paths')
    def test_creates_roast_directory_in_feature_folder(self, mock_get_feature_paths):
        """Test that roasts directory is created inside feature folder."""
        # Create feature directory
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        
        # Mock get_feature_paths to return our test directory
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(feature_dir, 'plan.md'),
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast.py']):
            self.module.main()
        
        # Check roasts directory was created
        roasts_dir = os.path.join(feature_dir, 'roasts')
        self.assertTrue(os.path.isdir(roasts_dir))

    @patch('setup_roast.get_feature_paths')
    def test_report_file_naming_pattern(self, mock_get_feature_paths):
        """Test that report file follows naming pattern."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(feature_dir, 'plan.md'),
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast.py']):
            self.module.main()
        
        # Check report file was created with correct pattern
        roasts_dir = os.path.join(feature_dir, 'roasts')
        files = os.listdir(roasts_dir)
        self.assertEqual(len(files), 1)
        
        filename = files[0]
        # Pattern: roast-report-FEATURE_NAME-YYYY-MM-DD-HHMM.md
        self.assertTrue(filename.startswith('roast-report-feature/001-test-feature-'))
        self.assertTrue(filename.endswith('.md'))

    @patch('setup_roast.get_feature_paths')
    def test_json_output_format(self, mock_get_feature_paths):
        """Test JSON output format."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(feature_dir, 'plan.md'),
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast.py', '--json']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                # Get output
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                
                # Parse JSON
                data = json.loads(output)
                self.assertIn('REPORT_FILE', data)
                self.assertIn('TASKS', data)
                self.assertIn('IMPL_PLAN', data)
                self.assertIn('BRANCH', data)

    @patch('setup_roast.get_feature_paths')
    def test_json_with_commits_and_design_system(self, mock_get_feature_paths):
        """Test JSON output with commits and design system."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(feature_dir, 'plan.md'),
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        json_data = '{"commits":["abc123","def456"],"design_system":"/custom/ds.md"}'
        with patch('sys.argv', ['setup-roast.py', f'--json={json_data}']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                # Get output
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                data = json.loads(output)
                
                self.assertEqual(data['COMMITS'], 'abc123,def456')
                self.assertEqual(data['DESIGN_SYSTEM'], '/custom/ds.md')

    @patch('setup_roast.get_feature_paths')
    def test_text_output_format(self, mock_get_feature_paths):
        """Test text output format (default)."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(feature_dir, 'plan.md'),
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast.py']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                # Get output
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                
                self.assertIn('REPORT_FILE:', output)
                self.assertIn('TASKS:', output)
                self.assertIn('IMPL_PLAN:', output)
                self.assertIn('BRANCH:', output)

    @patch('setup_roast.get_feature_paths')
    def test_main_branch_without_json_exits(self, mock_get_feature_paths):
        """Test that main branch without JSON input exits with error."""
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'main',
            'FEATURE_DIR': self.temp_dir,
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast.py']):
            with self.assertRaises(SystemExit) as context:
                self.module.main()
            
            self.assertEqual(context.exception.code, 1)

    @patch('setup_roast.get_feature_paths')
    def test_main_branch_with_json_uses_zo_dir(self, mock_get_feature_paths):
        """Test that main branch with JSON uses .zo directory."""
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'main',
            'FEATURE_DIR': self.temp_dir,
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'tasks.md')
        }
        
        json_data = '{"commits":["abc123"]}'
        with patch('sys.argv', ['setup-roast.py', f'--json={json_data}']):
            self.module.main()
            
            # Roast should be created in .zo/roasts/
            roasts_dir = os.path.join(self.temp_dir, '.zo', 'roasts')
            self.assertTrue(os.path.isdir(roasts_dir))

    @patch('setup_roast.get_feature_paths')
    def test_feature_dir_argument_override(self, mock_get_feature_paths):
        """Test that feature_dir argument overrides branch detection."""
        feature_dir = self.create_directory('.zo/features/002-custom-feature')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-other-feature',
            'FEATURE_DIR': os.path.join(self.temp_dir, '.zo', 'features', '001-other-feature'),
            'FEATURE_SPEC': os.path.join(self.temp_dir, '.zo', 'features', '001-other-feature', 'spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, '.zo', 'features', '001-other-feature', 'plan.md'),
            'TASKS': os.path.join(self.temp_dir, '.zo', 'features', '001-other-feature', 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast.py', feature_dir]):
            self.module.main()
            
            # Roast should be in the specified feature directory
            roasts_dir = os.path.join(feature_dir, 'roasts')
            self.assertTrue(os.path.isdir(roasts_dir))

    @patch('setup_roast.get_feature_paths')
    def test_default_design_system_path(self, mock_get_feature_paths):
        """Test that default design system path is used when not provided."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(feature_dir, 'plan.md'),
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast.py', '--json']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                data = json.loads(output)
                
                # Should use default design system path
                self.assertIn('.zo/design-system.md', data['DESIGN_SYSTEM'])

    @patch('setup_roast.get_feature_paths')
    def test_help_exits_with_zero(self, mock_get_feature_paths):
        """Test that --help exits with code 0."""
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'main',
            'FEATURE_DIR': self.temp_dir,
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast.py', '--help']):
            with self.assertRaises(SystemExit) as context:
                self.module.main()
            
            self.assertEqual(context.exception.code, 0)

    @patch('setup_roast.get_feature_paths')
    def test_report_metadata_appended_to_file(self, mock_get_feature_paths):
        """Test that metadata is appended to report file."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(feature_dir, 'plan.md'),
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        json_data = '{"commits":["abc123"],"design_system":"/custom/ds.md"}'
        with patch('sys.argv', ['setup-roast.py', f'--json={json_data}']):
            self.module.main()
            
            # Get the created report file
            roasts_dir = os.path.join(feature_dir, 'roasts')
            files = os.listdir(roasts_dir)
            report_path = os.path.join(roasts_dir, files[0])
            
            # Check metadata is in file
            with open(report_path, 'r') as f:
                content = f.read()
            
            self.assertIn('<!--', content)
            self.assertIn('-->', content)
            self.assertIn('Commits: abc123', content)
            self.assertIn('Design System: /custom/ds.md', content)

    @patch('setup_roast.get_feature_paths')
    def test_multiple_runs_create_unique_files(self, mock_get_feature_paths):
        """Test that multiple runs create files with unique timestamps."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(feature_dir, 'plan.md'),
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast.py']):
            self.module.main()
        
        # Small delay to ensure different timestamp
        time.sleep(0.1)
        
        with patch('sys.argv', ['setup-roast.py']):
            self.module.main()
        
        # Should have two different files
        roasts_dir = os.path.join(feature_dir, 'roasts')
        files = os.listdir(roasts_dir)
        self.assertEqual(len(files), 2)
        self.assertNotEqual(files[0], files[1])

    @patch('setup_roast.get_feature_paths')
    def test_master_branch_special_handling(self, mock_get_feature_paths):
        """Test master branch (not main) special handling."""
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'master',
            'FEATURE_DIR': self.temp_dir,
            'FEATURE_SPEC': os.path.join(self.temp_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(self.temp_dir, 'plan.md'),
            'TASKS': os.path.join(self.temp_dir, 'tasks.md')
        }
        
        json_data = '{"commits":["abc123"]}'
        with patch('sys.argv', ['setup-roast.py', f'--json={json_data}']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                data = json.loads(output)
                
                # Roast should be in .zo directory
                self.assertIn('.zo/roasts/', data['REPORT_FILE'])

    @patch('setup_roast.get_feature_paths')
    def test_json_data_internal_argument(self, mock_get_feature_paths):
        """Test --json-data internal argument for JSON input."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'FEATURE_SPEC': os.path.join(feature_dir, 'spec.md'),
            'IMPL_PLAN': os.path.join(feature_dir, 'plan.md'),
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        json_str = '{"commits":["abc123"]}'
        
        # Mock parse_args to include json_data
        with patch('setup_roast.parse_args') as mock_parse:
            args = MagicMock()
            args.json = True
            args.json_data = json_str
            args.feature_dir = None
            args.help = False
            mock_parse.return_value = args
            
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                data = json.loads(output)
                
                self.assertEqual(data['COMMITS'], 'abc123')


if __name__ == '__main__':
    unittest.main()
