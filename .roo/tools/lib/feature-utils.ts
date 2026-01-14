/**
 * Feature creation utility functions.
 *
 * This module provides shared utility functions for creating new features,
 * including branch number detection, branch name generation, and validation.
 *
 * Ported from: .zo/scripts/python/feature_utils.py
 */

import { execSync } from 'node:child_process';
import { existsSync, readdirSync } from 'node:fs';
import { cwd } from 'node:process';
import { resolve, sep } from 'node:path';

// ============================================================================
// Constants
// ============================================================================

const DEBUG = process.env.DEBUG || process.env.ZO_DEBUG;

/**
 * GitHub branch name limit (bytes).
 */
const MAX_BRANCH_LENGTH = 244;

/**
 * Stop words to filter out when generating branch names.
 */
const STOP_WORDS = /^(i|a|an|the|to|for|of|in|on|at|by|with|from|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|should|could|can|may|might|must|shall|this|that|these|those|my|your|our|their|want|need|add|get|set)$/i;

/**
 * Logger utility for debug/info/warning/error messages.
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
 * Run a git command and return output.
 *
 * @param args - List of git command arguments
 * @param cwd - Working directory for command (defaults to current dir)
 * @returns Command output as string, or null if command fails
 */
export function runGitCommand(args: readonly string[], workingDir?: string): string | null {
  // Validate and normalize cwd before passing to subprocess
  let effectiveCwd = workingDir;
  if (effectiveCwd !== undefined) {
    // Ensure cwd is an absolute path with proper format
    if (!effectiveCwd.startsWith(sep) && !effectiveCwd.startsWith('.')) {
      // If cwd looks like a relative path without './' prefix, skip it
      effectiveCwd = undefined;
    } else if (!existsSync(effectiveCwd)) {
      // If cwd doesn't exist, skip it
      effectiveCwd = undefined;
    }
  }

  try {
    const result = execSync(`git ${args.join(' ')}`, {
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'ignore'],
      timeout: 30000,
      cwd: effectiveCwd,
    });
    return result.trim();
  } catch {
    return null;
  }
}

/**
 * Check if git is available and this is a git repository.
 *
 * @param repoRoot - Repository root directory (optional, uses cwd if not provided)
 * @returns True if git is available, false otherwise
 */
export function hasGit(repoRoot?: string): boolean {
  return runGitCommand(['rev-parse', '--show-toplevel'], repoRoot) !== null;
}

// ============================================================================
// Repository Functions
// ============================================================================

/**
 * Find the repository root by searching for .git or .zo directories.
 *
 * Walks up the directory tree from the starting directory until it finds
 * a .git or .zo directory, or reaches the root.
 *
 * @param startDir - Directory to start searching from (defaults to current dir)
 * @returns Path to repository root, or null if not found
 */
export function findRepoRoot(startDir?: string): string | null {
  const effectiveStartDir = startDir ?? resolve(cwd());

  let current = resolve(effectiveStartDir);

  // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
  while (current && current !== resolve(current, '..')) {
    const gitDir = resolve(current, '.git');
    const zoDir = resolve(current, '.zo');

    if (existsSync(gitDir) || existsSync(zoDir)) {
      return current;
    }

    // Move up one directory
    const parent = resolve(current, '..');
    if (parent === current) {
      // Reached root
      break;
    }
    current = parent;
  }

  return null;
}

/**
 * Get repository root, with fallback for non-git repositories.
 *
 * @returns Path to repository root directory
 * @throws Error if repository root cannot be determined
 */
export function getRepoRoot(): string {
  // Find repo root by walking up from current working directory
  const repoRoot = findRepoRoot(cwd());

  if (repoRoot) {
    return repoRoot;
  }

  throw new Error('Could not determine repository root. Please run this script from within the repository.');
}

// ============================================================================
// Spec Directory Functions
// ============================================================================

/**
 * Get the highest number from spec directories.
 *
 * Scans the specs directory for directories matching the pattern ###-*,
 * extracts the numeric prefix, and returns the highest number found.
 *
 * @param specsDir - Path to specs directory
 * @returns Highest spec number found (0 if none)
 */
export function getHighestFromSpecs(specsDir: string): number {
  let highest = 0;

  if (!existsSync(specsDir)) {
    return highest;
  }

  try {
    const entries = readdirSync(specsDir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isDirectory()) {
        const dirname = entry.name;
        // Extract leading digits (force base-10 to avoid octal)
        const match = dirname.match(/^0*(\d+)/);
        if (match) {
          const number = Number.parseInt(match[1]!, 10);
          if (number > highest) {
            highest = number;
          }
        }
      }
    }
  } catch (error) {
    logger.warning(`Error reading specs directory: ${error}`);
  }

  return highest;
}

/**
 * Get the highest number from git branches.
 *
 * Lists all local and remote branches, extracts the numeric prefix
 * from branches matching ###-*, and returns the highest number.
 *
 * @returns Highest branch number found (0 if none)
 */
export function getHighestFromBranches(): number {
  let highest = 0;

  // Get all branches (local and remote)
  const branchesOutput = runGitCommand(['branch', '-a']);

  if (!branchesOutput) {
    return highest;
  }

  for (const line of branchesOutput.split('\n')) {
    // Clean branch name: remove leading markers and remote prefixes
    let cleanBranch = line.trim();
    cleanBranch = cleanBranch.replace(/^[\* ]+/, '');
    cleanBranch = cleanBranch.replace(/^remotes\/[^/]+\//, '');

    // Extract feature number if branch matches pattern ###-*
    if (/^\d{3}-/.test(cleanBranch)) {
      const match = cleanBranch.match(/^0*(\d+)/);
      if (match) {
        const number = Number.parseInt(match[1]!, 10); // Force decimal interpretation
        if (number > highest) {
          highest = number;
        }
      }
    }
  }

  return highest;
}

/**
 * Check existing branches and specs to return next available number.
 *
 * Fetches all remotes, then checks both git branches and spec directories
 * to find the highest numbered feature, and returns the next available number.
 *
 * @param specsDir - Path to specs directory (can be relative or absolute)
 * @returns Next available feature number
 */
export function checkExistingBranches(specsDir: string): number {
  // Fetch all remotes to get latest branch info (suppress errors)
  runGitCommand(['fetch', '--all', '--prune']);

  // Get highest number from all branches
  const highestBranch = getHighestFromBranches();

  // Get highest number from all specs (resolve to absolute path if relative)
  const specsPath = resolve(specsDir);
  const highestSpec = getHighestFromSpecs(specsPath);

  // Take the maximum of both
  const maxNum = Math.max(highestBranch, highestSpec);

  // Return next number
  return maxNum + 1;
}

// ============================================================================
// Branch Name Functions
// ============================================================================

/**
 * Clean and format a branch name.
 *
 * Converts to lowercase, replaces EACH non-alphanumeric character with a hyphen,
 * and trims leading/trailing hyphens.
 *
 * Matches bash behavior: sed 's/[^a-z0-9]/-/g' replaces each char with '-'
 *
 * @param name - Raw branch name
 * @returns Cleaned branch name
 */
export function cleanBranchName(name: string): string {
  // Convert to lowercase
  let cleaned = name.toLowerCase();

  // Replace EACH non-alphanumeric character with a hyphen (matches bash)
  cleaned = cleaned.split('').map((c) => (/[a-z0-9]/.test(c) ? c : '-')).join('');

  // Trim leading/trailing hyphens
  cleaned = cleaned.replace(/^-+|-+$/g, '');

  return cleaned;
}

/**
 * Generate a branch name from a description.
 *
 * Filters out stop words and short words (unless they're acronyms),
 * then uses the first 3-4 meaningful words to create the branch name.
 *
 * @param description - Feature description
 * @returns Generated branch name suffix
 */
export function generateBranchName(description: string): string {
  // Convert to lowercase and split into words
  let cleanName = description.toLowerCase();
  cleanName = cleanName.replace(/[^a-z0-9]+/g, ' ');
  const words = cleanName.split(' ').filter(Boolean);

  // Filter words: remove stop words and short words (unless acronyms)
  const meaningfulWords: string[] = [];

  for (const word of words) {
    // Check if word is a stop word
    if (STOP_WORDS.test(word)) {
      continue;
    }

    // Keep words >= 3 chars, or short words that appear as uppercase in original
    if (word.length >= 3) {
      meaningfulWords.push(word);
    } else {
      // Check if it appears as uppercase in original (likely acronym)
      const originalWords = description.split(/\s+/);
      for (const origWord of originalWords) {
        if (origWord.toLowerCase() === word && origWord.toUpperCase() === origWord && origWord.length <= 3) {
          meaningfulWords.push(word);
          break;
        }
      }
    }
  }

  // If we have meaningful words, use first 3-4 of them
  if (meaningfulWords.length > 0) {
    // Use 3 words, or 4 if exactly 4 available
    const maxWords = meaningfulWords.length === 4 ? 4 : 3;
    return meaningfulWords.slice(0, maxWords).join('-');
  }

  // Fallback: use cleaned description, take first 3 words
  const cleaned = cleanBranchName(description);
  const parts = cleaned.split('-').filter(Boolean);
  return parts.slice(0, 3).join('-');
}

/**
 * Truncate branch name if it exceeds GitHub's 244-byte limit.
 *
 * @param branchName - Full branch name
 * @returns Truncated branch name if needed, original otherwise
 */
export function truncateBranchName(branchName: string): string {
  // Check byte length (not character length)
  const byteLength = Buffer.byteLength(branchName, 'utf-8');

  if (byteLength <= MAX_BRANCH_LENGTH) {
    return branchName;
  }

  // Need to truncate
  // Account for: feature number (3) + hyphen (1) = 4 bytes/chars
  // But we need to be careful about UTF-8 multi-byte characters
  const parts = branchName.split('-');
  const prefix = parts[0] ? `${parts[0]}-` : '000-'; // e.g., "001-"
  const prefixBytes = Buffer.byteLength(prefix, 'utf-8');

  const maxSuffixBytes = MAX_BRANCH_LENGTH - prefixBytes;
  const suffix = parts.slice(1).join('-');

  // Truncate suffix byte by byte
  const suffixBytes = Buffer.byteLength(suffix, 'utf-8');
  let truncatedSuffix = suffix;

  if (suffixBytes > maxSuffixBytes) {
    // Simple character-based truncation (not perfect for UTF-8 but good enough)
    const maxChars = Math.floor(maxSuffixBytes); // Approximate
    truncatedSuffix = suffix.slice(0, maxChars);
  }

  // Remove trailing hyphen if truncation created one
  truncatedSuffix = truncatedSuffix.replace(/-+$/, '');

  const newBranchName = prefix + truncatedSuffix;

  // Log warning
  logger.warning(`Branch name exceeded GitHub's 244-byte limit`);
  logger.warning(`Original: ${branchName} (${byteLength} bytes)`);
  logger.warning(`Truncated to: ${newBranchName} (${Buffer.byteLength(newBranchName, 'utf-8')} bytes)`);

  return newBranchName;
}

/**
 * Create a new git branch.
 *
 * @param branchName - Name of branch to create
 * @param repoRoot - Repository root directory
 * @returns True if successful, false otherwise
 */
export function createGitBranch(branchName: string, repoRoot: string): boolean {
  if (!hasGit(repoRoot)) {
    logger.warning(`Git repository not detected; skipped branch creation for ${branchName}`);
    return false;
  }

  const result = runGitCommand(['checkout', '-b', branchName], repoRoot);
  return result !== null;
}
