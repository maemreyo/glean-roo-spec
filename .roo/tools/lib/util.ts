/**
 * Common utility functions for Roo Tools.
 *
 * This module provides shared utility functions migrated from Python's common.py.
 * It provides git utilities, path utilities, validation utilities, and feature path resolution.
 *
 * Ported from: .zo/scripts/python/common.py
 */

import { execSync } from 'node:child_process';
import { existsSync, readdirSync, statSync } from 'node:fs';
import { cwd, env } from 'node:process';
import { join, normalize, resolve, sep } from 'node:path';

// ============================================================================
// Types
// ============================================================================

/**
 * Result of a feature branch validation check.
 */
export interface BranchValidationResult {
  readonly isValid: boolean;
  readonly error?: string;
}

/**
 * All feature-related paths.
 */
export interface FeaturePaths {
  readonly REPO_ROOT: string;
  readonly CURRENT_BRANCH: string;
  readonly HAS_GIT: boolean;
  readonly FEATURE_DIR: string;
  readonly FEATURE_SPEC: string;
  readonly IMPL_PLAN: string;
  readonly TASKS: string;
  readonly RESEARCH: string;
  readonly DATA_MODEL: string;
  readonly QUICKSTART: string;
  readonly CONTRACTS_DIR: string;
  readonly DESIGN_FILE: string;
  readonly GLOBAL_DESIGN_SYSTEM: string;
}

// ============================================================================
// Constants
// ============================================================================

const DEBUG = env.DEBUG || env.ZO_DEBUG;

/**
 * Logger utility for debug/info/error messages.
 */
const logger = {
  debug: (...args: unknown[]) => {
    if (DEBUG) {
      console.debug('[DEBUG]', ...args);
    }
  },
  info: (...args: unknown[]) => {
    console.info('[INFO]', ...args);
  },
  warning: (...args: unknown[]) => {
    console.warn('[WARN]', ...args);
  },
  error: (...args: unknown[]) => {
    console.error('[ERROR]', ...args);
  },
};

// ============================================================================
// Git Utility Functions
// ============================================================================

/**
 * Run a git command and return output, or null if git not available.
 *
 * @param args - Array of git command arguments (e.g., ['status'])
 * @returns Command output as string, or null if command fails
 */
export function runGitCommand(args: readonly string[]): string | null {
  try {
    const result = execSync(`git ${args.join(' ')}`, {
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'ignore'],
      timeout: 5000,
    });
    return result.trim();
  } catch {
    return null;
  }
}

/**
 * Check if git is available and this is a git repository.
 *
 * @returns True if git is available, false otherwise
 */
export function hasGit(): boolean {
  return runGitCommand(['rev-parse', '--show-toplevel']) !== null;
}

// ============================================================================
// Repository and Branch Functions
// ============================================================================

/**
 * Get repository root, with fallback for non-git repositories.
 *
 * @returns Path to repository root directory
 */
export function getRepoRoot(): string {
  // Try git first
  const gitRoot = runGitCommand(['rev-parse', '--show-toplevel']);
  if (gitRoot) {
    return gitRoot;
  }

  // Fall back to current working directory for non-git repos
  logger.debug('No git root found, using current directory');
  return cwd();
}

/**
 * Get current branch, with fallback for non-git repositories.
 *
 * @returns Current branch name or feature directory name
 */
export function getCurrentBranch(): string {
  // First check if SPECIFY_FEATURE environment variable is set
  const specifyFeature = env.SPECIFY_FEATURE ?? '';
  if (specifyFeature) {
    logger.debug(`Using SPECIFY_FEATURE env var: ${specifyFeature}`);
    return specifyFeature;
  }

  // Then check git if available
  const gitBranch = runGitCommand(['rev-parse', '--abbrev-ref', 'HEAD']);
  if (gitBranch) {
    logger.debug(`Using git branch: ${gitBranch}`);
    return gitBranch;
  }

  // For non-git repos, try to find the latest feature directory
  const repoRoot = getRepoRoot();
  const specsDir = resolve(repoRoot, 'specs');

  if (!existsSync(specsDir)) {
    logger.debug("No specs directory found, using 'main' as fallback");
    return 'main';
  }

  let latestFeature: string | null = null;
  let highest = 0;

  try {
    const entries = readdirSync(specsDir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isDirectory()) {
        const match = entry.name.match(/^(\d{3})-(.+)$/);
        if (match) {
          const number = Number.parseInt(match[1]!, 10);
          if (number > highest) {
            highest = number;
            latestFeature = entry.name;
          }
        }
      }
    }
  } catch (error) {
    logger.warning(`Error reading specs directory: ${error}`);
  }

  if (latestFeature) {
    logger.debug(`Found latest feature directory: ${latestFeature}`);
    return latestFeature;
  }

  logger.debug("No feature directories found, using 'main' as fallback");
  return 'main';
}

/**
 * Get the feature directory path for a given branch.
 *
 * @param repoRoot - Repository root path
 * @param branchName - Current branch name
 * @returns Path to feature directory
 */
export function getFeatureDir(repoRoot: string, branchName: string): string {
  return findFeatureDirByPrefix(repoRoot, branchName);
}

/**
 * Find feature directory by numeric prefix instead of exact branch match.
 * This allows multiple branches to work on the same spec.
 *
 * @param repoRoot - Repository root path
 * @param branchName - Current branch name
 * @returns Path to feature directory
 */
export function findFeatureDirByPrefix(repoRoot: string, branchName: string): string {
  const specsDir = resolve(repoRoot, 'specs');

  // Extract numeric prefix from branch (e.g., "004" from "004-whatever")
  const match = branchName.match(/^(\d{3})-(.+)$/);
  if (!match) {
    // If branch doesn't have numeric prefix, fall back to exact match
    logger.debug(`Branch '${branchName}' doesn't match prefix pattern, using exact match`);
    return resolve(specsDir, branchName);
  }

  const prefix = match[1]!;

  // Search for directories in specs/ that start with this prefix
  const matches: string[] = [];
  if (existsSync(specsDir)) {
    try {
      const entries = readdirSync(specsDir, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isDirectory() && entry.name.startsWith(`${prefix}-`)) {
          matches.push(entry.name);
        }
      }
    } catch (error) {
      logger.warning(`Error searching specs directory: ${error}`);
    }
  }

  // Handle results
  if (matches.length === 0) {
    // No match found - return the branch name path (will fail later with clear error)
    logger.debug(`No matching directories found for prefix '${prefix}'`);
    return resolve(specsDir, branchName);
  }

  if (matches.length === 1) {
    // Exactly one match - perfect!
    logger.debug(`Found single matching directory: ${matches[0]}`);
    return resolve(specsDir, matches[0]!);
  }

  // Multiple matches - this shouldn't happen with proper naming convention
  logger.error(
    `Multiple spec directories found with prefix '${prefix}': ${matches.join(', ')}\n` +
      `Please ensure only one spec directory exists per numeric prefix.`,
  );
  return resolve(specsDir, branchName);
}

// ============================================================================
// Feature Paths Functions
// ============================================================================

/**
 * Get all feature-related paths as an object.
 *
 * @returns Object containing all path variables
 */
export function getFeaturePaths(): FeaturePaths {
  const workspace = getWorkspacePath();
  const repoRoot = getRepoRoot();
  const currentBranch = getCurrentBranch();
  const hasGitRepo = hasGit();

  // Use prefix-based lookup to support multiple branches per spec
  const featureDir = findFeatureDirByPrefix(repoRoot, currentBranch);

  // Resolve duplicate workspace prefix for featureDir
  const resolvedFeatureDir = stripDuplicateWorkspacePrefix(featureDir, workspace);

  // Helper to resolve and normalize paths
  const resolvePathVar = (path: string): string => {
    const resolved = stripDuplicateWorkspacePrefix(path, workspace);
    return resolve(resolved);
  };

  return {
    REPO_ROOT: resolvePathVar(repoRoot),
    CURRENT_BRANCH: currentBranch,
    HAS_GIT: hasGitRepo,
    FEATURE_DIR: resolvePathVar(resolvedFeatureDir),
    FEATURE_SPEC: resolvePathVar(join(resolvedFeatureDir, 'spec.md')),
    IMPL_PLAN: resolvePathVar(join(resolvedFeatureDir, 'plan.md')),
    TASKS: resolvePathVar(join(resolvedFeatureDir, 'tasks.md')),
    RESEARCH: resolvePathVar(join(resolvedFeatureDir, 'research.md')),
    DATA_MODEL: resolvePathVar(join(resolvedFeatureDir, 'data-model.md')),
    QUICKSTART: resolvePathVar(join(resolvedFeatureDir, 'quickstart.md')),
    CONTRACTS_DIR: resolvePathVar(join(resolvedFeatureDir, 'contracts')),
    DESIGN_FILE: resolvePathVar(join(resolvedFeatureDir, 'design.md')),
    GLOBAL_DESIGN_SYSTEM: resolvePathVar(join(repoRoot, '.zo', 'design-system.md')),
  };
}

// ============================================================================
// Feature Branch Validation Functions
// ============================================================================

/**
 * Check if the current branch is a valid feature branch.
 *
 * @param branch - Current branch name
 * @param hasGitRepo - Whether git repository is available
 * @returns Tuple of [is_valid, error_message]
 */
export function checkFeatureBranch(branch: string, hasGitRepo: boolean): BranchValidationResult {
  // For non-git repos, we can't enforce branch naming but still provide output
  if (!hasGitRepo) {
    return { isValid: true };
  }

  // Check if branch matches feature branch pattern (e.g., 001-feature-name)
  if (!/^\d{3}-/.test(branch)) {
    return {
      isValid: false,
      error: `Not on a feature branch. Current branch: ${branch}\nFeature branches should be named like: 001-feature-name`,
    };
  }

  return { isValid: true };
}

// ============================================================================
// File and Directory Check Functions
// ============================================================================

/**
 * Check if a file exists.
 *
 * @param filePath - Path to file
 * @returns True if file exists, false otherwise
 */
export function checkFileExists(filePath: string): boolean {
  try {
    const stats = statSync(filePath);
    return stats.isFile();
  } catch {
    return false;
  }
}

/**
 * Check if a directory exists.
 *
 * @param dirPath - Path to directory
 * @returns True if directory exists, false otherwise
 */
export function checkDirExists(dirPath: string): boolean {
  try {
    const stats = statSync(dirPath);
    return stats.isDirectory();
  } catch {
    return false;
  }
}

/**
 * Check if a directory exists and contains files.
 *
 * @param dirPath - Path to directory
 * @returns True if directory exists and has files, false otherwise
 */
export function checkDirExistsWithFiles(dirPath: string): boolean {
  if (!checkDirExists(dirPath)) {
    return false;
  }
  try {
    const entries = readdirSync(dirPath, { withFileTypes: true });
    return entries.length > 0;
  } catch {
    return false;
  }
}

/**
 * Check if file exists and return formatted status string.
 *
 * @param filePath - Path to file
 * @param displayName - Name to display
 * @returns Formatted status string with checkmark or cross
 */
export function checkFile(filePath: string, displayName: string): string {
  return checkFileExists(filePath) ? `  ✓ ${displayName}` : `  ✗ ${displayName}`;
}

/**
 * Check if directory exists with files and return formatted status string.
 *
 * @param dirPath - Path to directory
 * @param displayName - Name to display
 * @returns Formatted status string with checkmark or cross
 */
export function checkDir(dirPath: string, displayName: string): string {
  return checkDirExistsWithFiles(dirPath) ? `  ✓ ${displayName}` : `  ✗ ${displayName}`;
}

// ============================================================================
// Path Resolution Functions (for AI CWD resilience)
// ============================================================================

/**
 * Get the workspace root path from environment or current directory.
 *
 * This function handles the case where AIs may change the current working
 * directory (CWD) to incorrect locations.
 *
 * @returns Workspace root path as absolute string
 */
export function getWorkspacePath(): string {
  const pwd = env.PWD ?? '';
  const workspace = env.WORKSPACE ?? env.HOME ?? '';
  const currentCwd = cwd();

  logger.debug('Environment check:');
  logger.debug(`  PWD env: ${pwd}`);
  logger.debug(`  CWD: ${currentCwd}`);

  // Detect duplicate path segments (e.g., /Users/Users/ or /home/home/)
  const usersCount = (currentCwd.match(/\/Users\//g) ?? []).length;
  if (usersCount > 1) {
    logger.warning(`CWD contains duplicate '/Users/' (${usersCount} times): ${currentCwd}`);
  }

  const homeCount = (currentCwd.match(/\/home\//g) ?? []).length;
  if (homeCount > 1) {
    logger.warning(`CWD contains duplicate '/home/' (${homeCount} times): ${currentCwd}`);
  }

  if (pwd && existsSync(pwd)) {
    logger.debug(`Using PWD: ${pwd}`);
    return resolve(pwd);
  }

  logger.debug(`Using CWD: ${currentCwd}`);
  return resolve(currentCwd);
}

/**
 * Validate that we're running in the correct environment.
 *
 * @returns True if environment is valid, false otherwise
 */
export function validateExecutionEnvironment(): boolean {
  const workspace = getWorkspacePath();

  // Check for obvious path duplication patterns
  const segments = workspace.split(sep).filter(Boolean);

  const segmentCounts = new Map<string, number>();
  for (const segment of segments) {
    segmentCounts.set(segment, (segmentCounts.get(segment) ?? 0) + 1);
  }

  const duplicates = Array.from(segmentCounts.entries())
    .filter(([, count]) => count > 1)
    .map(([segment]) => segment);

  if (duplicates.length > 0) {
    logger.error(`Detected duplicate path segments: ${duplicates.join(', ')}`);
    logger.error(`   Workspace: ${workspace}`);
    return false;
  }

  // Check if workspace exists
  if (!existsSync(workspace)) {
    logger.error(`Workspace path does not exist: ${workspace}`);
    return false;
  }

  logger.debug(`Execution environment validated: ${workspace}`);
  return true;
}

/**
 * Normalize task ID to standard format TXXX.
 *
 * Handles common variations:
 * - [T001] -> T001
 * - task_T001 -> T001
 * - T001 -> T001
 *
 * @param taskId - Raw task ID input
 * @returns Normalized task ID in format T001
 */
export function normalizeTaskId(taskId: string): string {
  const original = taskId;

  // Remove brackets if present: [T001] -> T001
  let normalized = taskId.trim();
  if (normalized.startsWith('[') && normalized.endsWith(']')) {
    normalized = normalized.slice(1, -1);
  }

  // Remove 'task_' prefix if present: task_T001 -> T001
  if (normalized.toLowerCase().startsWith('task_')) {
    normalized = normalized.slice(5);
  }

  // Ensure uppercase T prefix
  if (!normalized.startsWith('T') && /^\d{3}$/.test(normalized)) {
    normalized = `T${normalized}`;
  }

  if (original !== normalized) {
    logger.debug(`Normalized task ID: '${original}' -> '${normalized}'`);
  }

  return normalized;
}

/**
 * Strip duplicate workspace prefix from path.
 *
 * Handles cases like:
 * /Users/xxx/Documents/zaob-dev/glean-v2/Users/xxx/Documents/zaob-dev/glean-v2/specs/...
 *
 * @param path - The input file path
 * @param workspace - The workspace root path
 * @returns Path with duplicate prefix stripped if detected
 */
export function stripDuplicateWorkspacePrefix(path: string, workspace: string): string {
  // Check for doubled workspace path (e.g., /path/to/workspace/path/to/workspace/...)
  const doubledPattern = workspace + workspace;
  if (path.startsWith(doubledPattern)) {
    const corrected = path.slice(workspace.length);
    logger.warning(
      `Detected doubled workspace path, corrected: ${path.slice(0, 50)}... -> ${corrected.slice(0, 50)}...`,
    );
    return corrected;
  }

  // Check if path starts with workspace + '/Users/xxx/...' pattern
  if (path.startsWith(workspace)) {
    const afterWorkspace = path.slice(workspace.length).replace(/^\//, '');

    if (afterWorkspace.startsWith('Users/') || afterWorkspace.startsWith('User/')) {
      const secondOccurrence = path.indexOf(afterWorkspace);
      if (secondOccurrence > workspace.length) {
        const corrected = '/' + afterWorkspace;
        logger.warning(
          `Detected duplicate workspace segment, corrected: ${path.slice(0, 50)}... -> ${corrected}`,
        );
        return corrected;
      }
    }
  }

  return path;
}

/**
 * Resolve task file path, handling common AI mistakes.
 *
 * This function handles:
 * 1. Double workspace path (AI mistakenly prepends workspace twice)
 * 2. Non-existent paths from wrong CWD (tries common locations)
 * 3. Relative paths from different directories
 *
 * @param taskFile - The input file path (possibly incorrect)
 * @returns Resolved absolute path to the file, or original if not found
 */
export function resolvePath(taskFile: string): string {
  const workspace = getWorkspacePath();
  const originalPath = taskFile;

  // Case A: Strip duplicate workspace prefix
  let resolvedPath = stripDuplicateWorkspacePrefix(taskFile, workspace);

  // Case B: Try multiple locations if file doesn't exist
  if (!existsSync(resolvedPath)) {
    const possiblePaths: string[] = [];

    // Original path (just in case)
    possiblePaths.push(resolvedPath);

    // Try relative to workspace
    possiblePaths.push(resolve(workspace, resolvedPath));

    // Try with 'specs/' prefix if not already present
    const basename = resolvedPath.split(sep).pop() ?? '';
    possiblePaths.push(resolve(workspace, 'specs', basename));

    // Try with 'specs/' prefix for full path
    if (!resolvedPath.startsWith('specs' + sep) && !resolvedPath.startsWith('specs/')) {
      possiblePaths.push(resolve(workspace, 'specs', resolvedPath));
    }

    // Try parent directories (for when AI assumes wrong CWD)
    const parts = resolvedPath.split(sep);
    if (parts.length > 1) {
      possiblePaths.push(resolve(workspace, parts[parts.length - 1]!));
    }

    // Try current working directory
    const currentCwd = cwd();
    if (currentCwd !== workspace) {
      possiblePaths.push(resolve(currentCwd, resolvedPath));
      possiblePaths.push(resolve(currentCwd, 'specs', basename));
    }

    // Find the first existing path
    for (const path of possiblePaths) {
      if (existsSync(path)) {
        const absPath = resolve(path);
        if (absPath !== originalPath) {
          logger.warning(`Path not found at '${originalPath}', resolved to: ${absPath}`);
        }
        return absPath;
      }
    }

    // If file exists after normalization, use it
    if (existsSync(resolvedPath)) {
      return resolve(resolvedPath);
    }
  }

  // Return absolute path if file exists
  if (existsSync(resolvedPath)) {
    return resolve(resolvedPath);
  }

  // Return original if nothing works (will fail at file check later)
  logger.warning(`Could not resolve path, using original: ${resolvedPath}`);
  return resolvedPath;
}
