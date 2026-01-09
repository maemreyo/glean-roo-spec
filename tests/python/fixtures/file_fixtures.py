"""
File System Test Fixtures

This module provides fixtures for creating and managing temporary file
structures in tests. All fixtures properly clean up after themselves.

Classes:
    TempDirectoryFixture: Creates temporary directory structures
    FeatureDirectoryFixture: Creates feature directory structures
    TemplateFixture: Creates and manages test templates
"""

import os
import shutil
import tempfile
import unittest
from typing import Dict, List, Optional


class TempDirectoryFixture(unittest.TestCase):
    """
    Fixture for creating temporary directory structures in tests.

    This fixture creates a temporary directory that can be used for
    testing file operations. The directory is automatically cleaned up
    in tearDown.

    Attributes:
        temp_dir (str): Path to the temporary directory
        original_dir (str): Original working directory before setup

    Example:
        class MyTestCase(TempDirectoryFixture):
            def test_file_operations(self):
                # self.temp_dir is available here
                file_path = os.path.join(self.temp_dir, 'test.txt')
                with open(file_path, 'w') as f:
                    f.write('test content')
    """

    def setUp(self):
        """Set up a temporary directory for testing."""
        super().setUp()
        self.original_dir = os.getcwd()
        self.temp_dir = tempfile.mkdtemp(prefix='temp_test_dir_')

    def tearDown(self):
        """Clean up the temporary directory."""
        super().tearDown()
        os.chdir(self.original_dir)

        # Clean up temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_file(self, path: str, content: str) -> str:
        """
        Create a file in the temporary directory.

        Args:
            path: Relative path from temp_dir
            content: Content to write to the file

        Returns:
            Absolute path to the created file
        """
        file_path = os.path.join(self.temp_dir, path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w') as f:
            f.write(content)

        return file_path

    def create_directory(self, path: str) -> str:
        """
        Create a directory in the temporary directory.

        Args:
            path: Relative path from temp_dir

        Returns:
            Absolute path to the created directory
        """
        dir_path = os.path.join(self.temp_dir, path)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    def file_exists(self, path: str) -> bool:
        """
        Check if a file exists in the temporary directory.

        Args:
            path: Relative path from temp_dir

        Returns:
            True if file exists, False otherwise
        """
        file_path = os.path.join(self.temp_dir, path)
        return os.path.isfile(file_path)

    def directory_exists(self, path: str) -> bool:
        """
        Check if a directory exists in the temporary directory.

        Args:
            path: Relative path from temp_dir

        Returns:
            True if directory exists, False otherwise
        """
        dir_path = os.path.join(self.temp_dir, path)
        return os.path.isdir(dir_path)

    def read_file(self, path: str) -> str:
        """
        Read a file from the temporary directory.

        Args:
            path: Relative path from temp_dir

        Returns:
            File content as string
        """
        file_path = os.path.join(self.temp_dir, path)
        with open(file_path, 'r') as f:
            return f.read()

    def list_directory(self, path: str = '') -> List[str]:
        """
        List contents of a directory in the temporary directory.

        Args:
            path: Relative path from temp_dir (default: root)

        Returns:
            List of file/directory names
        """
        dir_path = os.path.join(self.temp_dir, path) if path else self.temp_dir
        return os.listdir(dir_path) if os.path.exists(dir_path) else []


class FeatureDirectoryFixture(TempDirectoryFixture):
    """
    Fixture for creating feature directory structures in tests.

    Extends TempDirectoryFixture to add feature-specific directory
    creation capabilities following the .zo directory structure.

    Attributes:
        feature_id: Feature identifier (e.g., '001')
        feature_name: Feature name (e.g., 'test-feature')

    Example:
        class MyTestCase(FeatureDirectoryFixture):
            def test_feature_structure(self):
                feature_dir = self.create_feature_directory('001', 'test-feature')
                # Creates: .zo/features/001-test-feature/
    """

    def setUp(self):
        """Set up the temporary directory."""
        super().setUp()
        self.feature_id = None
        self.feature_name = None

    def create_feature_directory(
        self,
        feature_id: str,
        feature_name: str
    ) -> str:
        """
        Create a feature directory with standard structure.

        Args:
            feature_id: Feature identifier (e.g., '001')
            feature_name: Feature name (kebab-case)

        Returns:
            Path to the created feature directory
        """
        self.feature_id = feature_id
        self.feature_name = feature_name

        feature_dir_name = f'{feature_id}-{feature_name}'
        feature_path = os.path.join('.zo', 'features', feature_dir_name)

        # Create standard feature structure
        directories = [
            feature_path,
            os.path.join(feature_path, 'specs'),
            os.path.join(feature_path, 'templates'),
            os.path.join(feature_path, 'implementation'),
        ]

        for directory in directories:
            self.create_directory(directory)

        return feature_path

    def create_spec_file(
        self,
        content: str,
        spec_name: str = 'spec.md'
    ) -> str:
        """
        Create a spec file in the feature directory.

        Args:
            content: Spec file content
            spec_name: Name of the spec file

        Returns:
            Path to the created spec file
        """
        if not self.feature_id or not self.feature_name:
            raise ValueError('Feature directory not created. Call create_feature_directory first.')

        feature_dir_name = f'{self.feature_id}-{self.feature_name}'
        spec_path = os.path.join('.zo', 'features', feature_dir_name, 'specs', spec_name)

        return self.create_file(spec_path, content)

    def create_template_file(
        self,
        content: str,
        template_name: str
    ) -> str:
        """
        Create a template file in the feature directory.

        Args:
            content: Template file content
            template_name: Name of the template file

        Returns:
            Path to the created template file
        """
        if not self.feature_id or not self.feature_name:
            raise ValueError('Feature directory not created. Call create_feature_directory first.')

        feature_dir_name = f'{self.feature_id}-{self.feature_name}'
        template_path = os.path.join('.zo', 'features', feature_dir_name, 'templates', template_name)

        return self.create_file(template_path, content)


class TemplateFixture(TempDirectoryFixture):
    """
    Fixture for creating and managing test templates.

    This fixture provides utilities for creating template files with
    placeholders and performing template variable substitution.

    Attributes:
        templates: Dictionary of template contents
        variables: Dictionary of template variables

    Example:
        class MyTestCase(TemplateFixture):
            def test_template_rendering(self):
                template = self.create_template('test.md', '{{NAME}}')
                result = self.render_template(template, {'NAME': 'value'})
    """

    def setUp(self):
        """Set up the template fixture."""
        super().setUp()
        self.templates: Dict[str, str] = {}
        self.variables: Dict[str, str] = {}

    def create_template(
        self,
        name: str,
        content: str,
        placeholders: Optional[List[str]] = None
    ) -> str:
        """
        Create a template file with placeholders.

        Args:
            name: Template file name
            content: Template content with placeholders
            placeholders: List of placeholder names (default: auto-detect)

        Returns:
            Path to the created template file
        """
        template_path = self.create_file(name, content)
        self.templates[name] = content

        if placeholders is None:
            # Auto-detect placeholders (e.g., {{PLACEHOLDER}})
            import re
            placeholders = re.findall(r'\{\{(\w+)\}\}', content)

        return template_path

    def render_template(
        self,
        template_content: str,
        variables: Dict[str, str]
    ) -> str:
        """
        Render a template with variable substitution.

        Args:
            template_content: Template content with placeholders
            variables: Dictionary of variable values

        Returns:
            Rendered content with placeholders replaced
        """
        result = template_content
        for key, value in variables.items():
            result = result.replace(f'{{{{{key}}}}}', str(value))

        return result

    def render_template_file(
        self,
        template_path: str,
        variables: Dict[str, str],
        output_path: Optional[str] = None
    ) -> str:
        """
        Render a template file and write to output.

        Args:
            template_path: Path to template file (relative to temp_dir)
            variables: Dictionary of variable values
            output_path: Output file path (default: template_path without .template)

        Returns:
            Path to the rendered file
        """
        content = self.read_file(template_path)
        rendered = self.render_template(content, variables)

        if output_path is None:
            output_path = template_path.replace('.template', '')

        return self.create_file(output_path, rendered)

    def create_standard_template(self, template_type: str) -> str:
        """
        Create a standard template with common placeholders.

        Args:
            template_type: Type of template ('plan', 'spec', or 'readme')

        Returns:
            Path to the created template file
        """
        templates = {
            'plan': """# Feature Plan: {{FEATURE_NAME}}

**Feature ID:** {{FEATURE_ID}}
**Created:** {{DATE}}
**Status:** {{STATUS}}

## Overview

{{OVERVIEW}}

## Primary Dependencies

{{DEPENDENCIES}}

## Storage Requirements

{{STORAGE}}
""",
            'spec': """# {{FEATURE_NAME}} Specification

## Overview

{{OVERVIEW}}

## Requirements

{{REQUIREMENTS}}

## Implementation

{{IMPLEMENTATION}}
""",
            'readme': """# {{FEATURE_NAME}}

{{DESCRIPTION}}

## Installation

{{INSTALLATION}}

## Usage

{{USAGE}}
"""
        }

        if template_type not in templates:
            raise ValueError(f'Unknown template type: {template_type}')

        return self.create_template(
            f'{template_type}.md.template',
            templates[template_type]
        )
