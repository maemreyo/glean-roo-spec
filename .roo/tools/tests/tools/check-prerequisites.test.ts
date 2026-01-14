/**
 * Tests for check_prerequisites tool
 *
 * Example test file demonstrating testing patterns for Roo Custom Tools.
 * This file serves as a template for testing other tools.
 *
 * @see {@link plans/migration/05-testing-strategy.md}
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

// Mock the file system modules before importing the tool
jest.mock('node:fs');
jest.mock('node:path');
jest.mock('child_process');

// Import tool after mocking
import checkPrerequisites from '../check-prerequisites.js';
import * as util from '../lib/util.js';

// Mock the utility functions
jest.mock('../lib/util.js');

describe('check_prerequisites', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('success scenarios', () => {
    it('should return valid feature paths when all prerequisites are met', async () => {
      // Arrange
      const mockPaths = {
        REPO_ROOT: '/repo/root',
        CURRENT_BRANCH: '001-test-feature',
        HAS_GIT: 'true',
        FEATURE_DIR: 'specs/001-test-feature',
        FEATURE_SPEC: 'specs/001-test-feature/spec.md',
        IMPL_PLAN: 'specs/001-test-feature/plan.md',
        TASKS: 'specs/001-test-feature/tasks.md',
        RESEARCH: 'specs/001-test-feature/research.md',
        DATA_MODEL: 'specs/001-test-feature/data-model.md',
        DESIGN_FILE: 'specs/001-test-feature/design.md',
        CONTRACTS_DIR: 'specs/001-test-feature/contracts',
        QUICKSTART: 'specs/001-test-feature/quickstart.md',
      };

      jest.spyOn(util, 'validateExecutionEnvironment').mockReturnValue(true);
      jest.spyOn(util, 'getFeaturePaths').mockReturnValue(mockPaths as any);
      jest.spyOn(util, 'checkFeatureBranch').mockReturnValue({ isValid: true });
      jest.spyOn(util, 'resolvePath').mockImplementation((p: string) => `/resolved/${p}`);
      jest.spyOn(util, 'checkFileExists').mockReturnValue(false);
      jest.spyOn(util, 'checkDirExistsWithFiles').mockReturnValue(false);

      // Act
      const result = await checkPrerequisites.execute({ json: true }, {});

      // Assert
      const parsed = JSON.parse(result);
      expect(parsed.VALID).toBe(true);
      expect(parsed.FEATURE_DIR).toBe('specs/001-test-feature');
      expect(Array.isArray(parsed.AVAILABLE_DOCS)).toBe(true);
    });

    it('should return available optional docs', async () => {
      // Arrange
      const mockPaths = {
        REPO_ROOT: '/repo/root',
        CURRENT_BRANCH: '001-test-feature',
        HAS_GIT: 'true',
        FEATURE_DIR: 'specs/001-test-feature',
        FEATURE_SPEC: 'specs/001-test-feature/spec.md',
        IMPL_PLAN: 'specs/001-test-feature/plan.md',
        TASKS: 'specs/001-test-feature/tasks.md',
        RESEARCH: 'specs/001-test-feature/research.md',
        DATA_MODEL: 'specs/001-test-feature/data-model.md',
        DESIGN_FILE: 'specs/001-test-feature/design.md',
        CONTRACTS_DIR: 'specs/001-test-feature/contracts',
        QUICKSTART: 'specs/001-test-feature/quickstart.md',
      };

      jest.spyOn(util, 'validateExecutionEnvironment').mockReturnValue(true);
      jest.spyOn(util, 'getFeaturePaths').mockReturnValue(mockPaths as any);
      jest.spyOn(util, 'checkFeatureBranch').mockReturnValue({ isValid: true });
      jest.spyOn(util, 'resolvePath').mockImplementation((p: string) => `/resolved/${p}`);
      jest.spyOn(util, 'checkFileExists').mockImplementation((path: string) => {
        return path.includes('research.md') || path.includes('contracts');
      });
      jest.spyOn(util, 'checkDirExistsWithFiles').mockReturnValue(true);

      // Act
      const result = await checkPrerequisites.execute({ json: true }, {});

      // Assert
      const parsed = JSON.parse(result);
      expect(parsed.AVAILABLE_DOCS).toContain('research.md');
      expect(parsed.AVAILABLE_DOCS).toContain('contracts/');
    });

    it('should include tasks.md when includeTasks is true', async () => {
      // Arrange
      const mockPaths = {
        REPO_ROOT: '/repo/root',
        CURRENT_BRANCH: '001-test-feature',
        HAS_GIT: 'true',
        FEATURE_DIR: 'specs/001-test-feature',
        FEATURE_SPEC: 'specs/001-test-feature/spec.md',
        IMPL_PLAN: 'specs/001-test-feature/plan.md',
        TASKS: 'specs/001-test-feature/tasks.md',
        RESEARCH: 'specs/001-test-feature/research.md',
        DATA_MODEL: 'specs/001-test-feature/data-model.md',
        DESIGN_FILE: 'specs/001-test-feature/design.md',
        CONTRACTS_DIR: 'specs/001-test-feature/contracts',
        QUICKSTART: 'specs/001-test-feature/quickstart.md',
      };

      jest.spyOn(util, 'validateExecutionEnvironment').mockReturnValue(true);
      jest.spyOn(util, 'getFeaturePaths').mockReturnValue(mockPaths as any);
      jest.spyOn(util, 'checkFeatureBranch').mockReturnValue({ isValid: true });
      jest.spyOn(util, 'resolvePath').mockImplementation((p: string) => `/resolved/${p}`);
      jest.spyOn(util, 'checkFileExists').mockReturnValue(true);
      jest.spyOn(util, 'checkDirExistsWithFiles').mockReturnValue(false);

      // Act
      const result = await checkPrerequisites.execute({ json: true, includeTasks: true }, {});

      // Assert
      const parsed = JSON.parse(result);
      expect(parsed.AVAILABLE_DOCS).toContain('tasks.md');
    });

    it('should output text format when json is false', async () => {
      // Arrange
      const mockPaths = {
        REPO_ROOT: '/repo/root',
        CURRENT_BRANCH: '001-test-feature',
        HAS_GIT: 'true',
        FEATURE_DIR: 'specs/001-test-feature',
        FEATURE_SPEC: 'specs/001-test-feature/spec.md',
        IMPL_PLAN: 'specs/001-test-feature/plan.md',
        TASKS: 'specs/001-test-feature/tasks.md',
        RESEARCH: 'specs/001-test-feature/research.md',
        DATA_MODEL: 'specs/001-test-feature/data-model.md',
        DESIGN_FILE: 'specs/001-test-feature/design.md',
        CONTRACTS_DIR: 'specs/001-test-feature/contracts',
        QUICKSTART: 'specs/001-test-feature/quickstart.md',
      };

      jest.spyOn(util, 'validateExecutionEnvironment').mockReturnValue(true);
      jest.spyOn(util, 'getFeaturePaths').mockReturnValue(mockPaths as any);
      jest.spyOn(util, 'checkFeatureBranch').mockReturnValue({ isValid: true });
      jest.spyOn(util, 'resolvePath').mockImplementation((p: string) => `/resolved/${p}`);
      jest.spyOn(util, 'checkFileExists').mockReturnValue(false);
      jest.spyOn(util, 'checkDirExistsWithFiles').mockReturnValue(false);

      // Act
      const result = await checkPrerequisites.execute({ json: false }, {});

      // Assert
      expect(result).toContain('FEATURE_DIR:');
      expect(result).toContain('AVAILABLE_DOCS:');
      expect(result).toContain('✗');
    });
  });

  describe('error scenarios', () => {
    it('should return error when execution environment validation fails', async () => {
      // Arrange
      jest.spyOn(util, 'validateExecutionEnvironment').mockReturnValue(false);

      // Act
      const result = await checkPrerequisites.execute({ json: true }, {});

      // Assert
      const parsed = JSON.parse(result);
      expect(parsed.valid).toBe(false);
      expect(parsed.error).toContain('Execution environment validation failed');
    });

    it('should return error when not on a valid feature branch', async () => {
      // Arrange
      const mockPaths = {
        CURRENT_BRANCH: 'main',
        HAS_GIT: 'true',
      };

      jest.spyOn(util, 'validateExecutionEnvironment').mockReturnValue(true);
      jest.spyOn(util, 'getFeaturePaths').mockReturnValue(mockPaths as any);
      jest.spyOn(util, 'checkFeatureBranch').mockReturnValue({
        isValid: false,
        error: 'Not on a feature branch',
      });

      // Act
      const result = await checkPrerequisites.execute({ json: true }, {});

      // Assert
      const parsed = JSON.parse(result);
      expect(parsed.valid).toBe(false);
      expect(parsed.error).toContain('Not on a feature branch');
    });

    it('should return error when feature directory not found', async () => {
      // Arrange
      const mockPaths = {
        REPO_ROOT: '/repo/root',
        CURRENT_BRANCH: '001-test-feature',
        HAS_GIT: 'true',
        FEATURE_DIR: 'specs/001-test-feature',
        FEATURE_SPEC: 'specs/001-test-feature/spec.md',
        IMPL_PLAN: 'specs/001-test-feature/plan.md',
        TASKS: 'specs/001-test-feature/tasks.md',
        RESEARCH: 'specs/001-test-feature/research.md',
        DATA_MODEL: 'specs/001-test-feature/data-model.md',
        DESIGN_FILE: 'specs/001-test-feature/design.md',
        CONTRACTS_DIR: 'specs/001-test-feature/contracts',
        QUICKSTART: 'specs/001-test-feature/quickstart.md',
      };

      jest.spyOn(util, 'validateExecutionEnvironment').mockReturnValue(true);
      jest.spyOn(util, 'getFeaturePaths').mockReturnValue(mockPaths as any);
      jest.spyOn(util, 'checkFeatureBranch').mockReturnValue({ isValid: true });
      jest.spyOn(util, 'resolvePath').mockImplementation((p: string) => `/resolved/${p}`);
      (existsSync as jest.Mock).mockReturnValue(false);

      // Act
      const result = await checkPrerequisites.execute({ json: true }, {});

      // Assert
      const parsed = JSON.parse(result);
      expect(parsed.valid).toBe(false);
      expect(parsed.error).toContain('Feature directory not found');
    });

    it('should return error when plan.md not found', async () => {
      // Arrange
      const mockPaths = {
        REPO_ROOT: '/repo/root',
        CURRENT_BRANCH: '001-test-feature',
        HAS_GIT: 'true',
        FEATURE_DIR: 'specs/001-test-feature',
        FEATURE_SPEC: 'specs/001-test-feature/spec.md',
        IMPL_PLAN: 'specs/001-test-feature/plan.md',
        TASKS: 'specs/001-test-feature/tasks.md',
        RESEARCH: 'specs/001-test-feature/research.md',
        DATA_MODEL: 'specs/001-test-feature/data-model.md',
        DESIGN_FILE: 'specs/001-test-feature/design.md',
        CONTRACTS_DIR: 'specs/001-test-feature/contracts',
        QUICKSTART: 'specs/001-test-feature/quickstart.md',
      };

      jest.spyOn(util, 'validateExecutionEnvironment').mockReturnValue(true);
      jest.spyOn(util, 'getFeaturePaths').mockReturnValue(mockPaths as any);
      jest.spyOn(util, 'checkFeatureBranch').mockReturnValue({ isValid: true });
      jest.spyOn(util, 'resolvePath').mockImplementation((p: string) => `/resolved/${p}`);

      // Mock existsSync to return true for feature dir but false for plan.md
      (existsSync as jest.Mock).mockImplementation((path: string) => {
        if (path.includes('001-test-feature')) return true;
        return false;
      });

      // Act
      const result = await checkPrerequisites.execute({ json: true }, {});

      // Assert
      const parsed = JSON.parse(result);
      expect(parsed.valid).toBe(false);
      expect(parsed.error).toContain('plan.md not found');
    });

    it('should return error when tasks.md required but not found', async () => {
      // Arrange
      const mockPaths = {
        REPO_ROOT: '/repo/root',
        CURRENT_BRANCH: '001-test-feature',
        HAS_GIT: 'true',
        FEATURE_DIR: 'specs/001-test-feature',
        FEATURE_SPEC: 'specs/001-test-feature/spec.md',
        IMPL_PLAN: 'specs/001-test-feature/plan.md',
        TASKS: 'specs/001-test-feature/tasks.md',
        RESEARCH: 'specs/001-test-feature/research.md',
        DATA_MODEL: 'specs/001-test-feature/data-model.md',
        DESIGN_FILE: 'specs/001-test-feature/design.md',
        CONTRACTS_DIR: 'specs/001-test-feature/contracts',
        QUICKSTART: 'specs/001-test-feature/quickstart.md',
      };

      jest.spyOn(util, 'validateExecutionEnvironment').mockReturnValue(true);
      jest.spyOn(util, 'getFeaturePaths').mockReturnValue(mockPaths as any);
      jest.spyOn(util, 'checkFeatureBranch').mockReturnValue({ isValid: true });
      jest.spyOn(util, 'resolvePath').mockImplementation((p: string) => `/resolved/${p}`);

      // Mock existsSync to return true for feature dir and plan.md but false for tasks.md
      (existsSync as jest.Mock).mockImplementation((path: string) => {
        if (path.includes('plan.md')) return true;
        if (path.includes('tasks.md')) return false;
        if (path.includes('001-test-feature') && !path.includes('.md')) return true;
        return false;
      });

      // Act
      const result = await checkPrerequisites.execute({ json: true, requireTasks: true }, {});

      // Assert
      const parsed = JSON.parse(result);
      expect(parsed.valid).toBe(false);
      expect(parsed.error).toContain('tasks.md not found');
    });
  });

  describe('paths-only mode', () => {
    it('should output only path variables when pathsOnly is true', async () => {
      // Arrange
      const mockPaths = {
        REPO_ROOT: '/repo/root',
        CURRENT_BRANCH: '001-test-feature',
        HAS_GIT: 'true',
        FEATURE_DIR: 'specs/001-test-feature',
        FEATURE_SPEC: 'specs/001-test-feature/spec.md',
        IMPL_PLAN: 'specs/001-test-feature/plan.md',
        TASKS: 'specs/001-test-feature/tasks.md',
        RESEARCH: 'specs/001-test-feature/research.md',
        DATA_MODEL: 'specs/001-test-feature/data-model.md',
        DESIGN_FILE: 'specs/001-test-feature/design.md',
        CONTRACTS_DIR: 'specs/001-test-feature/contracts',
        QUICKSTART: 'specs/001-test-feature/quickstart.md',
      };

      jest.spyOn(util, 'validateExecutionEnvironment').mockReturnValue(true);
      jest.spyOn(util, 'getFeaturePaths').mockReturnValue(mockPaths as any);
      jest.spyOn(util, 'checkFeatureBranch').mockReturnValue({ isValid: true });

      // Act
      const result = await checkPrerequisites.execute({ pathsOnly: true, json: true }, {});

      // Assert
      const parsed = JSON.parse(result);
      expect(parsed.REPO_ROOT).toBe('/repo/root');
      expect(parsed.BRANCH).toBe('001-test-feature');
      expect(parsed.FEATURE_DIR).toBe('specs/001-test-feature');
      expect(parsed.FEATURE_SPEC).toBe('specs/001-test-feature/spec.md');
      expect(parsed.IMPL_PLAN).toBe('specs/001-test-feature/plan.md');
      expect(parsed.TASKS).toBe('specs/001-test-feature/tasks.md');
    });
  });

  describe('parameter validation', () => {
    it('should handle json parameter correctly', async () => {
      // Arrange
      const mockPaths = {
        REPO_ROOT: '/repo/root',
        CURRENT_BRANCH: '001-test-feature',
        HAS_GIT: 'true',
        FEATURE_DIR: 'specs/001-test-feature',
        FEATURE_SPEC: 'specs/001-test-feature/spec.md',
        IMPL_PLAN: 'specs/001-test-feature/plan.md',
        TASKS: 'specs/001-test-feature/tasks.md',
        RESEARCH: 'specs/001-test-feature/research.md',
        DATA_MODEL: 'specs/001-test-feature/data-model.md',
        DESIGN_FILE: 'specs/001-test-feature/design.md',
        CONTRACTS_DIR: 'specs/001-test-feature/contracts',
        QUICKSTART: 'specs/001-test-feature/quickstart.md',
      };

      jest.spyOn(util, 'validateExecutionEnvironment').mockReturnValue(true);
      jest.spyOn(util, 'getFeaturePaths').mockReturnValue(mockPaths as any);
      jest.spyOn(util, 'checkFeatureBranch').mockReturnValue({ isValid: true });
      jest.spyOn(util, 'resolvePath').mockImplementation((p: string) => `/resolved/${p}`);
      jest.spyOn(util, 'checkFileExists').mockReturnValue(false);
      jest.spyOn(util, 'checkDirExistsWithFiles').mockReturnValue(false);

      // Act
      const jsonResult = await checkPrerequisites.execute({ json: true }, {});
      const textResult = await checkPrerequisites.execute({ json: false }, {});

      // Assert
      expect(() => JSON.parse(jsonResult)).not.toThrow();
      expect(() => JSON.parse(textResult)).toThrow();
    });

    it('should handle default parameter values', async () => {
      // Arrange
      const mockPaths = {
        REPO_ROOT: '/repo/root',
        CURRENT_BRANCH: '001-test-feature',
        HAS_GIT: 'true',
        FEATURE_DIR: 'specs/001-test-feature',
        FEATURE_SPEC: 'specs/001-test-feature/spec.md',
        IMPL_PLAN: 'specs/001-test-feature/plan.md',
        TASKS: 'specs/001-test-feature/tasks.md',
        RESEARCH: 'specs/001-test-feature/research.md',
        DATA_MODEL: 'specs/001-test-feature/data-model.md',
        DESIGN_FILE: 'specs/001-test-feature/design.md',
        CONTRACTS_DIR: 'specs/001-test-feature/contracts',
        QUICKSTART: 'specs/001-test-feature/quickstart.md',
      };

      jest.spyOn(util, 'validateExecutionEnvironment').mockReturnValue(true);
      jest.spyOn(util, 'getFeaturePaths').mockReturnValue(mockPaths as any);
      jest.spyOn(util, 'checkFeatureBranch').mockReturnValue({ isValid: true });
      jest.spyOn(util, 'resolvePath').mockImplementation((p: string) => `/resolved/${p}`);
      jest.spyOn(util, 'checkFileExists').mockReturnValue(false);
      jest.spyOn(util, 'checkDirExistsWithFiles').mockReturnValue(false);

      // Act - call with no parameters
      const result = await checkPrerequisites.execute({}, {});

      // Assert
      expect(result).toBeDefined();
      expect(typeof result).toBe('string');
    });
  });

  describe('edge cases', () => {
    it('should handle unexpected errors gracefully', async () => {
      // Arrange
      jest.spyOn(util, 'validateExecutionEnvironment').mockImplementation(() => {
        throw new Error('Unexpected error');
      });

      // Act
      const result = await checkPrerequisites.execute({ json: true }, {});

      // Assert
      const parsed = JSON.parse(result);
      expect(parsed.valid).toBe(false);
      expect(parsed.error).toContain('Unexpected error');
    });

    it('should handle empty AVAILABLE_DOCS array', async () => {
      // Arrange
      const mockPaths = {
        REPO_ROOT: '/repo/root',
        CURRENT_BRANCH: '001-test-feature',
        HAS_GIT: 'true',
        FEATURE_DIR: 'specs/001-test-feature',
        FEATURE_SPEC: 'specs/001-test-feature/spec.md',
        IMPL_PLAN: 'specs/001-test-feature/plan.md',
        TASKS: 'specs/001-test-feature/tasks.md',
        RESEARCH: 'specs/001-test-feature/research.md',
        DATA_MODEL: 'specs/001-test-feature/data-model.md',
        DESIGN_FILE: 'specs/001-test-feature/design.md',
        CONTRACTS_DIR: 'specs/001-test-feature/contracts',
        QUICKSTART: 'specs/001-test-feature/quickstart.md',
      };

      jest.spyOn(util, 'validateExecutionEnvironment').mockReturnValue(true);
      jest.spyOn(util, 'getFeaturePaths').mockReturnValue(mockPaths as any);
      jest.spyOn(util, 'checkFeatureBranch').mockReturnValue({ isValid: true });
      jest.spyOn(util, 'resolvePath').mockImplementation((p: string) => `/resolved/${p}`);
      jest.spyOn(util, 'checkFileExists').mockReturnValue(false);
      jest.spyOn(util, 'checkDirExistsWithFiles').mockReturnValue(false);

      // Act
      const result = await checkPrerequisites.execute({ json: true }, {});

      // Assert
      const parsed = JSON.parse(result);
      expect(parsed.AVAILABLE_DOCS).toEqual([]);
    });
  });
});
