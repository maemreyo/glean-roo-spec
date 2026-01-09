"""
Mock Subprocess Module

This module provides a mock subprocess module for testing git commands
and other subprocess executions. It allows you to predefine command responses
and test code in isolation.

Classes:
    MockCompletedProcess: Mock result object for subprocess execution
    MockSubprocess: Mock subprocess module with configurable responses
"""

from typing import Dict, List, Optional, Any, Tuple


class MockCompletedProcess:
    """
    Mock result object for subprocess execution.

    Mimics subprocess.CompletedProcess with configurable output.

    Attributes:
        args: Arguments used to launch the process
        stdout: Standard output content
        stderr: Standard error content
        returncode: Process exit code
    """

    def __init__(
        self,
        args: List[str],
        stdout: str = '',
        stderr: str = '',
        returncode: int = 0
    ):
        self.args = args
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    def __repr__(self) -> str:
        return (f"MockCompletedProcess(args={self.args}, "
                f"returncode={self.returncode})")


class MockSubprocess:
    """
    Mock subprocess module with configurable command responses.

    This class allows you to predefine responses for specific commands
    and provides a run() method that returns those responses.

    Attributes:
        command_results: Dictionary mapping command tuples to results
        default_result: Default result for unrecognized commands

    Example:
        mock = MockSubprocess()
        mock.add_command_result('git', 'status', stdout='On branch main')
        result = mock.run(['git', 'status'])
        assert result.stdout == 'On branch main'
    """

    def __init__(self):
        """Initialize the mock subprocess with empty command results."""
        self.command_results: Dict[Tuple[str, ...], MockCompletedProcess] = {}
        self.default_result = MockCompletedProcess([], returncode=1)
        self.call_history: List[List[str]] = []

    def add_command_result(
        self,
        *command: str,
        stdout: str = '',
        stderr: str = '',
        returncode: int = 0
    ) -> None:
        """
        Add a predefined result for a specific command.

        Args:
            *command: Command components (e.g., 'git', 'status')
            stdout: Standard output to return
            stderr: Standard error to return
            returncode: Exit code to return

        Example:
            mock.add_command_result('git', 'branch', stdout='main\\nfeature/test')
        """
        key = tuple(command)
        self.command_results[key] = MockCompletedProcess(
            list(command),
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    def add_git_result(
        self,
        git_command: List[str],
        stdout: str = '',
        stderr: str = '',
        returncode: int = 0
    ) -> None:
        """
        Add a predefined result for a git command.

        Args:
            git_command: Git command without 'git' prefix
            stdout: Standard output to return
            stderr: Standard error to return
            returncode: Exit code to return

        Example:
            mock.add_git_result(['branch', '--format=%(refname:short)'], stdout='main')
        """
        self.add_command_result(
            'git',
            *git_command,
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    def set_default_result(
        self,
        stdout: str = '',
        stderr: str = '',
        returncode: int = 1
    ) -> None:
        """
        Set the default result for unrecognized commands.

        Args:
            stdout: Standard output to return
            stderr: Standard error to return
            returncode: Exit code to return
        """
        self.default_result = MockCompletedProcess(
            [],
            stdout=stdout,
            stderr=stderr,
            returncode=returncode
        )

    def run(
        self,
        args: List[str],
        capture_output: bool = False,
        text: bool = False,
        check: bool = False,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> MockCompletedProcess:
        """
        Mock subprocess.run() that returns predefined results.

        Args:
            args: Command to execute
            capture_output: Whether to capture output (ignored in mock)
            text: Whether to return text (ignored in mock)
            check: Whether to raise exception on non-zero exit (ignored in mock)
            cwd: Working directory (ignored in mock)
            env: Environment variables (ignored in mock)
            input: Input to provide (ignored in mock)
            timeout: Timeout (ignored in mock)

        Returns:
            MockCompletedProcess with predefined output

        Raises:
            KeyError: If command not found and no default set
        """
        self.call_history.append(args)

        key = tuple(args)
        if key in self.command_results:
            result = self.command_results[key]
        else:
            result = self.default_result

        # Create a new instance to avoid mutating stored results
        return MockCompletedProcess(
            args,
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode
        )

    def get_call_count(self, *command: str) -> int:
        """
        Get the number of times a command was called.

        Args:
            *command: Command components to count

        Returns:
            Number of times the command was called

        Example:
            mock.add_command_result('git', 'status', stdout='On branch main')
            mock.run(['git', 'status'])
            mock.run(['git', 'status'])
            assert mock.get_call_count('git', 'status') == 2
        """
        key = tuple(command)
        return sum(1 for call in self.call_history if tuple(call) == key)

    def was_called(self, *command: str) -> bool:
        """
        Check if a command was called.

        Args:
            *command: Command components to check

        Returns:
            True if command was called at least once

        Example:
            mock.run(['git', 'status'])
            assert mock.was_called('git', 'status')
        """
        return self.get_call_count(*command) > 0

    def reset(self) -> None:
        """Clear all command results and call history."""
        self.command_results.clear()
        self.call_history.clear()
        self.default_result = MockCompletedProcess([], returncode=1)

    def add_common_git_responses(self) -> None:
        """
        Add predefined responses for common git commands.

        This populates the mock with standard responses for:
        - git status
        - git branch
        - git rev-parse
        - git checkout
        - git config
        """
        # git status
        self.add_git_result(
            ['status'],
            stdout='On branch main\nnothing to commit, working tree clean'
        )

        # git branch
        self.add_git_result(
            ['branch'],
            stdout='  feature/001-test-feature\n* main'
        )

        self.add_git_result(
            ['branch', '--format=%(refname:short)'],
            stdout='feature/001-test-feature\nmain'
        )

        # git rev-parse
        self.add_git_result(
            ['rev-parse', '--abbrev-ref', 'HEAD'],
            stdout='main'
        )

        # git checkout (success)
        self.add_git_result(
            ['checkout', '-b'],
            returncode=0
        )

        # git config
        self.add_git_result(
            ['config', 'user.email'],
            stdout='test@example.com'
        )

        self.add_git_result(
            ['config', 'user.name'],
            stdout='Test User'
        )


# Convenience function for creating a pre-configured mock
def create_git_mock() -> MockSubprocess:
    """
    Create a MockSubprocess pre-configured with common git responses.

    Returns:
        MockSubprocess with common git command responses

    Example:
        mock = create_git_mock()
        result = mock.run(['git', 'status'])
        assert 'On branch main' in result.stdout
    """
    mock = MockSubprocess()
    mock.add_common_git_responses()
    return mock
