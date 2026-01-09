# Python Test Suite for .zo Scripts

This directory contains a comprehensive test suite for all Python scripts located in `.zo/scripts/python/`. The test suite uses Python's built-in `unittest` framework with no external dependencies.

## Overview

The test suite is organized into several packages:

- **fixtures**: Reusable test fixtures for git repositories, file systems, and templates
- **helpers**: Utility functions for test execution and assertions
- **mocks**: Mock objects for external dependencies (subprocess, etc.)
- **test_data**: Sample data and templates for testing
- **test_core**: Tests for core utility functions
- **test_features**: Tests for feature creation scripts
- **test_setup**: Tests for setup and configuration scripts
- **test_context**: Tests for context management scripts

## Running Tests

### Run All Tests

```bash
python tests/python/run_tests.py
```

### Run Tests with Verbose Output

```bash
python tests/python/run_tests.py -v
```

### Run Specific Test Package

```bash
python tests/python/run_tests.py test_core
python tests/python/run_tests.py test_features
python tests/python/run_tests.py test_setup
python tests/python/run_tests.py test_context
```

### Using Python's unittest Directly

```bash
# Run all tests
python -m unittest discover -s tests/python -p 'test_*.py'

# Run specific test file
python -m unittest tests.python.test_core.test_string_utils

# Run with verbose output
python -m unittest discover -s tests/python -p 'test_*.py' -v
```

## Test Organization

### Directory Structure

```
tests/python/
├── fixtures/              # Reusable test fixtures
│   ├── __init__.py
│   ├── git_fixtures.py    # Git repository fixtures
│   └── file_fixtures.py   # File system fixtures
├── helpers/               # Test utility functions
│   ├── __init__.py
│   ├── output_helpers.py  # Output capture and parsing
│   └── assertion_helpers.py  # Custom assertions
├── mocks/                 # Mock objects
│   ├── __init__.py
│   └── mock_subprocess.py # Subprocess mocks
├── test_data/             # Sample data
│   ├── __init__.py
│   ├── sample_plan.md
│   ├── sample_spec.md
│   └── sample_template.md
├── test_core/             # Core utility tests
│   └── __init__.py
├── test_features/         # Feature creation tests
│   └── __init__.py
├── test_setup/            # Setup script tests
│   └── __init__.py
├── test_context/          # Context management tests
│   └── __init__.py
├── __init__.py
├── run_tests.py           # Test runner script
└── README.md              # This file
```

## Using Fixtures

Fixtures are designed to be inherited by test classes. They provide automatic setup and teardown.

### Git Repository Fixture

```python
import unittest
from tests.python.fixtures import GitRepositoryFixture

class MyTestCase(GitRepositoryFixture, unittest.TestCase):
    def test_git_operation(self):
        # self.repo_path is available here
        # A temporary git repository has been created
        branch = self.get_current_branch()
        self.assertEqual(branch, 'main')
```

### File System Fixture

```python
import unittest
from tests.python.fixtures import TempDirectoryFixture

class MyTestCase(TempDirectoryFixture, unittest.TestCase):
    def test_file_operations(self):
        # self.temp_dir is available here
        file_path = self.create_file('test.txt', 'content')
        self.assertTrue(self.file_exists('test.txt'))
```

## Using Helpers

Helpers are standalone functions that can be used in any test.

### Output Helpers

```python
from tests.python.helpers import run_python_script, assert_exit_code

def test_script_execution():
    result = run_python_script('.zo/scripts/python/myscript.py')
    assert_exit_code(result, expected_code=0)
```

### Assertion Helpers

```python
from tests.python.helpers import assert_file_exists, assert_branch_name_pattern

def test_branch_creation():
    assert_file_exists('/path/to/file.txt')
    assert_branch_name_pattern('feature/001-test-feature')
```

## Using Mocks

Mocks allow you to test code in isolation without external dependencies.

### Subprocess Mocks

```python
from tests.python.mocks import MockSubprocess

def test_git_command():
    mock = MockSubprocess()
    mock.add_git_result(['status'], stdout='On branch main')
    
    result = mock.run(['git', 'status'])
    assert 'On branch main' in result.stdout
```

## Coverage Targets

The test suite aims for the following coverage targets:

- **Core utilities**: 90%+ coverage
- **Feature scripts**: 85%+ coverage
- **Setup scripts**: 85%+ coverage
- **Context scripts**: 85%+ coverage

## Coding Standards

All test code should follow these standards:

1. **PEP 8**: Follow Python style guidelines
2. **Docstrings**: Include docstrings for all classes, methods, and functions
3. **Cleanup**: All fixtures must properly clean up after themselves
4. **Isolation**: Tests should not depend on each other
5. **Clarity**: Test names should clearly describe what is being tested

## Test Naming Conventions

- Test files: `test_<module_name>.py`
- Test classes: `<ModuleName>TestCase` or `Test<ModuleName>`
- Test methods: `test_<specific_behavior>`

Example:
```python
class FeatureUtilsTestCase(unittest.TestCase):
    def test_generate_branch_name(self):
        # Test code here
        pass
```

## Adding New Tests

When adding new tests:

1. Determine the appropriate test package (core, features, setup, context)
2. Create a new test file following naming conventions
3. Inherit from appropriate fixtures if needed
4. Use helpers and mocks to simplify test code
5. Ensure tests are independent and clean up after themselves
6. Run the test suite to verify new tests pass

## Troubleshooting

### Tests Not Found

If tests are not being discovered:

- Ensure test files start with `test_`
- Verify you're in the project root directory
- Check that `__init__.py` files exist in all test packages

### Import Errors

If you encounter import errors:

- Ensure you're running from the project root
- Check that the `.zo/scripts/python` directory is in the Python path
- Verify all required modules exist

### Fixture Cleanup Issues

If temporary files are not being cleaned up:

- Check that `tearDown()` methods are calling `super().tearDown()`
- Ensure all fixtures inherit from `unittest.TestCase`
- Verify that temporary directories are properly removed

## Contributing

When contributing to the test suite:

1. Follow the existing code style and organization
2. Add docstrings to all new code
3. Ensure all tests pass before submitting
4. Add new fixtures/helpers to the appropriate `__init__.py`
5. Update this README if adding new functionality

## Additional Resources

- [Python unittest documentation](https://docs.python.org/3/library/unittest.html)
- [Test Architecture Design](../TEST_ARCHITECTURE_DESIGN.md)
- [.zo Scripts Documentation](../../.zo/README.md)
