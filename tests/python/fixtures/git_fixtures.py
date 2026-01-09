"""
Git Test Fixtures

This module provides fixtures for creating and managing git repositories
in tests. All fixtures properly clean up after themselves to ensure
no test artifacts are left on the filesystem.

Classes:
    GitRepositoryFixture: Creates a temporary git repository for testing
    GitBranchFixture: Creates test branches with naming patterns
"""

import os
import subprocess
import tempfile
import unittest
from typing import List, Optional


class GitRepositoryFixture(unittest.TestCase):
    """
    Fixture for creating temporary git repositories in tests.

    This fixture creates a temporary directory, initializes it as a git
    repository, and configures a test user. The repository is automatically
    cleaned up in tearDown.

    Attributes:
        repo_path (str): Path to the temporary git repository
        original_dir (str): Original working directory before setup

    Example:
        class MyTestCase(GitRepositoryFixture):
            def test_something(self):
                # self.repo_path is available here
                # Create files, commit, etc.
                pass
    """

    def setUp(self):
        """Set up a temporary git repository for testing."""
        super().setUp()
        self.original_dir = os.getcwd()
        self.repo_path = tempfile.mkdtemp(prefix='git_test_repo_')

        # Initialize git repository
        subprocess.run(
            ['git', 'init'],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )

        # Configure test user
        subprocess.run(
            ['git', 'config', 'user.email', 'test@example.com'],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ['git', 'config', 'user.name', 'Test User'],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )

        # Create initial commit
        readme_path = os.path.join(self.repo_path, 'README.md')
        with open(readme_path, 'w') as f:
            f.write('# Test Repository\n')

        subprocess.run(
            ['git', 'add', 'README.md'],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ['git', 'commit', '-m', 'Initial commit'],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )

    def tearDown(self):
        """Clean up the temporary git repository."""
        super().tearDown()
        os.chdir(self.original_dir)

        # Clean up temporary directory
        import shutil
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path)

    def create_file_in_repo(self, path: str, content: str) -> str:
        """
        Create a file in the test repository.

        Args:
            path: Relative path from repository root
            content: Content to write to the file

        Returns:
            Absolute path to the created file
        """
        file_path = os.path.join(self.repo_path, path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w') as f:
            f.write(content)

        return file_path

    def commit_file(self, path: str, message: str = 'Commit file') -> None:
        """
        Stage and commit a file in the repository.

        Args:
            path: Relative path from repository root
            message: Commit message
        """
        subprocess.run(
            ['git', 'add', path],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ['git', 'commit', '-m', message],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )

    def get_current_branch(self) -> str:
        """
        Get the name of the current branch.

        Returns:
            Current branch name
        """
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def get_branch_list(self) -> List[str]:
        """
        Get a list of all branches in the repository.

        Returns:
            List of branch names
        """
        result = subprocess.run(
            ['git', 'branch', '--format', '%(refname:short)'],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []


class GitBranchFixture(GitRepositoryFixture):
    """
    Fixture for creating test branches with naming patterns.

    Extends GitRepositoryFixture to add branch creation capabilities.
    Supports the standard branch naming pattern used by the .zo scripts.

    Attributes:
        base_branch (str): Name of the base branch (default: 'main')

    Example:
        class MyTestCase(GitBranchFixture):
            def test_branch_creation(self):
                branch_name = self.create_feature_branch('001', 'test-feature')
                self.assertEqual(branch_name, 'feature/001-test-feature')
    """

    def setUp(self):
        """Set up the repository with a main branch."""
        super().setUp()
        self.base_branch = 'main'

    def create_branch(
        self,
        branch_name: str,
        switch_to: bool = True
    ) -> str:
        """
        Create a new branch in the repository.

        Args:
            branch_name: Name for the new branch
            switch_to: Whether to switch to the new branch (default: True)

        Returns:
            Name of the created branch
        """
        subprocess.run(
            ['git', 'checkout', '-b', branch_name],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )

        if not switch_to:
            subprocess.run(
                ['git', 'checkout', self.base_branch],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

        return branch_name

    def create_feature_branch(
        self,
        feature_id: str,
        feature_name: str
    ) -> str:
        """
        Create a feature branch with the standard naming pattern.

        Args:
            feature_id: Feature identifier (e.g., '001')
            feature_name: Feature name (kebab-case, e.g., 'my-new-feature')

        Returns:
            Full branch name (e.g., 'feature/001-my-new-feature')
        """
        branch_name = f'feature/{feature_id}-{feature_name}'
        return self.create_branch(branch_name)

    def switch_to_branch(self, branch_name: str) -> None:
        """
        Switch to an existing branch.

        Args:
            branch_name: Name of the branch to switch to
        """
        subprocess.run(
            ['git', 'checkout', branch_name],
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )

    def delete_branch(self, branch_name: str, force: bool = False) -> None:
        """
        Delete a branch from the repository.

        Args:
            branch_name: Name of the branch to delete
            force: Force deletion even if not merged (default: False)
        """
        args = ['git', 'branch', '-d', branch_name]
        if force:
            args[2] = '-D'

        subprocess.run(
            args,
            cwd=self.repo_path,
            check=True,
            capture_output=True
        )
