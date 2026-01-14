/**
 * setup_roast - Initialize a roast report for code review
 *
 * Creates a new roast report file in the feature's roasts/ directory.
 * Uses the roast template if available, and appends metadata for commits
 * and design system if provided via JSON data.
 *
 * Ported from: .zo/scripts/python/setup-roast.py
 *
 * @example
 * ```typescript
 * const result = await setup_roast({ json: true })
 * // Returns: {"REPORT_FILE": "/path/to/roasts/roast-report-001-feature-2025-01-14-1200.md", "BRANCH": "001-feature"}
 * ```
 *
 * @param json - Output results in JSON format (default: false)
 * @param jsonData - JSON string with commits array and optional design_system
 *                   Example: '{"commits":["abc123","def456"],"design_system":"/path"}'
 * @param featureDir - Optional feature directory path (defaults to current branch)
 *
 * @returns JSON object or formatted text with created file paths
 *
 * @throws {Error} If execution environment validation fails
 * @throws {Error} If feature directory not found (when not on feature branch)
 * @throws {Error} If JSON data is invalid
 *
 * @see {@link ../lib/util.ts} for path resolution utilities
 */

import { defineCustomTool } from '@roo-code/types';
import { parametersSchema as z } from '@roo-code/types';
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import {
  checkFileExists,
  getFeaturePaths,
  getRepoRoot,
  resolvePath,
  validateExecutionEnvironment,
} from './lib/util.js';

interface RoastJsonData {
  commits?: string[];
  design_system?: string;
}

export default defineCustomTool({
  name: 'setup_roast',

  description: `
    Initialize a roast report for code review.
    Creates roast-report-<FEATURE>-<DATE>.md in the feature's roasts/ directory.
    Uses roast template if available, and appends commit metadata if provided.
  `,

  parameters: z.object({
    json: z
      .boolean()
      .optional()
      .describe('Output results in JSON format (compact)'),
    jsonData: z
      .string()
      .optional()
      .describe('JSON data with commits array and optional design_system path'),
    featureDir: z
      .string()
      .optional()
      .describe('Optional feature directory path (defaults to current branch)'),
  }),

  async execute({ json = false, jsonData, featureDir }, _context) {
    try {
      // Validate execution environment
      if (!validateExecutionEnvironment()) {
        const errorMsg = 'ERROR: Execution environment validation failed.';
        return json
          ? JSON.stringify({ error: errorMsg, created: false })
          : errorMsg;
      }

      // Parse JSON input if provided
      let parsedJsonData: RoastJsonData = {};
      if (jsonData) {
        try {
          parsedJsonData = JSON.parse(jsonData) as RoastJsonData;
        } catch (error) {
          const errorMsg = `ERROR: Invalid JSON input: ${error}`;
          return json
            ? JSON.stringify({ error: errorMsg, created: false })
            : errorMsg;
        }
      }

      // Get feature paths
      const paths = getFeaturePaths();
      const repoRoot = getRepoRoot();
      const currentBranch = paths.CURRENT_BRANCH;

      // Determine feature directory and name
      let actualFeatureDir: string;
      let featureName: string;
      let featureSpec: string;
      let implPlan: string;
      let tasks: string;

      if (featureDir) {
        // Resolve feature directory from argument
        actualFeatureDir = resolveFeatureDirectory(featureDir, repoRoot);
        featureName = actualFeatureDir.split('/').pop() || currentBranch;
        featureSpec = join(actualFeatureDir, 'spec.md');
        implPlan = join(actualFeatureDir, 'plan.md');
        tasks = join(actualFeatureDir, 'tasks.md');
      } else {
        // Use current branch
        featureName = currentBranch;

        // Special handling for main/master branch
        if (featureName === 'main' || featureName === 'master') {
          if (Object.keys(parsedJsonData).length > 0) {
            // Use .zo directory as FEATURE_DIR so roasts go to .zo/roasts/
            actualFeatureDir = join(repoRoot, '.zo');
            featureSpec = join(actualFeatureDir, 'spec.md');
            implPlan = join(actualFeatureDir, 'plan.md');
            tasks = join(actualFeatureDir, 'tasks.md');
          } else {
            const errorMsg = [
              'ERROR: Not on a feature branch.',
              'Please specify a feature directory or switch to a feature branch.',
              `Usage: setup_roast <feature-directory>`,
            ].join('\n');
            return json
              ? JSON.stringify({ error: errorMsg, created: false })
              : errorMsg;
          }
        } else {
          actualFeatureDir = paths.FEATURE_DIR;
          featureSpec = paths.FEATURE_SPEC;
          implPlan = paths.IMPL_PLAN;
          tasks = paths.TASKS;
        }
      }

      // Ensure the roast directory exists inside the feature spec folder
      const roastsDir = join(actualFeatureDir, 'roasts');
      if (!existsSync(roastsDir)) {
        mkdirSync(roastsDir, { recursive: true });
      }

      // Define report path with timestamp
      const dateStr = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0] +
        '-' + new Date().toTimeString().slice(0, 5).replace(':', '');
      const reportFile = join(roastsDir, `roast-report-${featureName}-${dateStr}.md`);

      // Parse commits and design system from JSON
      const commits = parsedJsonData.commits || [];
      const commitsStr = commits.join(',');
      let designSystem = parsedJsonData.design_system || '';

      // Default design system if not provided
      if (!designSystem) {
        designSystem = join(repoRoot, '.zo', 'design-system.md');
      }

      // Create roast report
      createRoastReport(reportFile, join(repoRoot, '.zo', 'templates', 'roast-template.md'), parsedJsonData);

      // Prepare result
      const result = {
        REPORT_FILE: reportFile,
        TASKS: tasks,
        IMPL_PLAN: implPlan,
        BRANCH: currentBranch,
        COMMITS: commitsStr,
        DESIGN_SYSTEM: designSystem,
        created: true,
      };

      // Return in requested format
      if (json) {
        return JSON.stringify(result);
      }

      // Formatted text output
      const lines = [
        `REPORT_FILE: ${result.REPORT_FILE}`,
        `TASKS: ${result.TASKS}`,
        `IMPL_PLAN: ${result.IMPL_PLAN}`,
        `BRANCH: ${result.BRANCH}`,
      ];

      if (result.COMMITS) {
        lines.push(`COMMITS: ${result.COMMITS}`);
      }
      if (result.DESIGN_SYSTEM) {
        lines.push(`DESIGN_SYSTEM: ${result.DESIGN_SYSTEM}`);
      }

      return lines.join('\n');

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return json
        ? JSON.stringify({ error: errorMessage, created: false })
        : `ERROR: ${errorMessage}`;
    }
  },
});

/**
 * Resolve feature directory from argument
 */
function resolveFeatureDirectory(featureArg: string, repoRoot: string): string {
  // Try as absolute path
  if (existsSync(featureArg) && checkFileExists(featureArg)) {
    return featureArg;
  }

  // Try relative to current directory
  const cwdRelative = resolvePath(featureArg);
  if (existsSync(cwdRelative)) {
    return cwdRelative;
  }

  // Try relative to repo root
  const repoRelative = join(repoRoot, featureArg);
  if (existsSync(repoRelative)) {
    return repoRelative;
  }

  throw new Error(`Directory '${featureArg}' not found.`);
}

/**
 * Create roast report from template, optionally appending metadata
 */
function createRoastReport(reportFile: string, templatePath: string, jsonData: RoastJsonData): void {
  if (checkFileExists(templatePath)) {
    copyFileSync(templatePath, reportFile);
  } else {
    // Create empty file if template not found
    writeFileSync(reportFile, '', 'utf-8');
  }

  // Append metadata if JSON input provided
  const commits = jsonData.commits || [];
  const designSystem = jsonData.design_system || '';

  if (commits.length > 0 || designSystem) {
    const metadata: string[] = ['\n\n<!--'];
    if (commits.length > 0) {
      metadata.push(`Commits: ${commits.join(',')}`);
    }
    if (designSystem) {
      metadata.push(`Design System: ${designSystem}`);
    }
    metadata.push('-->');

    // Append to file
    const content = readFileSync(reportFile, 'utf-8');
    writeFileSync(reportFile, content + metadata.join('\n'), 'utf-8');
  }
}
