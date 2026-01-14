/**
 * Roo Tools Library - Shared Utilities
 *
 * This module exports all shared utility functions for Roo Custom Tools.
 * These utilities provide git operations, path resolution, and feature management.
 *
 * @module lib
 */

// Export all utilities from util.ts
export {
  // Git utilities
  runGitCommand,
  hasGit,
  // Repository and branch functions
  getRepoRoot,
  getCurrentBranch,
  getFeatureDir,
  findFeatureDirByPrefix,
  // Feature paths
  getFeaturePaths,
  // Branch validation
  checkFeatureBranch,
  // File/directory checks
  checkFileExists,
  checkDirExists,
  checkDirExistsWithFiles,
  checkFile,
  checkDir,
  // Path resolution
  getWorkspacePath,
  validateExecutionEnvironment,
  normalizeTaskId,
  stripDuplicateWorkspacePrefix,
  resolvePath,
} from './util.js';

// Export all utilities from feature-utils.ts
export {
  // Git utilities
  runGitCommand as runGitCommandFeature,
  hasGit as hasGitFeature,
  // Repository functions
  findRepoRoot,
  getRepoRoot as getRepoRootFeature,
  // Spec directory functions
  getHighestFromSpecs,
  getHighestFromBranches,
  checkExistingBranches,
  // Branch name functions
  cleanBranchName,
  generateBranchName,
  truncateBranchName,
  createGitBranch,
} from './feature-utils.js';

// Re-export types
export type { BranchValidationResult, FeaturePaths } from './util.js';
