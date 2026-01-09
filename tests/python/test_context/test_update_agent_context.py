"""
Test suite for update-agent-context.py script.

This module tests the update-agent-context.py script which updates AI agent
context files with information from plan.md files.

Test Classes:
    TestValidation: Tests environment validation functions
    TestPlanParsing: Tests plan field extraction and parsing
    TestContentGeneration: Tests content generation functions
    TestFileManagement: Tests file creation and update operations
    TestAgentSelection: Tests agent selection and processing
    TestScriptExecution: Tests end-to-end script execution
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import tempfile
import shutil

# Add script directory to path
script_dir = Path(__file__).parent.parent.parent / '.zo' / 'scripts' / 'python'
sys.path.insert(0, str(script_dir))

from tests.python.fixtures.git_fixtures import GitBranchFixture
from tests.python.fixtures.file_fixtures import TempDirectoryFixture
from tests.python.helpers.assertion_helpers import (
    assert_file_exists,
    assert_file_contains,
)
from tests.python.helpers.output_helpers import (
    run_python_script,
    ProcessResult
)


class TestValidation(unittest.TestCase):
    """Test environment validation functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Import functions to test
        with patch('sys.argv', ['update-agent-context.py']):
            from update_agent_context import validate_environment
            self.validate_environment = validate_environment

    @patch('update_agent_context.sys.exit')
    def test_validate_environment_with_valid_env(self, mock_exit):
        """Test validation passes with valid environment."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_file = os.path.join(temp_dir, 'plan.md')
            template_file = os.path.join(temp_dir, 'template.md')
            
            # Create plan.md
            with open(plan_file, 'w') as f:
                f.write('# Plan\n')
            
            # Create template
            with open(template_file, 'w') as f:
                f.write('# Template\n')
            
            # Act
            self.validate_environment(temp_dir, 'feature/001-test', plan_file, template_file)
            
            # Assert - should not call sys.exit
            mock_exit.assert_not_called()

    @patch('update_agent_context.sys.exit')
    @patch('update_agent_context.log_error')
    def test_validate_environment_fails_on_main_branch(self, mock_log_error, mock_exit):
        """Test validation fails when on main branch."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_file = os.path.join(temp_dir, 'plan.md')
            template_file = os.path.join(temp_dir, 'template.md')
            
            with open(plan_file, 'w') as f:
                f.write('# Plan\n')
            
            # Act
            self.validate_environment(temp_dir, 'main', plan_file, template_file)
            
            # Assert
            mock_exit.assert_called_once_with(1)

    @patch('update_agent_context.sys.exit')
    @patch('update_agent_context.log_error')
    def test_validate_environment_fails_with_missing_plan(self, mock_log_error, mock_exit):
        """Test validation fails when plan.md is missing."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_file = os.path.join(temp_dir, 'plan.md')
            template_file = os.path.join(temp_dir, 'template.md')
            
            # Don't create plan.md
            
            # Act
            self.validate_environment(temp_dir, 'feature/001-test', plan_file, template_file)
            
            # Assert
            mock_exit.assert_called_once_with(1)

    @patch('update_agent_context.log_warning')
    def test_validate_environment_warns_missing_template(self, mock_log_warning):
        """Test validation warns when template is missing but doesn't exit."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_file = os.path.join(temp_dir, 'plan.md')
            template_file = os.path.join(temp_dir, 'template.md')
            
            # Create plan.md but not template
            with open(plan_file, 'w') as f:
                f.write('# Plan\n')
            
            # Act
            self.validate_environment(temp_dir, 'feature/001-test', plan_file, template_file)
            
            # Assert - should warn but not exit
            mock_log_warning.assert_called()


class TestPlanParsing(unittest.TestCase):
    """Test plan field extraction and parsing functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Import functions to test
        with patch('sys.argv', ['update-agent-context.py']):
            from update_agent_context import (
                extract_plan_field,
                parse_plan_data,
                NEW_LANG,
                NEW_FRAMEWORK,
                NEW_DB,
                NEW_PROJECT_TYPE
            )
            self.extract_plan_field = extract_plan_field
            self.parse_plan_data = parse_plan_data

    def test_extract_plan_field_language_version(self):
        """Test extracting Language/Version field from plan."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write('# Plan\n\n')
            f.write('**Language/Version**: Python 3.11+\n')
            f.write('**Other Field**: value\n')
            plan_file = f.name
        
        try:
            # Act
            result = self.extract_plan_field(plan_file, "Language/Version")
            
            # Assert
            self.assertEqual(result, "Python 3.11+")
        finally:
            os.unlink(plan_file)

    def test_extract_plan_field_primary_dependencies(self):
        """Test extracting Primary Dependencies field from plan."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write('# Plan\n\n')
            f.write('**Primary Dependencies**: React 18.2+, Next.js 14+\n')
            plan_file = f.name
        
        try:
            # Act
            result = self.extract_plan_field(plan_file, "Primary Dependencies")
            
            # Assert
            self.assertEqual(result, "React 18.2+, Next.js 14+")
        finally:
            os.unlink(plan_file)

    def test_extract_plan_field_storage(self):
        """Test extracting Storage field from plan."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write('# Plan\n\n')
            f.write('**Storage**: PostgreSQL 14+\n')
            plan_file = f.name
        
        try:
            # Act
            result = self.extract_plan_field(plan_file, "Storage")
            
            # Assert
            self.assertEqual(result, "PostgreSQL 14+")
        finally:
            os.unlink(plan_file)

    def test_extract_plan_field_filters_needs_clarification(self):
        """Test that NEEDS CLARIFICATION values are filtered out."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write('# Plan\n\n')
            f.write('**Language/Version**: NEEDS CLARIFICATION\n')
            plan_file = f.name
        
        try:
            # Act
            result = self.extract_plan_field(plan_file, "Language/Version")
            
            # Assert
            self.assertEqual(result, "")
        finally:
            os.unlink(plan_file)

    def test_extract_plan_field_filters_n_a(self):
        """Test that N/A values are filtered out."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write('# Plan\n\n')
            f.write('**Storage**: N/A\n')
            plan_file = f.name
        
        try:
            # Act
            result = self.extract_plan_field(plan_file, "Storage")
            
            # Assert
            self.assertEqual(result, "")
        finally:
            os.unlink(plan_file)

    def test_extract_plan_field_returns_empty_when_not_found(self):
        """Test that empty string is returned when field is not found."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write('# Plan\n\n')
            f.write('**Other Field**: value\n')
            plan_file = f.name
        
        try:
            # Act
            result = self.extract_plan_field(plan_file, "Language/Version")
            
            # Assert
            self.assertEqual(result, "")
        finally:
            os.unlink(plan_file)

    @patch('update_agent_context.parse_plan_data')
    @patch('update_agent_context.sys.exit')
    def test_parse_plan_data_exits_on_missing_file(self, mock_exit, mock_parse):
        """Test parse_plan_data exits when plan file doesn't exist."""
        # Arrange - don't create file
        non_existent_file = '/tmp/non_existent_plan_12345.md'
        
        # Act
        self.parse_plan_data(non_existent_file)
        
        # Assert
        mock_exit.assert_called_once_with(1)


class TestContentGeneration(unittest.TestCase):
    """Test content generation functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Import functions to test
        with patch('sys.argv', ['update-agent-context.py']):
            from update_agent_context import (
                format_technology_stack,
                get_project_structure,
                get_commands_for_language,
                get_language_conventions
            )
            self.format_technology_stack = format_technology_stack
            self.get_project_structure = get_project_structure
            self.get_commands_for_language = get_commands_for_language
            self.get_language_conventions = get_language_conventions

    def test_format_technology_stack_with_both(self):
        """Test formatting tech stack with both language and framework."""
        # Act
        result = self.format_technology_stack("Python 3.11+", "FastAPI")
        
        # Assert
        self.assertEqual(result, "Python 3.11+ + FastAPI")

    def test_format_technology_stack_with_language_only(self):
        """Test formatting tech stack with only language."""
        # Act
        result = self.format_technology_stack("Python 3.11+", "")
        
        # Assert
        self.assertEqual(result, "Python 3.11+")

    def test_format_technology_stack_with_framework_only(self):
        """Test formatting tech stack with only framework."""
        # Act
        result = self.format_technology_stack("", "React 18.2+")
        
        # Assert
        self.assertEqual(result, "React 18.2+")

    def test_format_technology_stack_filters_needs_clarification(self):
        """Test that NEEDS CLARIFICATION is filtered out."""
        # Act
        result = self.format_technology_stack("NEEDS CLARIFICATION", "React")
        
        # Assert
        self.assertEqual(result, "React")

    def test_format_technology_stack_filters_n_a(self):
        """Test that N/A is filtered out."""
        # Act
        result = self.format_technology_stack("Python", "N/A")
        
        # Assert
        self.assertEqual(result, "Python")

    def test_format_technology_stack_empty(self):
        """Test formatting tech stack with empty values."""
        # Act
        result = self.format_technology_stack("", "")
        
        # Assert
        self.assertEqual(result, "")

    def test_get_project_structure_web(self):
        """Test getting project structure for web projects."""
        # Act
        result = self.get_project_structure("web application")
        
        # Assert
        self.assertEqual(result, "backend/\nfrontend/\ntests/")

    def test_get_project_structure_non_web(self):
        """Test getting project structure for non-web projects."""
        # Act
        result = self.get_project_structure("CLI tool")
        
        # Assert
        self.assertEqual(result, "src/\ntests/")

    def test_get_project_structure_empty(self):
        """Test getting project structure with empty type."""
        # Act
        result = self.get_project_structure("")
        
        # Assert
        self.assertEqual(result, "src/\ntests/")

    def test_get_commands_for_language_python(self):
        """Test getting commands for Python."""
        # Act
        result = self.get_commands_for_language("Python 3.11+")
        
        # Assert
        self.assertEqual(result, "cd src && pytest && ruff check .")

    def test_get_commands_for_language_rust(self):
        """Test getting commands for Rust."""
        # Act
        result = self.get_commands_for_language("Rust 1.75")
        
        # Assert
        self.assertEqual(result, "cargo test && cargo clippy")

    def test_get_commands_for_language_javascript(self):
        """Test getting commands for JavaScript."""
        # Act
        result = self.get_commands_for_language("JavaScript ES2022")
        
        # Assert
        self.assertEqual(result, "npm test && npm run lint")

    def test_get_commands_for_language_typescript(self):
        """Test getting commands for TypeScript."""
        # Act
        result = self.get_commands_for_language("TypeScript 5.3+")
        
        # Assert
        self.assertEqual(result, "npm test && npm run lint")

    def test_get_commands_for_language_unknown(self):
        """Test getting commands for unknown language."""
        # Act
        result = self.get_commands_for_language("Go 1.21")
        
        # Assert
        self.assertEqual(result, "# Add commands for Go 1.21")

    def test_get_language_conventions(self):
        """Test getting language conventions."""
        # Act
        result = self.get_language_conventions("Python 3.11+")
        
        # Assert
        self.assertEqual(result, "Python 3.11+: Follow standard conventions")


class TestFileManagement(TempDirectoryFixture):
    """Test file creation and update operations."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Import functions to test
        with patch('sys.argv', ['update-agent-context.py']):
            from update_agent_context import (
                create_new_agent_file,
                update_existing_agent_file,
                update_agent_file,
                NEW_LANG,
                NEW_FRAMEWORK,
                NEW_DB,
                NEW_PROJECT_TYPE
            )
            self.create_new_agent_file = create_new_agent_file
            self.update_existing_agent_file = update_existing_agent_file
            self.update_agent_file = update_agent_file
            
            # Set global variables
            import update_agent_context
            update_agent_context.NEW_LANG = "Python 3.11+"
            update_agent_context.NEW_FRAMEWORK = "FastAPI"
            update_agent_context.NEW_DB = "PostgreSQL"
            update_agent_context.NEW_PROJECT_TYPE = "web application"

    def test_create_new_agent_file_with_template(self):
        """Test creating new agent file from template."""
        # Arrange
        template_content = """# [PROJECT NAME]

**Last updated**: [DATE]

## Active Technologies
[EXTRACTED FROM ALL PLAN.MD FILES]

## Project Structure
[ACTUAL STRUCTURE FROM PLANS]

## Commands
[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]

## Code Style
[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]

## Recent Changes
[LAST 3 FEATURES AND WHAT THEY ADDED]
"""
        template_dir = self.create_directory('.zo/templates')
        template_file = os.path.join(template_dir, 'agent-file-template.md')
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        target_file = os.path.join(self.temp_dir, 'CLAUDE.md')
        temp_file = os.path.join(self.temp_dir, 'temp_agent.md')
        
        # Mock get_current_branch
        with patch('update_agent_context.get_current_branch') as mock_branch:
            mock_branch.return_value = 'feature/001-test-feature'
            
            # Act
            result = self.create_new_agent_file(
                target_file, temp_file, 'test-project', '2026-01-09', self.temp_dir
            )
            
            # Assert
            self.assertTrue(result)
            self.assertTrue(os.path.exists(temp_file))
            
            # Check content was substituted
            with open(temp_file, 'r') as f:
                content = f.read()
                self.assertIn('test-project', content)
                self.assertIn('2026-01-09', content)
                self.assertIn('Active Technologies', content)

    def test_create_new_agent_file_fails_without_template(self):
        """Test that creating new agent file fails without template."""
        # Arrange
        target_file = os.path.join(self.temp_dir, 'CLAUDE.md')
        temp_file = os.path.join(self.temp_dir, 'temp_agent.md')
        
        # Don't create template
        
        # Act
        result = self.create_new_agent_file(
            target_file, temp_file, 'test-project', '2026-01-09', self.temp_dir
        )
        
        # Assert
        self.assertFalse(result)
        self.assertFalse(os.path.exists(temp_file))

    def test_update_existing_agent_file_adds_tech_stack(self):
        """Test updating existing file adds new tech stack entry."""
        # Arrange
        existing_content = """# Project Rules

## Active Technologies

## Recent Changes

**Last updated**: 2026-01-01
"""
        target_file = self.create_file('CLAUDE.md', existing_content)
        
        # Mock get_current_branch
        with patch('update_agent_context.get_current_branch') as mock_branch:
            mock_branch.return_value = 'feature/001-test-feature'
            
            # Act
            self.update_existing_agent_file(target_file, '2026-01-09')
            
            # Assert
            with open(target_file, 'r') as f:
                content = f.read()
                # Should add tech stack entry
                self.assertIn('Active Technologies', content)
                # Should update date
                self.assertIn('2026-01-09', content)
                self.assertNotIn('2026-01-01', content)

    def test_update_existing_agent_file_preserves_manual_additions(self):
        """Test that manual additions are preserved during update."""
        # Arrange
        existing_content = """# Project Rules

## Active Technologies
- Python 3.10+ (feature/000-old-feature)
- Custom Tool (manual addition)

## Recent Changes
- feature/000-old-feature: Added Python 3.10+

**Last updated**: 2026-01-01

## Custom Section
This should be preserved.
"""
        target_file = self.create_file('CLAUDE.md', existing_content)
        
        # Mock get_current_branch
        with patch('update_agent_context.get_current_branch') as mock_branch:
            mock_branch.return_value = 'feature/001-new-feature'
            
            # Act
            self.update_existing_agent_file(target_file, '2026-01-09')
            
            # Assert
            with open(target_file, 'r') as f:
                content = f.read()
                # Manual additions should be preserved
                self.assertIn('Custom Tool (manual addition)', content)
                self.assertIn('This should be preserved.', content)
                # New entry should be added
                self.assertIn('feature/001-new-feature', content)

    def test_update_agent_file_creates_new_when_missing(self):
        """Test that update_agent_file creates new file when missing."""
        # Arrange
        template_content = "# [PROJECT NAME]\n[DATE]"
        template_dir = self.create_directory('.zo/templates')
        template_file = os.path.join(template_dir, 'agent-file-template.md')
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        target_file = os.path.join(self.temp_dir, 'CLAUDE.md')
        
        # Mock get_current_branch
        with patch('update_agent_context.get_current_branch') as mock_branch:
            mock_branch.return_value = 'feature/001-test'
            
            # Act
            self.update_agent_file(target_file, "Claude Code", self.temp_dir)
            
            # Assert
            self.assertTrue(os.path.exists(target_file))

    def test_update_agent_file_updates_existing(self):
        """Test that update_agent_file updates existing file."""
        # Arrange
        existing_content = """# Project Rules

## Active Technologies

## Recent Changes

**Last updated**: 2026-01-01
"""
        target_file = self.create_file('CLAUDE.md', existing_content)
        
        # Mock get_current_branch
        with patch('update_agent_context.get_current_branch') as mock_branch:
            mock_branch.return_value = 'feature/001-test'
            
            # Act
            self.update_agent_file(target_file, "Claude Code", self.temp_dir)
            
            # Assert
            self.assertTrue(os.path.exists(target_file))
            with open(target_file, 'r') as f:
                content = f.read()
                self.assertIn('2026-01-09', content)  # Date should be updated

    def test_update_agent_file_creates_nested_directory(self):
        """Test that update_agent_file creates nested directories if needed."""
        # Arrange
        template_content = "# [PROJECT NAME]"
        template_dir = self.create_directory('.zo/templates')
        template_file = os.path.join(template_dir, 'agent-file-template.md')
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        target_file = os.path.join(self.temp_dir, '.github', 'agents', 'copilot-instructions.md')
        
        # Mock get_current_branch
        with patch('update_agent_context.get_current_branch') as mock_branch:
            mock_branch.return_value = 'feature/001-test'
            
            # Act
            self.update_agent_file(target_file, "GitHub Copilot", self.temp_dir)
            
            # Assert
            self.assertTrue(os.path.exists(target_file))
            self.assertTrue(os.path.isdir(os.path.dirname(target_file)))


class TestAgentSelection(TempDirectoryFixture):
    """Test agent selection and processing functions."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Import functions to test
        with patch('sys.argv', ['update-agent-context.py']):
            from update_agent_context import (
                update_specific_agent,
                update_all_existing_agents,
                AGENT_FILES,
                AGENT_NAMES
            )
            self.update_specific_agent = update_specific_agent
            self.update_all_existing_agents = update_all_existing_agents
            self.AGENT_FILES = AGENT_FILES
            self.AGENT_NAMES = AGENT_NAMES

    def test_agent_files_dict_contains_all_16_types(self):
        """Test that AGENT_FILES contains all 16 agent types."""
        # Assert
        expected_agents = [
            'claude', 'gemini', 'copilot', 'cursor-agent', 'qwen', 
            'opencode', 'codex', 'windsurf', 'kilocode', 'auggie',
            'roo', 'codebuddy', 'qoder', 'amp', 'shai', 'q', 'bob'
        ]
        for agent in expected_agents:
            self.assertIn(agent, self.AGENT_FILES)

    def test_agent_names_dict_contains_all_16_types(self):
        """Test that AGENT_NAMES contains all 16 agent types."""
        # Assert
        expected_agents = [
            'claude', 'gemini', 'copilot', 'cursor-agent', 'qwen',
            'opencode', 'codex', 'windsurf', 'kilocode', 'auggie',
            'roo', 'codebuddy', 'qoder', 'amp', 'shai', 'q', 'bob'
        ]
        for agent in expected_agents:
            self.assertIn(agent, self.AGENT_NAMES)

    def test_update_specific_agent_claude(self):
        """Test updating specific agent: Claude."""
        # Arrange
        template_content = "# [PROJECT NAME]\n[DATE]"
        template_dir = self.create_directory('.zo/templates')
        template_file = os.path.join(template_dir, 'agent-file-template.md')
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        # Mock get_current_branch
        with patch('update_agent_context.get_current_branch') as mock_branch:
            mock_branch.return_value = 'feature/001-test'
            
            # Act
            self.update_specific_agent('claude', self.temp_dir)
            
            # Assert
            target_file = os.path.join(self.temp_dir, 'CLAUDE.md')
            self.assertTrue(os.path.exists(target_file))

    def test_update_specific_agent_gemini(self):
        """Test updating specific agent: Gemini."""
        # Arrange
        template_content = "# [PROJECT NAME]\n[DATE]"
        template_dir = self.create_directory('.zo/templates')
        template_file = os.path.join(template_dir, 'agent-file-template.md')
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        # Mock get_current_branch
        with patch('update_agent_context.get_current_branch') as mock_branch:
            mock_branch.return_value = 'feature/001-test'
            
            # Act
            self.update_specific_agent('gemini', self.temp_dir)
            
            # Assert
            target_file = os.path.join(self.temp_dir, 'GEMINI.md')
            self.assertTrue(os.path.exists(target_file))

    def test_update_specific_agent_copilot(self):
        """Test updating specific agent: Copilot."""
        # Arrange
        template_content = "# [PROJECT NAME]\n[DATE]"
        template_dir = self.create_directory('.zo/templates')
        template_file = os.path.join(template_dir, 'agent-file-template.md')
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        # Mock get_current_branch
        with patch('update_agent_context.get_current_branch') as mock_branch:
            mock_branch.return_value = 'feature/001-test'
            
            # Act
            self.update_specific_agent('copilot', self.temp_dir)
            
            # Assert
            target_file = os.path.join(self.temp_dir, '.github', 'agents', 'copilot-instructions.md')
            self.assertTrue(os.path.exists(target_file))

    def test_update_specific_agent_cursor(self):
        """Test updating specific agent: Cursor."""
        # Arrange
        template_content = "# [PROJECT NAME]\n[DATE]"
        template_dir = self.create_directory('.zo/templates')
        template_file = os.path.join(template_dir, 'agent-file-template.md')
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        # Mock get_current_branch
        with patch('update_agent_context.get_current_branch') as mock_branch:
            mock_branch.return_value = 'feature/001-test'
            
            # Act
            self.update_specific_agent('cursor-agent', self.temp_dir)
            
            # Assert
            target_file = os.path.join(self.temp_dir, '.cursor', 'rules', 'specify-rules.mdc')
            self.assertTrue(os.path.exists(target_file))

    def test_update_specific_agent_roo(self):
        """Test updating specific agent: Roo."""
        # Arrange
        template_content = "# [PROJECT NAME]\n[DATE]"
        template_dir = self.create_directory('.zo/templates')
        template_file = os.path.join(template_dir, 'agent-file-template.md')
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        # Mock get_current_branch
        with patch('update_agent_context.get_current_branch') as mock_branch:
            mock_branch.return_value = 'feature/001-test'
            
            # Act
            self.update_specific_agent('roo', self.temp_dir)
            
            # Assert
            target_file = os.path.join(self.temp_dir, '.roo', 'rules', 'specify-rules.md')
            self.assertTrue(os.path.exists(target_file))

    @patch('update_agent_context.sys.exit')
    def test_update_specific_agent_unknown_type(self, mock_exit):
        """Test updating specific agent with unknown type exits."""
        # Act
        self.update_specific_agent('unknown-agent', self.temp_dir)
        
        # Assert
        mock_exit.assert_called_once_with(1)

    def test_update_all_existing_agents_with_multiple_agents(self):
        """Test updating all existing agents when multiple exist."""
        # Arrange
        template_content = "# [PROJECT NAME]\n[DATE]"
        template_dir = self.create_directory('.zo/templates')
        template_file = os.path.join(template_dir, 'agent-file-template.md')
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        # Create existing agent files
        self.create_file('CLAUDE.md', '# Claude Rules')
        self.create_file('GEMINI.md', '# Gemini Rules')
        
        # Mock get_current_branch
        with patch('update_agent_context.get_current_branch') as mock_branch:
            mock_branch.return_value = 'feature/001-test'
            
            # Act
            self.update_all_existing_agents(self.temp_dir)
            
            # Assert
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'CLAUDE.md')))
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'GEMINI.md')))

    def test_update_all_existing_agents_creates_default_when_none_exist(self):
        """Test that default Claude file is created when no agents exist."""
        # Arrange
        template_content = "# [PROJECT NAME]\n[DATE]"
        template_dir = self.create_directory('.zo/templates')
        template_file = os.path.join(template_dir, 'agent-file-template.md')
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        # Don't create any agent files
        
        # Mock get_current_branch
        with patch('update_agent_context.get_current_branch') as mock_branch:
            mock_branch.return_value = 'feature/001-test'
            
            # Act
            self.update_all_existing_agents(self.temp_dir)
            
            # Assert
            target_file = os.path.join(self.temp_dir, 'CLAUDE.md')
            self.assertTrue(os.path.exists(target_file))


class TestScriptExecution(TempDirectoryFixture):
    """Test end-to-end script execution."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        super().tearDown()

    @patch('update_agent_context.get_repo_root')
    @patch('update_agent_context.get_current_branch')
    @patch('update_agent_context.get_feature_dir')
    def test_script_execution_success(self, mock_get_feature, mock_get_branch, mock_get_root):
        """Test successful script execution."""
        # Arrange
        mock_get_root.return_value = self.temp_dir
        mock_get_branch.return_value = 'feature/001-test-feature'
        mock_get_feature.return_value = self.temp_dir
        
        # Create required files
        plan_content = """# Feature Plan

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, pytest
**Storage**: PostgreSQL
**Project Type**: web application
"""
        plan_file = self.create_file('plan.md', plan_content)
        
        template_content = """# [PROJECT NAME]

**Last updated**: [DATE]

## Active Technologies
[EXTRACTED FROM ALL PLAN.MD FILES]

## Project Structure
[ACTUAL STRUCTURE FROM PLANS]

## Commands
[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]

## Code Style
[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]

## Recent Changes
[LAST 3 FEATURES AND WHAT THEY ADDED]
"""
        template_dir = self.create_directory('.zo/templates')
        template_file = os.path.join(template_dir, 'agent-file-template.md')
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        # Mock get_feature_dir to return correct path for plan.md
        mock_get_feature.side_effect = lambda repo, branch: self.temp_dir
        
        # Act
        result = run_python_script(
            str(script_dir / 'update-agent-context.py'),
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)

    @patch('update_agent_context.get_repo_root')
    @patch('update_agent_context.get_current_branch')
    @patch('update_agent_context.get_feature_dir')
    def test_script_with_specific_agent(self, mock_get_feature, mock_get_branch, mock_get_root):
        """Test script execution with specific agent type."""
        # Arrange
        mock_get_root.return_value = self.temp_dir
        mock_get_branch.return_value = 'feature/001-test-feature'
        mock_get_feature.side_effect = lambda repo, branch: self.temp_dir
        
        # Create required files
        plan_content = """# Feature Plan

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI
**Storage**: N/A
**Project Type**: CLI tool
"""
        plan_file = self.create_file('plan.md', plan_content)
        
        template_content = "# [PROJECT NAME]\n[DATE]"
        template_dir = self.create_directory('.zo/templates')
        template_file = os.path.join(template_dir, 'agent-file-template.md')
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        # Act
        result = run_python_script(
            str(script_dir / 'update-agent-context.py'),
            ['gemini'],
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'GEMINI.md')))

    @patch('update_agent_context.get_repo_root')
    @patch('update_agent_context.get_current_branch')
    @patch('update_agent_context.get_feature_dir')
    def test_script_fails_on_main_branch(self, mock_get_feature, mock_get_branch, mock_get_root):
        """Test script fails when on main branch."""
        # Arrange
        mock_get_root.return_value = self.temp_dir
        mock_get_branch.return_value = 'main'
        mock_get_feature.side_effect = lambda repo, branch: self.temp_dir
        
        # Create plan.md
        plan_file = self.create_file('plan.md', '# Plan\n')
        
        # Act
        result = run_python_script(
            str(script_dir / 'update-agent-context.py'),
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertFalse(result.success)
        self.assertIn('Unable to determine current feature', result.stderr)

    @patch('update_agent_context.get_repo_root')
    @patch('update_agent_context.get_current_branch')
    @patch('update_agent_context.get_feature_dir')
    def test_script_fails_with_missing_plan(self, mock_get_feature, mock_get_branch, mock_get_root):
        """Test script fails when plan.md is missing."""
        # Arrange
        mock_get_root.return_value = self.temp_dir
        mock_get_branch.return_value = 'feature/001-test'
        mock_get_feature.side_effect = lambda repo, branch: self.temp_dir
        
        # Don't create plan.md
        
        # Act
        result = run_python_script(
            str(script_dir / 'update-agent-context.py'),
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertFalse(result.success)
        self.assertIn('No plan.md found', result.stderr)

    @patch('update_agent_context.get_repo_root')
    @patch('update_agent_context.get_current_branch')
    @patch('update_agent_context.get_feature_dir')
    def test_script_preserves_existing_agent_content(self, mock_get_feature, mock_get_branch, mock_get_root):
        """Test that script preserves existing agent file content."""
        # Arrange
        mock_get_root.return_value = self.temp_dir
        mock_get_branch.return_value = 'feature/001-test'
        mock_get_feature.side_effect = lambda repo, branch: self.temp_dir
        
        # Create plan.md
        plan_content = """# Feature Plan

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI
**Storage**: N/A
**Project Type**: CLI tool
"""
        plan_file = self.create_file('plan.md', plan_content)
        
        # Create existing agent file with custom content
        existing_content = """# Project Rules

## Active Technologies
- Python 3.10+ (feature/000-old)

## Custom Section
This custom content should be preserved.
"""
        agent_file = self.create_file('CLAUDE.md', existing_content)
        
        # Act
        result = run_python_script(
            str(script_dir / 'update-agent-context.py'),
            cwd=self.temp_dir
        )
        
        # Assert
        self.assertTrue(result.success)
        with open(agent_file, 'r') as f:
            content = f.read()
            # Custom section should be preserved
            self.assertIn('This custom content should be preserved.', content)


if __name__ == '__main__':
    unittest.main()
