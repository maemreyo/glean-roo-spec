"""
Test Suite for setup-roast-verify.py

This module tests the roast report verification script.
Tests cover feature directory resolution, latest roast report finding,
report path resolution, and end-to-end script execution.

Test Classes:
    TestResolveFeatureDir: Test feature directory resolution logic
    TestFindLatestRoastReport: Test finding latest roast report
    TestResolveReportPath: Test --report argument resolution
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
from unittest.mock import patch, MagicMock
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

from file_fixtures import TempDirectoryFixture
from assertion_helpers import assert_file_exists, assert_json_output
from output_helpers import parse_json_output


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
        self.temp_dir = tempfile.mkdtemp(prefix='roast_verify_test_')
        
        # Import the module
        import setup_roast_verify
        self.module = setup_roast_verify

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


class TestFindLatestRoastReport(TempDirectoryFixture):
    """
    Test the find_latest_roast_report function for locating latest reports.

    Tests ensure that:
    - Latest report is found based on modification time
    - Pattern matching works correctly
    - Multiple reports are sorted by modification time
    - Non-existent roasts directory causes error
    - No matching reports causes error
    """

    def setUp(self):
        """Set up test environment with temporary directory."""
        super().setUp()
        
        # Import the module
        import setup_roast_verify
        self.module = setup_roast_verify

    def test_finds_single_report(self):
        """Test finding a single roast report."""
        roasts_dir = self.create_directory('feature/roasts')
        feature_name = 'test-feature'
        
        # Create a report file
        report_path = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-01-1200.md')
        with open(report_path, 'w') as f:
            f.write('# Roast Report')
        
        result = self.module.find_latest_roast_report(roasts_dir, feature_name)
        
        self.assertEqual(result, report_path)

    def test_finds_latest_report_by_modification_time(self):
        """Test that the most recently modified report is returned."""
        roasts_dir = self.create_directory('feature/roasts')
        feature_name = 'test-feature'
        
        # Create multiple reports with different timestamps
        report1 = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-01-1200.md')
        report2 = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-02-1200.md')
        report3 = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-03-1200.md')
        
        # Create files
        for report in [report1, report2, report3]:
            with open(report, 'w') as f:
                f.write('# Roast Report')
        
        # Make report2 the most recently modified
        time.sleep(0.1)
        with open(report2, 'a') as f:
            f.write('\nUpdated')
        
        result = self.module.find_latest_roast_report(roasts_dir, feature_name)
        
        self.assertEqual(result, report2)

    def test_pattern_matching_wildcard(self):
        """Test that pattern matching uses wildcard correctly."""
        roasts_dir = self.create_directory('feature/roasts')
        feature_name = 'my-feature'
        
        # Create reports with different feature names
        correct_report = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-01-1200.md')
        wrong_report = os.path.join(roasts_dir, 'roast-report-other-feature-2024-01-01-1200.md')
        
        with open(correct_report, 'w') as f:
            f.write('# Correct Report')
        with open(wrong_report, 'w') as f:
            f.write('# Wrong Report')
        
        result = self.module.find_latest_roast_report(roasts_dir, feature_name)
        
        self.assertEqual(result, correct_report)

    def test_nonexistent_roasts_directory_exits(self):
        """Test that non-existent roasts directory causes error."""
        roasts_dir = os.path.join(self.temp_dir, 'nonexistent', 'roasts')
        feature_name = 'test-feature'
        
        with self.assertRaises(SystemExit) as context:
            self.module.find_latest_roast_report(roasts_dir, feature_name)
        
        self.assertEqual(context.exception.code, 1)

    def test_no_matching_reports_exits(self):
        """Test that no matching reports causes error."""
        roasts_dir = self.create_directory('feature/roasts')
        feature_name = 'test-feature'
        
        # Create a report with wrong feature name
        wrong_report = os.path.join(roasts_dir, 'roast-report-wrong-feature-2024-01-01-1200.md')
        with open(wrong_report, 'w') as f:
            f.write('# Wrong Report')
        
        with self.assertRaises(SystemExit) as context:
            self.module.find_latest_roast_report(roasts_dir, feature_name)
        
        self.assertEqual(context.exception.code, 1)

    def test_sorting_by_modification_time_descending(self):
        """Test that reports are sorted by modification time (newest first)."""
        roasts_dir = self.create_directory('feature/roasts')
        feature_name = 'test-feature'
        
        # Create reports in order
        reports = []
        for i in range(3):
            report_path = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-0{i+1}-1200.md')
            with open(report_path, 'w') as f:
                f.write(f'# Report {i}')
            reports.append(report_path)
            if i < 2:
                time.sleep(0.1)  # Ensure different modification times
        
        # Update the middle report to be the newest
        time.sleep(0.1)
        with open(reports[1], 'a') as f:
            f.write('\nNewest update')
        
        result = self.module.find_latest_roast_report(roasts_dir, feature_name)
        
        self.assertEqual(result, reports[1])

    def test_handles_multiple_timestamps(self):
        """Test handling reports with various timestamp formats."""
        roasts_dir = self.create_directory('feature/roasts')
        feature_name = 'test-feature'
        
        # Create reports with different timestamps
        timestamps = [
            '2024-01-01-0900',
            '2024-01-01-1200',
            '2024-12-31-2359'
        ]
        
        for ts in timestamps:
            report_path = os.path.join(roasts_dir, f'roast-report-{feature_name}-{ts}.md')
            with open(report_path, 'w') as f:
                f.write(f'# Report at {ts}')
        
        result = self.module.find_latest_roast_report(roasts_dir, feature_name)
        
        # Should return one of the reports
        self.assertTrue(os.path.isfile(result))
        self.assertIn(feature_name, result)


class TestResolveReportPath(TempDirectoryFixture):
    """
    Test the resolve_report_path function for --report argument resolution.

    Tests ensure that:
    - Absolute paths are resolved correctly
    - Relative paths from current directory work
    - Relative paths from repo root work
    - Non-existent files cause error
    """

    def setUp(self):
        """Set up test environment with temporary directory."""
        super().setUp()
        
        # Import the module
        import setup_roast_verify
        self.module = setup_roast_verify

    def test_absolute_path_resolution(self):
        """Test resolving absolute path to report file."""
        report_path = os.path.join(self.temp_dir, 'roast-report-test.md')
        with open(report_path, 'w') as f:
            f.write('# Roast Report')
        
        result = self.module.resolve_report_path(report_path, self.temp_dir)
        
        self.assertEqual(result, os.path.abspath(report_path))

    def test_relative_path_from_current_dir(self):
        """Test resolving relative path from current directory."""
        original_dir = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            report_name = 'roast-report.md'
            
            with open(report_name, 'w') as f:
                f.write('# Report')
            
            result = self.module.resolve_report_path(report_name, self.temp_dir)
            
            self.assertTrue(os.path.isabs(result))
            self.assertTrue(os.path.isfile(result))
        finally:
            os.chdir(original_dir)

    def test_relative_path_from_repo_root(self):
        """Test resolving relative path from repository root."""
        report_name = 'roast-report.md'
        report_path = os.path.join(self.temp_dir, report_name)
        
        with open(report_path, 'w') as f:
            f.write('# Report')
        
        result = self.module.resolve_report_path(report_name, self.temp_dir)
        
        self.assertIn(report_name, result)

    def test_nonexistent_file_exits(self):
        """Test that non-existent file causes error."""
        nonexistent = 'nonexistent-report.md'
        
        with self.assertRaises(SystemExit) as context:
            self.module.resolve_report_path(nonexistent, self.temp_dir)
        
        self.assertEqual(context.exception.code, 1)

    def test_resolves_existing_file(self):
        """Test that existing file is resolved correctly."""
        roasts_dir = self.create_directory('feature/roasts')
        report_name = 'roast-report-test-2024-01-01-1200.md'
        report_path = os.path.join(roasts_dir, report_name)
        
        with open(report_path, 'w') as f:
            f.write('# Roast Report')
        
        result = self.module.resolve_report_path(report_path, self.temp_dir)
        
        self.assertTrue(os.path.isfile(result))
        self.assertEqual(os.path.basename(result), report_name)


class TestScriptExecution(TempDirectoryFixture):
    """
    Test end-to-end execution of setup-roast-verify.py.

    Tests ensure that:
    - Latest roast report is found automatically
    - --report argument uses specific report
    - JSON and text output formats work
    - Multiple reports result in latest being selected
    - Feature directory resolution from argument and branch
    """

    def setUp(self):
        """Set up test environment with temporary directory."""
        super().setUp()
        
        # Import the module
        import setup_roast_verify
        self.module = setup_roast_verify
        
        # Create .zo directory structure
        self.zo_dir = self.create_directory('.zo')

    @patch('setup_roast_verify.get_feature_paths')
    def test_finds_latest_report_automatically(self, mock_get_feature_paths):
        """Test that latest report is found automatically."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        roasts_dir = self.create_directory('.zo/features/001-test-feature/roasts')
        
        # Create multiple reports
        feature_name = 'feature/001-test-feature'
        report1 = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-01-1200.md')
        report2 = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-02-1200.md')
        
        with open(report1, 'w') as f:
            f.write('# Report 1')
        with open(report2, 'w') as f:
            f.write('# Report 2')
        
        # Make report2 newer
        time.sleep(0.1)
        with open(report2, 'a') as f:
            f.write('\nNewer')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast-verify.py']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                self.assertIn(report2, output)

    @patch('setup_roast_verify.get_feature_paths')
    def test_json_output_format(self, mock_get_feature_paths):
        """Test JSON output format."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        roasts_dir = self.create_directory('.zo/features/001-test-feature/roasts')
        
        feature_name = 'feature/001-test-feature'
        report_path = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-01-1200.md')
        with open(report_path, 'w') as f:
            f.write('# Roast Report')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast-verify.py', '--json']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                data = json.loads(output)
                
                self.assertIn('REPORT_FILE', data)
                self.assertIn('TASKS', data)
                self.assertIn('BRANCH', data)

    @patch('setup_roast_verify.get_feature_paths')
    def test_text_output_format(self, mock_get_feature_paths):
        """Test text output format (default)."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        roasts_dir = self.create_directory('.zo/features/001-test-feature/roasts')
        
        feature_name = 'feature/001-test-feature'
        report_path = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-01-1200.md')
        with open(report_path, 'w') as f:
            f.write('# Roast Report')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast-verify.py']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                
                self.assertIn('REPORT_FILE:', output)
                self.assertIn('TASKS:', output)
                self.assertIn('BRANCH:', output)

    @patch('setup_roast_verify.get_feature_paths')
    def test_report_argument_uses_specific_file(self, mock_get_feature_paths):
        """Test that --report argument uses specific report file."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        roasts_dir = self.create_directory('.zo/features/001-test-feature/roasts')
        
        feature_name = 'feature/001-test-feature'
        report1 = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-01-1200.md')
        report2 = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-02-1200.md')
        
        with open(report1, 'w') as f:
            f.write('# Report 1')
        with open(report2, 'w') as f:
            f.write('# Report 2')
        
        # Make report1 newer (but we want to select report2 via argument)
        time.sleep(0.1)
        with open(report1, 'a') as f:
            f.write('\nNewer')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast-verify.py', f'--report={report2}']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                self.assertIn(report2, output)

    @patch('setup_roast_verify.get_feature_paths')
    def test_feature_dir_argument_override(self, mock_get_feature_paths):
        """Test that feature_dir argument overrides branch detection."""
        feature_dir = self.create_directory('.zo/features/002-custom-feature')
        roasts_dir = self.create_directory('.zo/features/002-custom-feature/roasts')
        
        feature_name = 'feature/002-custom-feature'
        report_path = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-01-1200.md')
        with open(report_path, 'w') as f:
            f.write('# Custom Report')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-other-feature',
            'FEATURE_DIR': os.path.join(self.temp_dir, '.zo', 'features', '001-other-feature'),
            'TASKS': os.path.join(self.temp_dir, '.zo', 'features', '001-other-feature', 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast-verify.py', feature_dir]):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                self.assertIn('002-custom-feature', output)

    @patch('setup_roast_verify.get_feature_paths')
    def test_no_matching_reports_exits(self, mock_get_feature_paths):
        """Test that no matching reports causes error."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        roasts_dir = self.create_directory('.zo/features/001-test-feature/roasts')
        
        # Create a report with wrong feature name
        wrong_report = os.path.join(roasts_dir, 'roast-report-wrong-feature-2024-01-01-1200.md')
        with open(wrong_report, 'w') as f:
            f.write('# Wrong Report')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast-verify.py']):
            with self.assertRaises(SystemExit) as context:
                self.module.main()
            
            self.assertEqual(context.exception.code, 1)

    @patch('setup_roast_verify.get_feature_paths')
    def test_help_exits_with_zero(self, mock_get_feature_paths):
        """Test that --help exits with code 0."""
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'main',
            'FEATURE_DIR': self.temp_dir,
            'TASKS': os.path.join(self.temp_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast-verify.py', '--help']):
            with self.assertRaises(SystemExit) as context:
                self.module.main()
            
            self.assertEqual(context.exception.code, 0)

    @patch('setup_roast_verify.get_feature_paths')
    def test_report_pattern_matching(self, mock_get_feature_paths):
        """Test that roast report pattern matching works correctly."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        roasts_dir = self.create_directory('.zo/features/001-test-feature/roasts')
        
        feature_name = 'feature/001-test-feature'
        
        # Create files that should and should not match
        correct_report = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-01-1200.md')
        wrong_feature = os.path.join(roasts_dir, 'roast-report-other-2024-01-01-1200.md')
        wrong_pattern = os.path.join(roasts_dir, 'my-report-test-2024-01-01-1200.md')
        
        with open(correct_report, 'w') as f:
            f.write('# Correct Report')
        with open(wrong_feature, 'w') as f:
            f.write('# Wrong Feature')
        with open(wrong_pattern, 'w') as f:
            f.write('# Wrong Pattern')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast-verify.py']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                self.assertIn('001-test-feature', output)
                self.assertNotIn('other', output)

    @patch('setup_roast_verify.get_feature_paths')
    def test_multiple_reports_selects_latest(self, mock_get_feature_paths):
        """Test that with multiple reports, the latest is selected."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        roasts_dir = self.create_directory('.zo/features/001-test-feature/roasts')
        
        feature_name = 'feature/001-test-feature'
        
        # Create multiple reports
        reports = []
        for i in range(3):
            report_path = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-0{i+1}-120{i}.md')
            with open(report_path, 'w') as f:
                f.write(f'# Report {i}')
            reports.append(report_path)
            if i < 2:
                time.sleep(0.1)
        
        # Update the middle report to be the newest
        time.sleep(0.1)
        with open(reports[1], 'a') as f:
            f.write('\nNewest update')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast-verify.py']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                self.assertIn('2024-01-02-1201', output)

    @patch('setup_roast_verify.get_feature_paths')
    def test_report_argument_with_absolute_path(self, mock_get_feature_paths):
        """Test --report argument with absolute path."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        
        # Create report in a different location
        custom_report = os.path.join(self.temp_dir, 'custom-report.md')
        with open(custom_report, 'w') as f:
            f.write('# Custom Report')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast-verify.py', f'--report={custom_report}']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                self.assertIn('custom-report.md', output)

    @patch('setup_roast_verify.get_feature_paths')
    def test_report_argument_with_relative_path(self, mock_get_feature_paths):
        """Test --report argument with relative path."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        
        # Create report in temp directory
        report_name = 'relative-report.md'
        report_path = os.path.join(self.temp_dir, report_name)
        with open(report_path, 'w') as f:
            f.write('# Relative Report')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        # Change to temp directory to test relative path
        original_dir = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            
            with patch('sys.argv', ['setup-roast-verify.py', f'--report={report_name}']):
                with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                    self.module.main()
                    
                    output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                    self.assertIn('relative-report.md', output)
        finally:
            os.chdir(original_dir)

    @patch('setup_roast_verify.get_feature_paths')
    def test_nonexistent_report_argument_exits(self, mock_get_feature_paths):
        """Test that non-existent --report argument causes error."""
        feature_dir = self.create_directory('.zo/features/001-test-feature')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature',
            'FEATURE_DIR': feature_dir,
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        nonexistent_report = os.path.join(self.temp_dir, 'nonexistent-report.md')
        
        with patch('sys.argv', ['setup-roast-verify.py', f'--report={nonexistent_report}']):
            with self.assertRaises(SystemExit) as context:
                self.module.main()
            
            self.assertEqual(context.exception.code, 1)

    @patch('setup_roast_verify.get_feature_paths')
    def test_feature_name_with_special_characters(self, mock_get_feature_paths):
        """Test feature names with special characters in pattern."""
        feature_dir = self.create_directory('.zo/features/001-test-feature-2')
        roasts_dir = self.create_directory('.zo/features/001-test-feature-2/roasts')
        
        # Use branch name as feature name in pattern
        feature_name = 'feature/001-test-feature-2'
        report_path = os.path.join(roasts_dir, f'roast-report-{feature_name}-2024-01-01-1200.md')
        with open(report_path, 'w') as f:
            f.write('# Report')
        
        mock_get_feature_paths.return_value = {
            'REPO_ROOT': self.temp_dir,
            'CURRENT_BRANCH': 'feature/001-test-feature-2',
            'FEATURE_DIR': feature_dir,
            'TASKS': os.path.join(feature_dir, 'tasks.md')
        }
        
        with patch('sys.argv', ['setup-roast-verify.py']):
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.module.main()
                
                output = ''.join(str(call) for call in mock_stdout.write.call_args_list)
                self.assertIn('001-test-feature-2', output)


if __name__ == '__main__':
    unittest.main()
