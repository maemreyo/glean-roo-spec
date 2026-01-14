/**
 * setup_roast_verify - Verify and locate the latest roast report for a feature
 *
 * Finds the latest roast report matching pattern: roast-report-FEATURE_NAME-*.md
 * If --report is specified, uses that exact report file instead of searching.
 *
 * Ported from: .zo/scripts/python/setup-roast-verify.py
 *
 * @example
 * ```typescript
 * // Auto-detect latest roast report
 * const result = await setup_roast_verify({ json: true })
 * // Returns: {"REPORT_FILE":"/path/to/roasts/roast-report-001-feature-2025-01-14-1200.md",...}
 *
 * // Use specific report file
 * const result = await setup_roast_verify({ json: true, report: "/path/to/report.md" })
 * // Returns: {"REPORT_FILE":"/path/to/report.md",...}
 *
 * // Use specific feature directory
 * const result = await setup_roast_verify({ json: true, featureDir: "specs/001-feature" })
 * ```
 *
 * @param json - Output results in JSON format (default: false)
 * @param report - Optional specific roast report file (absolute or relative path)
 * @param featureDir - Optional feature directory path (defaults to current branch)
 *
 * @returns JSON object or formatted text with roast report paths
 *
 * @throws {Error} If execution environment validation fails
 * @throws {Error} If roast report not found
 * @throws {Error} If specified report file doesn't exist
 *
 * @see {@link ../lib/util.ts} for path resolution utilities
 */

import { defineCustomTool } from '@roo-code/types';
import { parametersSchema as z } from '@roo-code/types';
import { existsSync, readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import {
  getFeaturePaths,
  getRepoRoot,
  resolvePath,
  validateExecutionEnvironment,
} from './lib/util.js';

export default defineCustomTool({
  name: 'setup_roast_verify',

  description: `
    Verify and locate the latest roast report for a feature.
    Finds the latest roast-report-FEATURE_NAME-*.md or uses specified report file.
    Outputs REPORT_FILE, TASKS, and BRANCH information.
  `,

  parameters: z.object({
    json: z
      .boolean()
      .optional()
      .describe('Output results in JSON format (compact)'),
    report: z
      .string()
      .optional()
      .describe('Specify a specific roast report file (absolute or relative path)'),
    featureDir: z
      .string()
      .optional()
      .describe('Optional feature directory path (defaults to current branch)'),
  }),

  async execute({ json = false, report, featureDir }, _context) {
    try {
      // Validate execution environment
      if (!validateExecutionEnvironment()) {
        const errorMsg = 'ERROR: Execution environment validation failed.';
        return json
          ? JSON.stringify({ error: errorMsg })
          : errorMsg;
      }

      // Get all feature paths
      const paths = getFeaturePaths();
      const repoRoot = getRepoRoot();
      const currentBranch = paths.CURRENT_BRANCH;

      // Determine feature directory and name
      let actualFeatureDir: string;
      let featureName: string;
      let tasks: string;

      if (featureDir) {
        const resolved = resolveFeatureDirectory(featureDir, repoRoot);
        actualFeatureDir = resolved.dir;
        featureName = resolved.name;
        tasks = join(actualFeatureDir, 'tasks.md');
      } else {
        featureName = currentBranch;
        actualFeatureDir = paths.FEATURE_DIR;
        tasks = paths.TASKS;
      }

      // Determine report file
      const roastsDir = join(actualFeatureDir, 'roasts');

      let reportFile: string;
      if (report) {
        // Use specified report file
        reportFile = resolveReportPath(report, repoRoot);
      } else {
        // Find the latest roast report for the current branch/feature
        reportFile = findLatestRoastReport(roastsDir, featureName);
      }

      // Prepare result
      const result = {
        REPORT_FILE: reportFile,
        TASKS: tasks,
        BRANCH: currentBranch,
      };

      // Return in requested format
      if (json) {
        return JSON.stringify(result);
      }

      return [
        `REPORT_FILE: ${result.REPORT_FILE}`,
        `TASKS: ${result.TASKS}`,
        `BRANCH: ${result.BRANCH}`,
      ].join('\n');

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return json
        ? JSON.stringify({ error: errorMessage })
        : `ERROR: ${errorMessage}`;
    }
  },
});

/**
 * Resolve feature directory from argument
 */
function resolveFeatureDirectory(featureArg: string, repoRoot: string): { dir: string; name: string } {
  // Try as absolute path
  if (existsSync(featureArg)) {
    const resolved = resolve(featureArg);
    const name = resolved.split('/').pop() || featureArg;
    console.log(`Using specified feature directory: ${resolved}`);
    return { dir: resolved, name };
  }

  // Try relative to current directory
  const cwdRelative = resolvePath(featureArg);
  if (existsSync(cwdRelative)) {
    const name = cwdRelative.split('/').pop() || featureArg;
    console.log(`Using specified feature directory: ${cwdRelative}`);
    return { dir: cwdRelative, name };
  }

  // Try relative to repo root
  const repoRelative = join(repoRoot, featureArg);
  if (existsSync(repoRelative)) {
    const name = repoRelative.split('/').pop() || featureArg;
    console.log(`Using specified feature directory: ${repoRelative}`);
    return { dir: repoRelative, name };
  }

  throw new Error(`Directory '${featureArg}' not found.`);
}

/**
 * Find the latest roast report for a feature
 */
function findLatestRoastReport(roastsDir: string, featureName: string): string {
  if (!existsSync(roastsDir)) {
    throw new Error(`No roast report found for feature ${featureName} in ${roastsDir}`);
  }

  // Pattern: roast-report-FEATURE_NAME-*.md
  const pattern = `roast-report-${featureName}-`;

  // Find all matching files
  const matchingFiles: Array<{ path: string; mtime: number }> = [];

  try {
    const entries = readdirSync(roastsDir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isFile() && entry.name.startsWith(pattern) && entry.name.endsWith('.md')) {
        const fullPath = join(roastsDir, entry.name);
        const stats = require('node:fs').statSync(fullPath);
        matchingFiles.push({ path: fullPath, mtime: stats.mtimeMs });
      }
    }
  } catch (error) {
    throw new Error(`Error reading roasts directory: ${error}`);
  }

  if (matchingFiles.length === 0) {
    throw new Error(`No roast report found for feature ${featureName} in ${roastsDir}`);
  }

  // Sort by modification time (most recent first) and return the latest
  matchingFiles.sort((a, b) => b.mtime - a.mtime);
  return matchingFiles[0]!.path;
}

/**
 * Resolve report path from --report argument
 */
function resolveReportPath(reportArg: string, repoRoot: string): string {
  // Try as absolute path
  if (existsSync(reportArg)) {
    return resolve(reportArg);
  }

  // Try as relative path from current directory
  const cwdRelative = resolvePath(reportArg);
  if (existsSync(cwdRelative)) {
    return cwdRelative;
  }

  // Try as relative path from repo root
  const repoRelative = join(repoRoot, reportArg);
  if (existsSync(repoRelative)) {
    return repoRelative;
  }

  throw new Error(`Specified report file not found: ${reportArg}`);
}
