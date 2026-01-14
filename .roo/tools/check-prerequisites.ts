/**
 * check_prerequisites - Validate feature prerequisites and available documentation
 *
 * Checks if the current feature has required documentation files and directories.
 * Returns available optional docs (research.md, data-model.md, design.md, contracts/, quickstart.md).
 * Validates prerequisites for Spec-Driven Development workflow operations.
 *
 * Ported from: .zo/scripts/python/check-prerequisites.py
 *
 * @example
 * ```typescript
 * const result = await check_prerequisites({ json: true })
 * // Returns: {"FEATURE_DIR": "/path/to/specs/001-feature", "AVAILABLE_DOCS": ["research.md"]}
 * ```
 *
 * @param json - Output in JSON format (default: false)
 * @param requireTasks - Require tasks.md to exist (for implementation phase, default: false)
 * @param includeTasks - Include tasks.md in AVAILABLE_DOCS list (default: false)
 * @param pathsOnly - Only output path variables, no validation (default: false)
 *
 * @returns JSON object or formatted text with feature paths and available docs
 *
 * @throws {Error} If execution environment validation fails
 * @throws {Error} If not on a valid feature branch
 * @throws {Error} If feature directory not found
 * @throws {Error} If plan.md not found
 * @throws {Error} If tasks.md required but not found
 *
 * @see {@link ../lib/util.ts} for path resolution utilities
 */

import { defineCustomTool } from '@roo-code/types';
import { parametersSchema as z } from '@roo-code/types';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import {
  checkDirExistsWithFiles,
  checkFeatureBranch,
  checkFileExists,
  getFeaturePaths,
  getRepoRoot,
  resolvePath,
  validateExecutionEnvironment,
} from './lib/util.js';

export default defineCustomTool({
  name: 'check_prerequisites',

  description: `
    Check if the current feature branch has required documentation files.
    Returns available optional docs (research.md, data-model.md, design.md, contracts/, quickstart.md).
    Validates prerequisites for Spec-Driven Development workflow operations.
  `,

  parameters: z.object({
    json: z
      .boolean()
      .optional()
      .describe('Output results in JSON format (compact, no indentation)'),
    requireTasks: z
      .boolean()
      .optional()
      .describe('Require tasks.md to exist (for implementation phase)'),
    includeTasks: z
      .boolean()
      .optional()
      .describe('Include tasks.md in AVAILABLE_DOCS list'),
    pathsOnly: z
      .boolean()
      .optional()
      .describe('Only output path variables without validation'),
  }),

  async execute({ json = false, requireTasks = false, includeTasks = false, pathsOnly = false }, _context) {
    try {
      // Validate execution environment first
      if (!validateExecutionEnvironment()) {
        const errorMsg = 'ERROR: Execution environment validation failed.';
        return json
          ? JSON.stringify({ error: errorMsg, valid: false })
          : errorMsg;
      }

      // Get feature paths and validate branch
      const paths = getFeaturePaths();

      // Check if on valid feature branch
      const branchValidation = checkFeatureBranch(paths.CURRENT_BRANCH, paths.HAS_GIT);
      if (!branchValidation.isValid) {
        const errorMsg = `ERROR: ${branchValidation.error}`;
        return json
          ? JSON.stringify({ error: errorMsg, valid: false })
          : errorMsg;
      }

      // If paths-only mode, output paths and exit
      if (pathsOnly) {
        const pathsData = {
          REPO_ROOT: paths.REPO_ROOT,
          BRANCH: paths.CURRENT_BRANCH,
          FEATURE_DIR: paths.FEATURE_DIR,
          FEATURE_SPEC: paths.FEATURE_SPEC,
          IMPL_PLAN: paths.IMPL_PLAN,
          TASKS: paths.TASKS,
        };
        return json
          ? JSON.stringify(pathsData)
          : [
              `REPO_ROOT: ${pathsData.REPO_ROOT}`,
              `BRANCH: ${pathsData.BRANCH}`,
              `FEATURE_DIR: ${pathsData.FEATURE_DIR}`,
              `FEATURE_SPEC: ${pathsData.FEATURE_SPEC}`,
              `IMPL_PLAN: ${pathsData.IMPL_PLAN}`,
              `TASKS: ${pathsData.TASKS}`,
            ].join('\n');
      }

      // Resolve paths for file operations
      const featureDir = resolvePath(paths.FEATURE_DIR);
      const implPlan = resolvePath(paths.IMPL_PLAN);
      const tasks = resolvePath(paths.TASKS);
      const research = resolvePath(paths.RESEARCH);
      const dataModel = resolvePath(paths.DATA_MODEL);
      const designFile = resolvePath(paths.DESIGN_FILE);
      const contractsDir = resolvePath(paths.CONTRACTS_DIR);
      const quickstart = resolvePath(paths.QUICKSTART);

      // Validate required directories and files
      if (!existsSync(featureDir)) {
        const errorMsg = [
          `ERROR: Feature directory not found: ${featureDir}`,
          `  Current working directory: ${process.cwd()}`,
          `  Expected feature directory: ${featureDir}`,
          "Run 'zo.spec' first to create the feature structure.",
        ].join('\n');
        return json
          ? JSON.stringify({ error: errorMsg, valid: false })
          : errorMsg;
      }

      if (!existsSync(implPlan)) {
        const errorMsg = [
          `ERROR: plan.md not found in ${featureDir}`,
          "Run 'zo.plan' first to create the implementation plan.",
        ].join('\n');
        return json
          ? JSON.stringify({ error: errorMsg, valid: false })
          : errorMsg;
      }

      // Check for tasks.md if required
      if (requireTasks && !existsSync(tasks)) {
        const errorMsg = [
          `ERROR: tasks.md not found in ${featureDir}`,
          "Run 'zo.tasks' first to create the task list.",
        ].join('\n');
        return json
          ? JSON.stringify({ error: errorMsg, valid: false })
          : errorMsg;
      }

      // Build list of available documents
      const availableDocs: string[] = [];

      // Check optional docs
      if (checkFileExists(research)) {
        availableDocs.push('research.md');
      }
      if (checkFileExists(dataModel)) {
        availableDocs.push('data-model.md');
      }
      if (checkFileExists(designFile)) {
        availableDocs.push('design.md');
      }
      if (checkDirExistsWithFiles(contractsDir)) {
        availableDocs.push('contracts/');
      }
      if (checkFileExists(quickstart)) {
        availableDocs.push('quickstart.md');
      }

      // Include tasks.md if requested and it exists
      if (includeTasks && checkFileExists(tasks)) {
        availableDocs.push('tasks.md');
      }

      // Output results
      if (json) {
        const result = {
          FEATURE_DIR: paths.FEATURE_DIR,
          AVAILABLE_DOCS: availableDocs,
          HAS_TASKS: checkFileExists(tasks),
          VALID: true,
        };
        return JSON.stringify(result);
      }

      // Text output
      const lines = [
        `FEATURE_DIR: ${paths.FEATURE_DIR}`,
        'AVAILABLE_DOCS:',
        checkFile(research, 'research.md'),
        checkFile(dataModel, 'data-model.md'),
        checkFile(designFile, 'design.md'),
        checkDir(contractsDir, 'contracts/'),
        checkFile(quickstart, 'quickstart.md'),
      ];

      if (includeTasks) {
        lines.push(checkFile(tasks, 'tasks.md'));
      }

      return lines.join('\n');

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return json
        ? JSON.stringify({ error: errorMessage, valid: false })
        : `ERROR: ${errorMessage}`;
    }
  },
});

/**
 * Check file status and return formatted string
 */
function checkFile(filePath: string, displayName: string): string {
  return checkFileExists(filePath) ? `  ✓ ${displayName}` : `  ✗ ${displayName}`;
}

/**
 * Check directory status and return formatted string
 */
function checkDir(dirPath: string, displayName: string): string {
  return checkDirExistsWithFiles(dirPath) ? `  ✓ ${displayName}` : `  ✗ ${displayName}`;
}
