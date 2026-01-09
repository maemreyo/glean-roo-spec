# Python Scripts Test Architecture Design

## Executive Summary

This document outlines a comprehensive test architecture for the 13 Python scripts located in `.zo/scripts/python/`. The architecture follows Test-Driven Development (TDD) principles, using Python's built-in `unittest` framework without external dependencies. The design emphasizes specification-based testing, independent verification of behavior, and maintainability for the Spec-Driven Development workflow system.

---

## 1. Test Directory Structure

### 1.1 Complete Directory Hierarchy

```
tests/
├── python/
│   ├── __init__.py
│   ├── conftest.py
│   ├── run_tests.py
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── git_fixtures.py
│   │   ├── filesystem_fixtures.py
│   │   ├── template_fixtures.py
│   │   └── script_fixtures.py
│   ├── helpers/
│   │   ├── __init__.py
│   │   ├── test_assertions.py
│   │   ├── output_capture.py
│   │   └── validation_helpers.py
│   ├── test_core/
│   │   ├── __init__.py
│   │   ├── test_common.py
│   │   ├── test_feature_utils.py
│   │   └── test_test_common.py
│   ├── test_features/
│   │   ├── __init__.py
│   │   ├── test_create_feature.py
│   │   ├── test_create_feature_from_idea.py
│   │   └── test_check_prerequisites.py
│   ├── test_setup/
│   │   ├── __init__.py
│   │   ├── test_setup_brainstorm.py
│   │   ├── test_setup_brainstorm_crazy.py
│   │   ├── test_setup_design.py
│   │   ├── test_setup_plan.py
│   │   ├── test_setup_roast.py
│   │   ├── test_setup_roast_verify.py
│   │   └── test_setup_specify_idea.py
│   ├── test_context/
│   │   ├── __init__.py
│   │   └── test_update_agent_context.py
│   ├── mocks/
│   │   ├── __init__.py
│   │   ├── mock_git.py
│   │   ├── mock_filesystem.py
│   │   └── mock_subprocess.py
│   └── test_data/
│       ├── __init__.py
│       ├── sample_plans/
│       ├── sample_templates/
│       └── sample_features/
```

### 1.2 Directory Purpose Definitions

**Root Test Directory (`tests/python/`)**
- Entry point for all Python script tests
- Contains configuration and shared test infrastructure
- Main `__init__.py` marks this as a test package

**Configuration Files**
- `conftest.py`: Central fixture definitions
- `run_tests.py`: Test discovery and execution script

**Fixtures (`fixtures/`)**
- Reusable test setup components organized by domain
- Git, filesystem, templates, and script fixtures
- Factory classes and helper functions

**Helpers (`helpers/`)**
- Custom assertion methods
- Output capture utilities
- Validation helper functions

**Test Modules by Category**
- `test_core/`: Tests for core utility modules (common.py, feature_utils.py)
- `test_features/`: Tests for feature creation scripts
- `test_setup/`: Tests for setup and initialization scripts
- `test_context/`: Tests for context management scripts

**Mocks (`mocks/`)**
- Mock objects for external dependencies
- Git command responses, filesystem operations, subprocess calls

**Test Data (`test_data/`)**
- Sample plan.md files, template files, feature directory structures

---

## 2. Test Architecture Components

### 2.1 Shared Fixtures (conftest.py)

The `conftest.py` module serves as the central configuration point for all tests:

```python
# conftest.py
def set_git_repository(root_path):
    """Initialize a git repository in the test root."""
    subprocess.run(['git', 'init'], cwd=root_path, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], 
                   cwd=root_path, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'],
                   cwd=root_path, capture_output=True)

def create_feature_structure(root_path, feature_name='001-test-feature'):
    """Create a complete feature directory structure."""
    feature_dir = os.path.join(root_path, 'specs', feature_name)
    os.makedirs(feature_dir, exist_ok=True)
    for filename in ['spec.md', 'plan.md', 'tasks.md']:
        Path(os.path.join(feature_dir, filename)).touch()
    return feature_dir
```

### 2.2 Test Helper Utilities

**Custom Assertions Module**

```python
# helpers/test_assertions.py
class TestAssertions:
    """Custom assertion methods for common test patterns."""
    
    @staticmethod
    def assert_json_output(test_case, output, expected_keys):
        """Assert that output contains expected JSON keys."""
        result = json.loads(output)
        for key in expected_keys:
            test_case.assertIn(key, result)
    
    @staticmethod
    def assert_exit_code(test_case, return_code, expected_code=0):
        """Assert script exit code matches expected value."""
        test_case.assertEqual(return_code, expected_code)
```

**Output Capture Helper**

```python
# helpers/output_capture.py
class OutputCapture:
    """Capture stdout and stderr for script execution tests."""
    
    def __init__(self):
        self.stdout_capture = io.StringIO()
        self.stderr_capture = io.StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
    
    def __enter__(self):
        sys.stdout = self.stdout_capture
        sys.stderr = self.stderr_capture
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
    
    @property
    def stdout(self):
        return self.stdout_capture.getvalue()
    
    @property
    def stderr(self):
        return self.stderr_capture.getvalue()
```

### 2.3 Mock/Fixture Data Organization

**Git Command Mocks**

```python
# mocks/mock_git.py
class GitCommandMock:
    """Mock responses for git commands."""
    
    VALID_REPO_ROOT = '/mock/repo/root'
    CURRENT_BRANCH = '001-test-feature'
    
    @staticmethod
    def mock_rev_parse_show_toplevel():
        return GitCommandMock.VALID_REPO_ROOT
    
    @staticmethod
    def mock_rev_parse_abbrev_ref_head():
        return GitCommandMock.CURRENT_BRANCH
```

**Filesystem Mocks**

```python
# mocks/mock_filesystem.py
class FilesystemMock:
    """Mock filesystem operations for testing."""
    
    SAMPLE_SPECS_STRUCTURE = {
        'specs': {
            '001-test-feature': {
                'spec.md': '# Test Feature Specification',
                'plan.md': '# Implementation Plan',
                'tasks.md': '# Task List'
            },
            '002-another-feature': {
                'spec.md': '# Another Feature'
            }
        }
    }
```

### 2.4 Test Categories

**Unit Tests**
- Test individual functions in isolation
- Mock all external dependencies
- Focus on input/output behavior
- Location: `test_core/` modules

**Integration Tests**
- Test interactions between functions
- Minimal mocking for filesystem/git
- Test complete workflows
- Location: `test_features/`, `test_setup/`, `test_context/`

**Validation Tests**
- Test command-line argument parsing
- Test error handling and edge cases
- Test output format compliance

---

## 3. Testing Framework and Tools

### 3.1 Testing Framework Selection

**Framework: Python's built-in `unittest`**

**Rationale:**
- No external dependencies required
- Built into Python standard library
- Supports test discovery and organization
- Familiar patterns for Python developers
- Class-based test organization aligns with TDD

### 3.2 Required Dependencies

**No external dependencies required.**

The test architecture uses only Python standard library modules:
- `unittest`: Test framework
- `tempfile`: Temporary file handling
- `subprocess`: Process execution (for integration tests)
- `io`: StringIO for output capture
- `pathlib`: Path manipulation
- `json`: JSON parsing/validation
- `contextlib`: Context managers

### 3.3 Configuration Files

**Test Runner Script (`tests/python/run_tests.py`)**

```python
#!/usr/bin/env python3
"""
Test runner script for Python scripts.

Usage:
    python tests/python/run_tests.py
    python tests/python/run_tests.py --verbose
    python tests/python/run_tests.py --pattern "test_common"
    python tests/python/run_tests.py --module "test_core.test_common"
"""

import unittest
import sys
import argparse
from pathlib import Path

def discover_tests(module_pattern=None):
    """Discover and return test suite."""
    loader = unittest.TestLoader()
    
    if module_pattern:
        suite = loader.loadTestsFromName(module_pattern)
    else:
        test_dir = Path(__file__).parent
        suite = loader.discover(str(test_dir), pattern='test_*.py')
    
    return suite

def run_tests(suite, verbose=False):
    """Run tests and return results."""
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    return runner.run(suite)

def main():
    parser = argparse.ArgumentParser(description='Run Python script tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--pattern', '-p', help='Test pattern to match')
    parser.add_argument('--module', '-m', help='Specific module to test')
    
    args = parser.parse_args()
    
    suite = discover_tests(args.module)
    
    if not suite.countTestCases():
        print('No tests found matching criteria.')
        sys.exit(1)
    
    result = run_tests(suite, args.verbose)
    
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == '__main__':
    main()
```

**Makefile Integration**

```makefile
# Add to existing Makefile
test-python:
	@python tests/python/run_tests.py

test-python-verbose:
	@python tests/python/run_tests.py --verbose

test-python-core:
	@python tests/python/run_tests.py --module test_core

test-python-features:
	@python tests/python/run_tests.py --module test_features

test-python-setup:
	@python tests/python/run_tests.py --module test_setup

test-python-context:
	@python tests/python/run_tests.py --module test_context
```

---

## 4. Test Design Patterns

### 4.1 Fixture Design for Git Operations

```python
# fixtures/git_fixtures.py
class GitRepositoryFixture:
    """Factory for creating git repositories for testing."""
    
    @staticmethod
    def create_repository(path):
        """Create a git repository at the specified path."""
        os.makedirs(path, exist_ok=True)
        
        subprocess.run(['git', 'init'], cwd=path, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'],
                       cwd=path, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'],
                       cwd=path, capture_output=True)
        
        Path(os.path.join(path, 'README.md')).write_text('# Test Repo')
        subprocess.run(['git', 'add', '.'], cwd=path, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'],
                       cwd=path, capture_output=True)
        
        return path
    
    @staticmethod
    def create_feature_branch(path, branch_name):
        """Create a feature branch in the repository."""
        subprocess.run(['git', 'checkout', '-b', branch_name], 
                       cwd=path, capture_output=True)
```

### 4.2 Fixture Design for File System Operations

```python
# fixtures/filesystem_fixtures.py
class FilesystemFixture:
    """Factory for filesystem operations in tests."""
    
    @staticmethod
    def create_temp_directory():
        """Create and return a temporary directory."""
        temp_dir = tempfile.mkdtemp()
        FilesystemFixture._temp_dirs.add(temp_dir)
        return temp_dir
    
    @staticmethod
    def cleanup_all():
        """Clean up all temporary directories."""
        for temp_dir in FilesystemFixture._temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        FilesystemFixture._temp_dirs.clear()
    
    _temp_dirs = set()
    
    @staticmethod
    def create_directory_structure(base_path, structure):
        """Create a directory structure from a dictionary."""
        for name, content in structure.items():
            path = os.path.join(base_path, name)
            if isinstance(content, dict):
                os.makedirs(path, exist_ok=True)
                FilesystemFixture.create_directory_structure(path, content)
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                Path(path).write_text(content)
```

### 4.3 Fixture Design for Template Processing

```python
# fixtures/template_fixtures.py
class TemplateFixture:
    """Factory for template operations in tests."""
    
    @staticmethod
    def create_template_directory(root):
        """Create a template directory with sample templates."""
        template_dir = os.path.join(root, '.zo', 'templates')
        os.makedirs(template_dir, exist_ok=True)
        
        templates = {
            'spec-template.md': '# Feature Specification\n\n## Overview\n{description}',
            'plan-template.md': '# Implementation Plan\n\n## Language/Version\n{lang}',
            'agent-file-template.md': '# Agent Context\n\n## Active Technologies\n{tech_stack}'
        }
        
        for filename, content in templates.items():
            filepath = os.path.join(template_dir, filename)
            Path(filepath).write_text(content)
        
        return template_dir
```

### 4.4 Mock Strategy for External Dependencies

```python
# mocks/mock_subprocess.py
class SubprocessMock:
    """Mock subprocess calls for testing."""
    
    @staticmethod
    def mock_run_git(args, capture_output=False, text=False, timeout=None, cwd=None):
        """Mock subprocess.run for git commands."""
        result = subprocess.CompletedProcess(
            args=['git'] + args,
            returncode=0,
            stdout='',
            stderr=''
        )
        
        if args[0] == 'rev-parse':
            if args[1] == '--show-toplevel':
                result.stdout = '/mock/repo/root'
            elif args[1] == '--abbrev-ref':
                result.stdout = '001-test-feature'
        
        elif args[0] == 'branch':
            result.stdout = '  001-test-feature\n  main'
        
        return result
```

---

## 5. Test Organization Strategy

### 5.1 Grouping Tests by Functionality

**Module-Based Organization**

```
tests/python/
├── test_core/              # Core utility modules
│   ├── test_common.py      # common.py tests
│   ├── test_feature_utils.py # feature_utils.py tests
│   └── test_test_common.py # test_common.py tests
│
├── test_features/          # Feature creation scripts
│   ├── test_create_new_feature.py
│   ├── test_create_feature_from_idea.py
│   └── test_check_prerequisites.py
│
├── test_setup/             # Setup and initialization scripts
│   ├── test_setup_brainstorm.py
│   ├── test_setup_brainstorm_crazy.py
│   ├── test_setup_design.py
│   ├── test_setup_plan.py
│   ├── test_setup_roast.py
│   ├── test_setup_roast_verify.py
│   └── test_setup_specify_idea.py
│
└── test_context/           # Context management scripts
    └── test_update_agent_context.py
```

### 5.2 Shared Test Utilities

**Base Test Classes**

```python
# helpers/base_test_case.py
class BaseTestCase(unittest.TestCase):
    """Base test case with common functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(self._cleanup_test_dir)
    
    def _cleanup_test_dir(self):
        """Clean up test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def create_file(self, filename, content=''):
        """Create a file in the test directory."""
        filepath = os.path.join(self.test_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        Path(filepath).write_text(content)
        return filepath
    
    def create_directory(self, dirname):
        """Create a directory in the test directory."""
        dirpath = os.path.join(self.test_dir, dirname)
        os.makedirs(dirpath, exist_ok=True)
        return dirpath
```

### 5.3 Reusable Test Patterns

**Argument Parsing Tests**

```python
class TestArgumentParsing(unittest.TestCase):
    """Test cases for command-line argument parsing."""
    
    def test_json_flag_produces_json_output(self):
        """Verify --json flag produces compact JSON output."""
        result = subprocess.run(
            ['python', script_path, '--json'],
            capture_output=True,
            text=True
        )
        json.loads(result.stdout)
        self.assertNotIn('\n', result.stdout.strip())
    
    def test_help_flag_shows_usage(self):
        """Verify --help flag shows usage information."""
        result = subprocess.run(
            ['python', script_path, '--help'],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('Usage:', result.stdout)
    
    def test_unknown_option_returns_error(self):
        """Verify unknown options produce error and exit."""
        result = subprocess.run(
            ['python', script_path, '--unknown-option'],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn('Error', result.stderr)
```

---

## 6. Coverage and Quality Standards

### 6.1 Coverage Targets by Module Priority

**High Priority Modules (95% coverage target)**

- `common.py`: 412 lines
  - Git operations (has_git, run_git_command)
  - Repository functions (get_repo_root, get_current_branch)
  - Path management (get_feature_paths, find_feature_dir_by_prefix)
  - Validation functions (check_feature_branch, check_file_exists)

- `feature_utils.py`: 369 lines
  - Branch number detection
  - Name generation (generate_branch_name, clean_branch_name)
  - Git operations

**Medium Priority Modules (85% coverage target)**

- `create-new-feature.py`: Feature creation workflow
- `create-feature-from-idea.py`: Feature creation from ideas
- `check-prerequisites.py`: Prerequisite validation
- `update-agent-context.py`: 794 lines, context management

**Lower Priority Modules (75% coverage target)**

- `setup-*.py`: Setup scripts (brainstorm, design, plan, roast, etc.)
- `test_common.py`: Test utilities

### 6.2 Code Quality Standards

**Test Naming Conventions**

```python
# Test method naming: snake_case with descriptive purpose
def test_function_name_behavior_or_state_change(self):
    """Clear description of what's being tested."""
    pass

# Examples:
def test_get_current_branch_returns_feature_branch_name(self):
    """Test that get_current_branch returns the current feature branch name."""
    pass

def test_generate_branch_name_filters_stop_words(self):
    """Test that generate_branch_name filters out common stop words."""
    pass

def test_create_new_feature_exits_with_error_when_description_missing(self):
    """Test that create-new-feature exits with error when no description provided."""
    pass
```

### 6.3 Test Quality Metrics

**Test Quality Checklist**

- [ ] Each test has a clear, single purpose
- [ ] Tests are independent and can run in any order
- [ ] Tests use proper setup and teardown
- [ ] Tests use appropriate assertions
- [ ] Tests are maintainable and readable
- [ ] Tests follow the Arrange-Act-Assert pattern
- [ ] Tests cover edge cases and error conditions
- [ ] Tests use meaningful assertions (not just assertTrue)

---

## 7. TDD Workflow Integration

### 7.1 Test-First Development Approach

**TDD Cycle for New Features**

```
1. RED: Write a failing test that specifies the desired behavior
2. GREEN: Write minimal code to make the test pass
3. REFACTOR: Improve code quality while keeping tests passing
4. REPEAT: Continue with next test case
```

**Example TDD Workflow**

```python
# Step 1: Write failing test first
class TestFeatureNameGeneration(unittest.TestCase):
    """Tests for feature name generation from descriptions."""
    
    def test_generates_name_from_simple_description(self):
        """Given a simple feature description, generate a clean branch name."""
        from feature_utils import generate_branch_name
        
        result = generate_branch_name('Add user authentication')
        
        self.assertEqual(result, 'user-authentication')
```

### 7.2 Test Execution Strategy

**Development Workflow**

```mermaid
graph TD
    A[Write Failing Test] --> B[Run Tests - Expect Failure]
    B --> C[Write Minimal Implementation]
    C --> D[Run Tests - Expect Pass]
    D --> E[Refactor Code]
    E --> F[Run Tests - Verify Pass]
    F --> G[Add More Tests]
    G --> A
```

**Running Tests During Development**

```bash
# Run all tests
python tests/python/run_tests.py

# Run specific test module
python tests/python/run_tests.py --module test_core.test_feature_utils

# Run with verbose output
python tests/python/run_tests.py --verbose

# Run single test class
python -m unittest test_core.test_feature_utils.TestBranchNameGeneration

# Run single test method
python -m unittest test_core.test_feature_utils.TestBranchNameGeneration.test_generates_name_from_simple_description
```

### 7.3 CI/CD Integration Considerations

**GitHub Actions Workflow**

```yaml
name: Python Scripts Tests

on:
  push:
    paths:
      - '.zo/scripts/python/**/*.py'
      - 'tests/python/**/*.py'
  pull_request:
    paths:
      - '.zo/scripts/python/**/*.py'
      - 'tests/python/**/*.py'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run Python Tests
        run: |
          python tests/python/run_tests.py --verbose
```

---

## 8. Migration Path

### 8.1 Phased Approach for Test Implementation

**Phase 1: Foundation (Weeks 1-2)**

- Create test directory structure
- Set up configuration files (conftest.py, run_tests.py)
- Create base test classes and fixtures
- Implement Git operation fixtures
- Implement filesystem fixtures

**Phase 2: Core Module Tests (Weeks 3-4)**

- Test `common.py` module (highest priority)
- Test `feature_utils.py` module

**Phase 3: Feature Script Tests (Weeks 5-6)**

- Test `create-new-feature.py`
- Test `create-feature-from-idea.py`
- Test `check-prerequisites.py`

**Phase 4: Setup Script Tests (Weeks 7-8)**

- Test all `setup-*.py` scripts
- Each setup script should have comprehensive tests
- Cover template processing and file creation

**Phase 5: Context Management Tests (Weeks 9-10)**

- Test `update-agent-context.py`
- Plan parsing tests
- Agent file update tests
- Template processing tests

### 8.2 Order of Test Development

**Priority-Based Test Development Order**

```
Priority 1 - Core Utilities:
1. test_common.py - Git operations
2. test_common.py - Path functions
3. test_common.py - File check functions
4. test_feature_utils.py - Branch number detection
5. test_feature_utils.py - Name generation functions

Priority 2 - Feature Creation:
6. test_create_new_feature.py
7. test_create_feature_from_idea.py
8. test_check_prerequisites.py

Priority 3 - Setup Scripts:
9-15. test_setup_*.py scripts

Priority 4 - Context Management:
16. test_update_agent_context.py
```

### 8.3 Dependencies Between Test Modules

**Dependency Graph**

```
conftest.py (base fixtures)
    ↓
test_common.py (core utilities)
    ↓
test_feature_utils.py (feature utilities)
    ↓
test_check_prerequisites.py (depends on common)
    ↓
test_create_new_feature.py (depends on feature_utils)
    ↓
test_setup_*.py scripts (depend on common)
    ↓
test_update_agent_context.py (depends on common)
```

---

## Summary

This test architecture design provides a comprehensive framework for testing the 13 Python scripts in the Spec-Driven Development workflow system. Key highlights include:

- **Framework**: Python's built-in `unittest` for zero external dependencies
- **Organization**: Module-based test structure with clear separation of concerns
- **Fixtures**: Domain-specific fixtures for git, filesystem, and template operations
- **Quality**: High coverage targets (95% for core modules, 85% for feature modules)
- **TDD Integration**: Specification-based tests following test-first development
- **CI/CD Ready**: GitHub Actions workflow included
- **Migration Path**: Phased implementation approach with clear dependencies

The design emphasizes maintainability, extensibility, and alignment with TDD principles while respecting the preference for using built-in Python tools only.
