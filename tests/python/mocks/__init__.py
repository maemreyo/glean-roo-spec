"""
Mock Objects Package

This package provides mock objects for external dependencies used in tests.
Mocks allow testing code in isolation without requiring actual external services.

Available Mocks:
- mock_subprocess: Mock subprocess module for testing git commands and script execution

Example:
    from tests.python.mocks import MockSubprocess

    mock = MockSubprocess()
    mock.add_command_result('git', 'status', stdout='On branch main')
"""

from .mock_subprocess import MockSubprocess

__all__ = [
    'MockSubprocess',
]
