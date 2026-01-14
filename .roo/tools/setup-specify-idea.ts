/**
 * setup_specify_idea - Find brainstorm file and spec template for spec creation
 *
 * Locates the appropriate brainstorm file and outputs paths needed for
 * creating a spec from an idea. Searches multiple locations for brainstorm files
 * in priority order: user-provided path, .zo/brainstorms/, FEATURE_DIR/brainstorms/, docs/brainstorms/
 *
 * Ported from: .zo/scripts/python/setup-specify-idea.py
 *
 * @example
 * ```typescript
 * const result = await setup_specify_idea({ json: true })
 * // Returns: {"BRAINSTORM_FILE": "/path/to/brainstorms/idea-2025-01-14.md", "SPEC_TEMPLATE": "/path/to/templates/spec-from-idea.md"}
 * ```
 *
 * @param json - Output results in JSON format (default: false)
 * @param brainstormFile - Optional path to brainstorm file (absolute or relative)
 *
 * @returns JSON object or formatted text with brainstorm file and template paths
 *
 * @throws {Error} If execution environment validation fails
 * @throws {Error} If no brainstorm file is found
 * @throws {Error} If user-provided path doesn't exist
 *
 * @see {@link ../lib/util.ts} for path resolution utilities
 */

import { defineCustomTool } from '@roo-code/types';
import { parametersSchema as z } from '@roo-code/types';
import { existsSync, readdirSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { cwd } from 'node:process';
import {
  getFeatureDir,
  getRepoRoot,
  validateExecutionEnvironment,
} from './lib/util.js';

export default defineCustomTool({
  name: 'setup_specify_idea',

  description: `
    Find brainstorm file and spec template for creating a spec from an idea.
    Searches for brainstorm files in .zo/brainstorms/, FEATURE_DIR/brainstorms/, or docs/brainstorms/.
    Returns paths needed for spec creation workflow.
  `,

  parameters: z.object({
    json: z
      .boolean()
      .optional()
      .describe('Output results in JSON format (compact)'),
    brainstormFile: z
      .string()
      .optional()
      .describe('Optional path to brainstorm file (absolute or relative)'),
  }),

  async execute({ json = false, brainstormFile }, _context) {
    try {
      // Validate execution environment
      if (!validateExecutionEnvironment()) {
        const errorMsg = 'ERROR: Execution environment validation failed.';
        return json
          ? JSON.stringify({ error: errorMsg })
          : errorMsg;
      }

      // Get repository paths
      const repoRoot = getRepoRoot();
      const currentBranch = getCurrentBranch();
      const featureDir = getFeatureDir(repoRoot, currentBranch);

      // Find brainstorm file
      let actualBrainstormFile: string;
      try {
        actualBrainstormFile = findBrainstormFile(repoRoot, featureDir, brainstormFile);
      } catch (error) {
        const errorMsg = `Error: ${(error as Error).message}`;
        return json
          ? JSON.stringify({ error: errorMsg })
          : errorMsg;
      }

      // Define other paths
      const specTemplate = join(repoRoot, '.zo', 'templates', 'spec-from-idea.md');
      const designFile = join(featureDir, 'design.md');

      // Prepare result
      const result = {
        BRAINSTORM_FILE: actualBrainstormFile,
        SPEC_TEMPLATE: specTemplate,
        DESIGN_FILE: designFile,
      };

      // Return in requested format
      if (json) {
        return JSON.stringify(result);
      }

      // Formatted text output
      return [
        `BRAINSTORM_FILE: ${result.BRAINSTORM_FILE}`,
        `SPEC_TEMPLATE: ${result.SPEC_TEMPLATE}`,
        `DESIGN_FILE: ${result.DESIGN_FILE}`,
      ].join('\n');

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return json
        ? JSON.stringify({ error: errorMessage })
        : `Error: ${errorMessage}`;
    }
  },
});

/**
 * Get current branch (simplified version)
 */
function getCurrentBranch(): string {
  // Try to get from git
  try {
    const { execSync } = require('node:child_process');
    const result = execSync('git rev-parse --abbrev-ref HEAD', {
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'ignore'],
    });
    return result.trim();
  } catch {
    // Fallback to feature directory name
    return cwd().split('/').pop() || 'main';
  }
}

/**
 * Find the brainstorm file from various possible locations
 *
 * Searches in the following order:
 * 1. User-provided path (if specified)
 * 2. .zo/brainstorms/ (primary location)
 * 3. FEATURE_DIR/brainstorms/ (legacy)
 * 4. docs/brainstorms/ (legacy)
 */
function findBrainstormFile(repoRoot: string, featureDir: string, userPath?: string): string {
  if (userPath) {
    // User provided a path - check if it exists
    const userPathObj = resolve(userPath);
    if (existsSync(userPathObj) && statSync(userPathObj).isFile()) {
      return userPathObj;
    }
    // Try relative to current directory
    const cwdRelative = resolve(cwd(), userPath);
    if (existsSync(cwdRelative) && statSync(cwdRelative).isFile()) {
      return cwdRelative;
    }
    throw new Error(`File '${userPath}' not found.`);
  }

  // Auto-detect latest brainstorm file

  // Primary Location: .zo/brainstorms
  const primaryDir = resolve(repoRoot, '.zo', 'brainstorms');
  if (existsSync(primaryDir)) {
    const latestFile = findLatestMdFile(primaryDir);
    if (latestFile) {
      return latestFile;
    }
  }

  // Legacy location 1: FEATURE_DIR/brainstorms
  const legacyDir1 = resolve(featureDir, 'brainstorms');
  if (existsSync(legacyDir1)) {
    const latestFile = findLatestMdFile(legacyDir1, 'brainstorm-');
    if (latestFile) {
      return latestFile;
    }
  }

  // Legacy location 2: docs/brainstorms
  const legacyDir2 = resolve(repoRoot, 'docs', 'brainstorms');
  if (existsSync(legacyDir2)) {
    const latestFile = findLatestMdFile(legacyDir2, 'brainstorm-');
    if (latestFile) {
      return latestFile;
    }
  }

  throw new Error(
    'No brainstorm file found. Run \'zo.brainstorm\' first.'
  );
}

/**
 * Find the latest .md file in a directory by modification time
 */
function findLatestMdFile(dir: string, prefix: string = ''): string | null {
  try {
    const entries = readdirSync(dir, { withFileTypes: true });
    const mdFiles: Array<{ path: string; mtime: number }> = [];

    for (const entry of entries) {
      if (entry.isFile() && entry.name.endsWith('.md')) {
        if (prefix && !entry.name.startsWith(prefix)) {
          continue;
        }
        const fullPath = resolve(dir, entry.name);
        const stats = statSync(fullPath);
        mdFiles.push({ path: fullPath, mtime: stats.mtimeMs });
      }
    }

    if (mdFiles.length === 0) {
      return null;
    }

    // Sort by modification time (most recent first)
    mdFiles.sort((a, b) => b.mtime - a.mtime);
    return mdFiles[0]!.path;
  } catch {
    return null;
  }
}
