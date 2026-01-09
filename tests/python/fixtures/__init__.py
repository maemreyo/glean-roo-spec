"""
Test Fixtures Package

This package provides reusable test fixtures for the Python test suite.
Fixtures are designed to be inherited by test classes and provide common
setup and teardown functionality.

Available Fixtures:
- GitRepositoryFixture: Creates temporary git repositories for testing
- GitBranchFixture: Creates test branches with naming patterns
- TempDirectoryFixture: Creates temporary directory structures
- FeatureDirectoryFixture: Creates feature directory structures
- TemplateFixture: Creates and manages test templates

All fixtures implement proper cleanup in their tearDown methods to ensure
no test artifacts are left behind.
"""

from .git_fixtures import GitRepositoryFixture, GitBranchFixture
from .file_fixtures import TempDirectoryFixture, FeatureDirectoryFixture, TemplateFixture

__all__ = [
    'GitRepositoryFixture',
    'GitBranchFixture',
    'TempDirectoryFixture',
    'FeatureDirectoryFixture',
    'TemplateFixture',
]
