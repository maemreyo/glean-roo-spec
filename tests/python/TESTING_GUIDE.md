# Testing Guide for Python Scripts

**Project**: Python Scripts Test Suite for `.zo` Scripts  
**Test Framework**: Python unittest (built-in)  
**Last Updated**: 2026-01-09

This guide provides comprehensive instructions for writing, running, and maintaining tests for the Python scripts in the `.zo/scripts/python/` directory.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Running Tests](#running-tests)
3. [Writing New Tests](#writing-new-tests)
4. [Test Naming Conventions](#test-naming-conventions)
5. [Using Fixtures](#using-fixtures)
6. [Using Helpers](#using-helpers)
7. [Using Mocks](#using-mocks)
8. [TDD Best Practices](#tdd-best-practices)
9. [Common Testing Patterns](#common-testing-patterns)
10. [Debugging Tests](#debugging-tests)
11. [Test Maintenance](#test-maintenance)

---

## Quick Start

### Install Dependencies

This test suite uses **only Python standard library** modules. No external dependencies required.

```bash
# Verify Python version (3.7+ recommended)
python --version

# No pip install needed - uses built-in unittest
```

### Run All Tests

```bash
# From project root
python tests/python/run_tests.py
```

### Run Specific Tests

```bash
# Run core utilities tests
python tests/python/run_tests.py test_core

# Run with verbose output
python tests/python/run_tests.py -v

# Run specific test file
python -m unittest tests.python.test_core.test_common
```

---

## Running Tests

### Basic Test Execution

#### Run All Tests

```bash
python tests/python/run_tests.py
```

Expected output:
```
.......
----------------------------------------------------------------------
Ran 360+ tests in 2.345s

OK
```

#### Run with Verbose Output

```bash
python tests/python/run_tests.py -v
```

This shows detailed output for each test:
```
test_get_repo_root_returns_repository_path (test_core.test_common.TestGitOperations) ... ok
test_get_current_branch_returns_branch_name (test_core.test_common.TestGitOperations) ... ok
...
----------------------------------------------------------------------
Ran 360+ tests in 2.345s

OK
```

### Run Specific Test Packages

```bash
# Core utilities (common.py, feature_utils.py)
python tests/python/run_tests.py test_core

# Feature creation scripts
python tests/python/run_tests.py test_features

# Setup scripts
python tests/python/run_tests.py test_setup

# Context management
python tests/python/run_tests.py test_context
```

### Run Specific Test Files

```bash
# Test common.py
python -m unittest tests.python.test_core.test_common

# Test feature_utils.py
python -m unittest tests.python.test_core.test_feature_utils

# Test create-new-feature.py
python -m unittest tests.python.test_features.test_create_new_feature
```

### Run Specific Test Classes

```bash
# Test git operations in common.py
python -m unittest tests.python.test_core.test_common.TestGitOperations

# Test branch name generation
python -m unittest tests.python.test_core.test_feature_utils.TestBranchNameGeneration
```

### Run Specific Test Methods

```bash
# Test single method
python -m unittest tests.python.test_core.test_common.TestGitOperations.test_get_repo_root_returns_repository_path

# Test multiple methods
python -m unittest tests.python.test_core.test_common.TestGitOperations.test_get_repo_root_returns_repository_path tests.python.test_core.test_common.TestGitOperations.test_get_current_branch_returns_branch_name
```

### Run Tests with Pattern Matching

```bash
# Run all tests matching pattern
python -m unittest discover -s tests/python -p 'test_common*.py'

# Run tests in subdirectory
python -m unittest discover -s tests/python/test_core -p 'test_*.py'
```

### Test Execution Options

```bash
# Stop on first failure
python -m unittest -f tests.python.test_core.test_common

# Catch exceptions during test loading
python -m unittest -c tests.python.test_core.test_common

# Buffer output during test execution
python -m unittest -b tests.python.test_core.test_common

# Show local variables in tracebacks
python -m unittest -l tests.python.test_core.test_common
```

---

## Writing New Tests

### Test File Structure

```python
#!/usr/bin/env python3
"""
Tests for module_name.py functionality.

This module contains tests for the module_name.py script,
covering feature X, feature Y, and feature Z.
"""

import unittest
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../.zo/scripts/python'))

from tests.python.fixtures import GitRepositoryFixture, TempDirectoryFixture
from tests.python.helpers import run_python_script, assert_exit_code


class TestModuleName(GitRepositoryFixture, TempDirectoryFixture, unittest.TestCase):
    """Tests for module_name.py functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test."""
        super().setUp()
        # Additional setup here
        
    def tearDown(self):
        """Clean up after each test."""
        # Additional cleanup here
        super().tearDown()
    
    def test_specific_behavior(self):
        """Test that specific behavior works as expected."""
        # Arrange
        input_data = "test input"
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        self.assertEqual(result, "expected output")
    
    def test_error_case(self):
        """Test that error cases are handled properly."""
        with self.assertRaises(ValueError):
            function_under_test(invalid_input)


if __name__ == '__main__':
    unittest.main()
```

### Test Method Structure

Follow the **Arrange-Act-Assert (AAA)** pattern:

```python
def test_function_name_descriptive_outcome(self):
    """Test that function_name produces descriptive outcome when given input."""
    # Arrange - Set up the test
    input_value = "test input"
    expected_output = "expected result"
    
    # Act - Execute the code under test
    result = function_under_test(input_value)
    
    # Assert - Verify the outcome
    self.assertEqual(result, expected_output)
```

### Example: Testing a Git Operation

```python
import unittest
from tests.python.fixtures import GitRepositoryFixture
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../.zo/scripts/python'))
import common


class TestGitOperations(GitRepositoryFixture, unittest.TestCase):
    """Tests for git operation functions in common.py."""
    
    def test_get_repo_root_returns_repository_path(self):
        """Test that get_repo_root returns the repository root path."""
        # Arrange - Git repository already created by fixture
        expected_path = self.repo_path
        
        # Act
        result = common.get_repo_root()
        
        # Assert
        self.assertEqual(result, expected_path)
        self.assertTrue(os.path.isabs(result))
    
    def test_get_current_branch_returns_branch_name(self):
        """Test that get_current_branch returns the current branch name."""
        # Arrange - Create a test branch
        test_branch = 'feature/test-branch'
        self.create_branch(test_branch)
        self.checkout_branch(test_branch)
        
        # Act
        result = common.get_current_branch()
        
        # Assert
        self.assertEqual(result, test_branch)
    
    def test_get_repo_root_raises_error_when_not_in_git_repo(self):
        """Test that get_repo_root raises error when not in a git repository."""
        # Arrange - Change to non-git directory
        non_git_dir = tempfile.mkdtemp()
        original_dir = os.getcwd()
        
        try:
            os.chdir(non_git_dir)
            
            # Act & Assert
            with self.assertRaises(RuntimeError):
                common.get_repo_root()
        finally:
            os.chdir(original_dir)
            os.rmdir(non_git_dir)
```

### Example: Testing Command-Line Script

```python
import unittest
import subprocess
from tests.python.fixtures import TempDirectoryFixture
from tests.python.helpers import assert_exit_code


class TestCreateNewFeature(TempDirectoryFixture, unittest.TestCase):
    """Tests for create-new-feature.py script."""
    
    def test_creates_feature_directory_with_valid_name(self):
        """Test that script creates feature directory with valid name."""
        # Arrange
        feature_name = '001-test-feature'
        script_path = '.zo/scripts/python/create-new-feature.py'
        
        # Act
        result = subprocess.run(
            ['python', script_path, feature_name],
            capture_output=True,
            text=True,
            cwd=self.temp_dir
        )
        
        # Assert
        assert_exit_code(result, expected_code=0)
        feature_dir = os.path.join(self.temp_dir, 'specs', feature_name)
        self.assertTrue(os.path.exists(feature_dir))
        self.assertTrue(os.path.isdir(feature_dir))
    
    def test_exits_with_error_when_name_missing(self):
        """Test that script exits with error when feature name is missing."""
        # Arrange
        script_path = '.zo/scripts/python/create-new-feature.py'
        
        # Act
        result = subprocess.run(
            ['python', script_path],
            capture_output=True,
            text=True,
            cwd=self.temp_dir
        )
        
        # Assert
        assert_exit_code(result, expected_code=1)
        self.assertIn('error', result.stderr.lower())
```

### Example: Testing with Mocks

```python
import unittest
from unittest.mock import patch, MagicMock
from tests.python.mocks import MockSubprocess


class TestSubprocessOperations(unittest.TestCase):
    """Tests for functions that use subprocess."""
    
    def test_run_git_command_with_mock(self):
        """Test that run_git_command executes git command correctly."""
        # Arrange
        mock_subprocess = MockSubprocess()
        mock_subprocess.add_git_result(['status'], stdout='On branch main')
        
        with patch('subprocess.run', side_effect=mock_subprocess.run):
            # Act
            result = run_git_command(['status'])
            
            # Assert
            self.assertEqual(result.returncode, 0)
            self.assertIn('On branch main', result.stdout)
    
    @patch('os.path.exists')
    def test_check_file_exists_with_mock(self, mock_exists):
        """Test that check_file_exists returns correct result."""
        # Arrange
        mock_exists.return_value = True
        
        # Act
        result = check_file_exists('/path/to/file.txt')
        
        # Assert
        self.assertTrue(result)
        mock_exists.assert_called_once_with('/path/to/file.txt')
```

---

## Test Naming Conventions

### File Naming

- Test files must start with `test_`
- Use snake_case for file names
- Name should reflect the module being tested

```
✅ Good:
test_common.py
test_feature_utils.py
test_create_new_feature.py

❌ Bad:
common_tests.py
FeatureUtilsTest.py
test.py
```

### Class Naming

- Test classes should end with `TestCase` or start with `Test`
- Use PascalCase for class names
- Name should reflect the functionality being tested

```python
✅ Good:
class TestGitOperations(unittest.TestCase):
class FeatureUtilsTestCase(unittest.TestCase):

❌ Bad:
class test_git_operations(unittest.TestCase):
class GitTest(unittest.TestCase):
```

### Method Naming

- Test methods must start with `test_`
- Use snake_case for method names
- Names should describe what is being tested
- Format: `test_<function>_<scenario>_<expected_result>`

```python
✅ Good:
def test_get_repo_root_returns_repository_path(self):
def test_generate_branch_name_filters_stop_words(self):
def test_create_feature_exits_with_error_when_description_missing(self):

❌ Bad:
def test_git(self):
def test1(self):
def testFeature(self):
```

### Docstrings

- All test methods should have docstrings
- Docstrings should describe what is being tested
- Use the format: "Test that <function> <behavior>"

```python
def test_get_repo_root_returns_repository_path(self):
    """Test that get_repo_root returns the repository root path."""
    pass
```

---

## Using Fixtures

Fixtures provide reusable test setup and teardown. They are designed to be inherited by test classes.

### GitRepositoryFixture

Creates a temporary git repository for testing git operations.

```python
from tests.python.fixtures import GitRepositoryFixture

class MyTestCase(GitRepositoryFixture, unittest.TestCase):
    def test_git_operation(self):
        # self.repo_path is available here
        # A temporary git repository has been created
        
        # Get current branch
        branch = self.get_current_branch()
        self.assertEqual(branch, 'main')
        
        # Create a new branch
        self.create_branch('feature/test-branch')
        self.checkout_branch('feature/test-branch')
        
        # Verify branch changed
        current = self.get_current_branch()
        self.assertEqual(current, 'feature/test-branch')
```

Available methods:
- `self.repo_path` - Path to the temporary repository
- `self.get_current_branch()` - Get current branch name
- `self.create_branch(name)` - Create a new branch
- `self.checkout_branch(name)` - Checkout a branch
- `self.commit_all(message)` - Commit all changes

### TempDirectoryFixture

Creates a temporary directory for file system operations.

```python
from tests.python.fixtures import TempDirectoryFixture

class MyTestCase(TempDirectoryFixture, unittest.TestCase):
    def test_file_operations(self):
        # self.temp_dir is available here
        # A temporary directory has been created
        
        # Create a file
        file_path = self.create_file('test.txt', 'content')
        self.assertTrue(self.file_exists('test.txt'))
        
        # Read the file
        content = self.read_file('test.txt')
        self.assertEqual(content, 'content')
        
        # Create nested directories
        self.create_directory('nested/dir')
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'nested/dir')))
```

Available methods:
- `self.temp_dir` - Path to the temporary directory
- `self.create_file(filename, content)` - Create a file
- `self.read_file(filename)` - Read a file
- `self.file_exists(filename)` - Check if file exists
- `self.create_directory(dirname)` - Create a directory

### Custom Fixtures

You can create your own fixtures by extending existing ones:

```python
from tests.python.fixtures import GitRepositoryFixture

class CustomFeatureFixture(GitRepositoryFixture):
    """Fixture for testing feature creation with git."""
    
    def setUp(self):
        """Set up feature directory structure."""
        super().setUp()
        self.feature_dir = os.path.join(self.repo_path, 'specs', '001-test-feature')
        os.makedirs(self.feature_dir, exist_ok=True)
        
        # Create feature files
        self.create_feature_files()
    
    def create_feature_files(self):
        """Create standard feature files."""
        files = ['spec.md', 'plan.md', 'tasks.md']
        for filename in files:
            filepath = os.path.join(self.feature_dir, filename)
            Path(filepath).touch()
```

---

## Using Helpers

Helper functions provide reusable utilities for common test operations.

### Output Helpers

Functions for running scripts and capturing output.

```python
from tests.python.helpers import run_python_script, assert_exit_code

def test_script_execution():
    # Run a Python script
    result = run_python_script('.zo/scripts/python/myscript.py', 
                               args=['--option', 'value'])
    
    # Assert exit code
    assert_exit_code(result, expected_code=0)
    
    # Check output
    self.assertIn('Success', result.stdout)
```

Available functions:
- `run_python_script(script_path, args=None, cwd=None)` - Run a Python script
- `assert_exit_code(result, expected_code)` - Assert exit code matches expected

### Assertion Helpers

Custom assertion methods for common test patterns.

```python
from tests.python.helpers import (
    assert_file_exists,
    assert_branch_name_pattern,
    assert_feature_structure
)

def test_feature_creation():
    # Assert file exists
    assert_file_exists('/path/to/spec.md')
    
    # Assert branch name follows pattern
    assert_branch_name_pattern('feature/001-test-feature')
    
    # Assert feature directory structure
    assert_feature_structure('/path/to/specs/001-test-feature',
                           required_files=['spec.md', 'plan.md', 'tasks.md'])
```

Available functions:
- `assert_file_exists(filepath)` - Assert file exists
- `assert_branch_name_pattern(branch_name)` - Assert branch follows naming pattern
- `assert_feature_structure(feature_dir, required_files)` - Assert feature structure

### Custom Helpers

Create custom helpers for repeated test patterns:

```python
# In tests/python/helpers/custom_helpers.py

def assert_feature_created(feature_dir, feature_name):
    """Assert that a feature directory was created correctly."""
    assert os.path.exists(feature_dir), f"Feature directory {feature_dir} does not exist"
    assert os.path.isdir(feature_dir), f"{feature_dir} is not a directory"
    
    required_files = ['spec.md', 'plan.md', 'tasks.md']
    for filename in required_files:
        filepath = os.path.join(feature_dir, filename)
        assert os.path.exists(filepath), f"Required file {filename} not found"

# Use in tests
from tests.python.helpers.custom_helpers import assert_feature_created

def test_create_feature(self):
    feature_dir = create_feature('001-test-feature')
    assert_feature_created(feature_dir, '001-test-feature')
```

---

## Using Mocks

Mocks allow you to test code in isolation without external dependencies.

### Subprocess Mocks

Mock subprocess calls for testing command execution.

```python
from tests.python.mocks import MockSubprocess

def test_git_command():
    mock = MockSubprocess()
    
    # Add expected results
    mock.add_git_result(['status'], stdout='On branch main', returncode=0)
    mock.add_git_result(['branch'], stdout='  main\n* feature/test', returncode=0)
    
    # Use mock
    with patch('subprocess.run', side_effect=mock.run):
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        self.assertEqual(result.stdout, 'On branch main')
```

### Using unittest.mock

Python's built-in mocking library:

```python
from unittest.mock import patch, MagicMock, Mock

@patch('os.path.exists')
def test_with_patch(self, mock_exists):
    """Test using patch decorator."""
    mock_exists.return_value = True
    
    result = check_file_exists('/path/to/file.txt')
    
    self.assertTrue(result)
    mock_exists.assert_called_once_with('/path/to/file.txt')

def test_with_context_manager(self):
    """Test using patch as context manager."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout='success')
        
        result = run_command(['git', 'status'])
        
        self.assertEqual(result.returncode, 0)
        mock_run.assert_called_once_with(['git', 'status'], capture_output=True)

def test_with_mock_object(self):
    """Test using Mock object."""
    mock_obj = Mock()
    mock_obj.method.return_value = 'test value'
    
    result = mock_obj.method()
    
    self.assertEqual(result, 'test value')
    mock_obj.method.assert_called_once()
```

---

## TDD Best Practices

### Red-Green-Refactor Cycle

Follow the TDD cycle when developing new features:

```
1. RED   → Write a failing test that specifies desired behavior
2. GREEN → Write minimal code to make the test pass
3. REFACTOR → Improve code quality while keeping tests passing
4. REPEAT → Continue with next test case
```

### Example: TDD Workflow

```python
# Step 1: RED - Write failing test first
def test_generate_branch_name_from_description(self):
    """Test that generate_branch_name creates branch names from descriptions."""
    result = generate_branch_name('Add user authentication')
    
    # This will fail because function doesn't exist yet
    self.assertEqual(result, 'user-authentication')

# Step 2: GREEN - Write minimal implementation
def generate_branch_name(description):
    """Generate a branch name from a description."""
    words = description.lower().split()
    return '-'.join(words)

# Step 3: REFACTOR - Improve implementation
def generate_branch_name(description):
    """Generate a clean branch name from a description."""
    # Remove stop words
    stop_words = {'a', 'an', 'the', 'for', 'with'}
    words = [w for w in description.lower().split() if w not in stop_words]
    
    # Clean and join
    return '-'.join(words)

# Step 4: REPEAT - Add more tests
def test_generate_branch_name_filters_stop_words(self):
    """Test that generate_branch_name filters stop words."""
    result = generate_branch_name('Add a feature for testing')
    
    self.assertEqual(result, 'add-feature-testing')
```

### Test-First Development Rules

1. **Write tests before code**
   - Tests serve as specifications
   - Prevents over-engineering
   - Ensures code is testable

2. **Write the simplest code that passes**
   - Don't implement features not tested
   - Keep implementation minimal
   - Refactor after tests pass

3. **Run tests frequently**
   - Run tests after each change
   - Fix failing tests immediately
   - Maintain green test suite

4. **Refactor confidently**
   - Tests protect against regressions
   - Improve code quality continuously
   - Keep code maintainable

### Clean Test Code

Follow these principles for maintainable test code:

#### Single Responsibility

Each test should verify one behavior:

```python
# ❌ Bad - Testing multiple behaviors
def test_git_operations(self):
    branch = get_current_branch()
    root = get_repo_root()
    self.assertEqual(branch, 'main')
    self.assertEqual(root, '/path')

# ✅ Good - One behavior per test
def test_get_current_branch_returns_branch_name(self):
    branch = get_current_branch()
    self.assertEqual(branch, 'main')

def test_get_repo_root_returns_repository_path(self):
    root = get_repo_root()
    self.assertEqual(root, '/path')
```

#### Clear Naming

Test names should describe what is being tested:

```python
# ❌ Bad - Unclear what is being tested
def test_git(self):
    pass

# ✅ Good - Clear description
def test_get_repo_root_returns_repository_path(self):
    pass
```

#### DRY Principle

Use fixtures and helpers to avoid duplication:

```python
# ❌ Bad - Duplicated setup
def test_feature_1(self):
    repo = tempfile.mkdtemp()
    subprocess.run(['git', 'init'], cwd=repo)
    # test code
    shutil.rmtree(repo)

def test_feature_2(self):
    repo = tempfile.mkdtemp()
    subprocess.run(['git', 'init'], cwd=repo)
    # test code
    shutil.rmtree(repo)

# ✅ Good - Use fixture
class MyTest(GitRepositoryFixture, unittest.TestCase):
    def test_feature_1(self):
        # self.repo_path already set up
        # test code
    
    def test_feature_2(self):
        # self.repo_path already set up
        # test code
```

#### Meaningful Assertions

Use specific assertions that clearly indicate failures:

```python
# ❌ Bad - Generic assertion
def test_branch_name(self):
    result = generate_branch_name('Test')
    assert result  # What does this test?

# ✅ Good - Specific assertion
def test_branch_name_not_empty(self):
    result = generate_branch_name('Test')
    self.assertIsNotNone(result)
    self.assertGreater(len(result), 0)
```

---

## Common Testing Patterns

### Testing Command-Line Scripts

```python
def test_script_with_arguments(self):
    """Test script with command-line arguments."""
    script_path = '.zo/scripts/python/myscript.py'
    
    result = subprocess.run(
        ['python', script_path, '--option', 'value'],
        capture_output=True,
        text=True,
        cwd=self.temp_dir
    )
    
    self.assertEqual(result.returncode, 0)
    self.assertIn('Expected output', result.stdout)
```

### Testing Error Handling

```python
def test_error_handling(self):
    """Test that errors are handled correctly."""
    with self.assertRaises(ValueError) as context:
        function_with_invalid_input()
    
    self.assertIn('expected error message', str(context.exception))
```

### Testing File Operations

```python
def test_file_creation(self):
    """Test that file is created correctly."""
    filepath = create_file('test.txt', 'content')
    
    self.assertTrue(os.path.exists(filepath))
    with open(filepath, 'r') as f:
        content = f.read()
    self.assertEqual(content, 'content')
```

### Testing Git Operations

```python
def test_git_branch_creation(self):
    """Test that git branch is created."""
    self.create_branch('feature/test-branch')
    
    branches = subprocess.run(
        ['git', 'branch'],
        capture_output=True,
        text=True,
        cwd=self.repo_path
    )
    
    self.assertIn('feature/test-branch', branches.stdout)
```

### Testing with Fixtures

```python
class MyTest(GitRepositoryFixture, TempDirectoryFixture, unittest.TestCase):
    """Test using multiple fixtures."""
    
    def test_with_git_and_files(self):
        # Both git repo and temp dir available
        feature_file = os.path.join(self.temp_dir, 'feature.txt')
        Path(feature_file).write_text('feature content')
        
        subprocess.run(['git', 'add', '.'], cwd=self.repo_path)
        subprocess.run(['git', 'commit', '-m', 'Add feature'], 
                      cwd=self.repo_path)
        
        # Assert changes committed
        result = subprocess.run(['git', 'log', '--oneline'], 
                              capture_output=True, text=True,
                              cwd=self.repo_path)
        self.assertIn('Add feature', result.stdout)
```

---

## Debugging Tests

### Running Tests in Debug Mode

```bash
# Run with verbose output
python tests/python/run_tests.py -v

# Run single test with detailed output
python -m unittest tests.python.test_core.test_common.TestGitOperations.test_get_repo_root_returns_repository_path -v
```

### Using Print Statements

```python
def test_with_debugging(self):
    """Test with debug output."""
    value = function_under_test()
    
    print(f"Value: {value}")  # Will show in verbose output
    print(f"Type: {type(value)}")
    
    self.assertEqual(value, expected)
```

### Using Python Debugger

```python
import pdb

def test_with_breakpoint(self):
    """Test with breakpoint for debugging."""
    value = some_function()
    
    pdb.set_trace()  # Execution pauses here
    
    self.assertEqual(value, expected)
```

### Common Debugging Techniques

1. **Isolate the failing test**
   ```bash
   python -m unittest tests.python.test_module.test_class.test_method -v
   ```

2. **Check fixture setup**
   ```python
   def test_with_fixture_check(self):
       print(f"Repo path: {self.repo_path}")
       print(f"Files in repo: {os.listdir(self.repo_path)}")
   ```

3. **Verify test data**
   ```python
   def test_with_data_check(self):
       data = load_test_data()
       print(f"Test data: {data}")
   ```

4. **Check assertions**
   ```python
   def test_with_assertion_check(self):
       result = function_under_test()
       print(f"Result: {result}")
       print(f"Expected: {expected}")
       self.assertEqual(result, expected)
   ```

---

## Test Maintenance

### Keeping Tests Up to Date

1. **Update tests when code changes**
   - Modify tests to reflect new behavior
   - Add tests for new features
   - Remove tests for deprecated functionality

2. **Refactor test code**
   - Improve test organization
   - Extract common patterns to fixtures/helpers
   - Keep test code DRY

3. **Review test coverage**
   - Identify untested code paths
   - Add tests for edge cases
   - Maintain coverage targets

### Managing Test Data

1. **Use test data directory**
   ```
   tests/python/test_data/
   ├── sample_plan.md
   ├── sample_spec.md
   └── sample_template.md
   ```

2. **Load test data in tests**
   ```python
   def test_with_sample_data(self):
       data_file = os.path.join(
           os.path.dirname(__file__),
           'test_data',
           'sample_plan.md'
       )
       with open(data_file, 'r') as f:
           data = f.read()
       # Test with data
   ```

3. **Keep test data minimal**
   - Use minimal examples
   - Avoid large files
   - Focus on test-specific data

### Handling Flaky Tests

1. **Identify the cause**
   - Timing issues
   - Dependency on external state
   - Race conditions

2. **Fix the test**
   - Add proper setup/teardown
   - Use mocks for external dependencies
   - Make tests deterministic

3. **If flaky, isolate**
   ```bash
   # Run test multiple times
   for i in {1..10}; do
       python -m unittest tests.python.test_module.test_class.test_method
   done
   ```

### Performance Considerations

1. **Keep tests fast**
   - Avoid unnecessary I/O
   - Use mocks for slow operations
   - Parallelize independent tests

2. **Profile slow tests**
   ```python
   import time
   
   def test_with_timing(self):
       start = time.time()
       result = slow_function()
       duration = time.time() - start
       print(f"Test took {duration:.2f} seconds")
   ```

3. **Optimize when needed**
   - Cache expensive operations
   - Use fixtures for setup
   - Minimize test data

---

## Additional Resources

### Documentation

- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [Test Suite README](README.md)
- [Test Coverage Report](TEST_COVERAGE_REPORT.md)
- [Test Architecture Design](../../TEST_ARCHITECTURE_DESIGN.md)

### Best Practices

- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [TDD Best Practices](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- [Clean Code Principles](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)

### Community Resources

- [Python Testing Tutorial](https://realpython.com/python-testing/)
- [unittest Pattern Reference](https://docs.python.org/3/library/unittest.html#organizing-tests)

---

## Quick Reference

### Test Execution Commands

```bash
# Run all tests
python tests/python/run_tests.py

# Run with verbose output
python tests/python/run_tests.py -v

# Run specific package
python tests/python/run_tests.py test_core

# Run specific file
python -m unittest tests.python.test_core.test_common

# Run specific class
python -m unittest tests.python.test_core.test_common.TestGitOperations

# Run specific method
python -m unittest tests.python.test_core.test_common.TestGitOperations.test_get_repo_root
```

### Test Template

```python
import unittest
from tests.python.fixtures import GitRepositoryFixture

class TestMyModule(GitRepositoryFixture, unittest.TestCase):
    """Tests for my_module.py functionality."""
    
    def test_specific_behavior(self):
        """Test that specific behavior works as expected."""
        # Arrange
        input_value = "test"
        
        # Act
        result = function_under_test(input_value)
        
        # Assert
        self.assertEqual(result, "expected")
```

### Common Assertions

```python
# Equality
self.assertEqual(a, b)
self.assertNotEqual(a, b)

# Boolean
self.assertTrue(x)
self.assertFalse(x)

# None
self.assertIsNone(x)
self.assertIsNotNone(x)

# Exceptions
with self.assertRaises(ValueError):
    function_that_raises()

# File operations
self.assertTrue(os.path.exists(path))
self.assertFalse(os.path.exists(path))
```

---

**Last Updated**: 2026-01-09  
**Test Framework**: Python unittest (built-in)  
**Total Test Cases**: 360+  
**Average Coverage**: 85%
