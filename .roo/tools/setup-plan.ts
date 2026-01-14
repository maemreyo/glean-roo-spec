/**
 * setup_plan - Initialize implementation plan for a feature
 *
 * Creates an implementation plan file in the feature directory using
 * the plan template. Outputs feature paths for AI context.
 *
 * Ported from: .zo/scripts/python/setup-plan.py
 *
 * @example
 * ```typescript
 * const result = await setup_plan({ json: true })
 * // Returns: {"FEATURE_SPEC":"/path/to/spec.md","IMPL_PLAN":"/path/to/plan.md",...}
 * ```
 *
 * @param json - Output results in JSON format (default: false)
 *
 * @returns JSON object or formatted text with feature paths
 *
 * @throws {Error} If execution environment validation fails
 * @throws {Error} If feature directory cannot be determined
 *
 * @see {@link ../lib/util.ts} for path resolution utilities
 */

import { defineCustomTool } from '@roo-code/types';
import { parametersSchema as z } from '@roo-code/types';
import { copyFileSync, existsSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import {
  checkFileExists,
  getFeaturePaths,
  getRepoRoot,
  validateExecutionEnvironment,
} from './lib/util.js';

export default defineCustomTool({
  name: 'setup_plan',

  description: `
    Initialize implementation plan for a feature.
    Creates plan.md in the feature directory using the plan template.
    Outputs feature paths including FEATURE_SPEC, IMPL_PLAN, DESIGN_FILE, etc.
  `,

  parameters: z.object({
    json: z
      .boolean()
      .optional()
      .describe('Output results in JSON format (compact)'),
  }),

  async execute({ json = false }, _context) {
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
      const featureDir = paths.FEATURE_DIR;
      const implPlan = paths.IMPL_PLAN;
      const featureSpec = paths.FEATURE_SPEC;
      const designFile = paths.DESIGN_FILE;
      const currentBranch = paths.CURRENT_BRANCH;
      const hasGit = paths.HAS_GIT;

      // Ensure the feature directory exists
      if (!existsSync(featureDir)) {
        mkdirSync(featureDir, { recursive: true });
      }

      // Copy plan template if it exists
      const templatePath = join(repoRoot, '.zo', 'templates', 'plan-template.md');

      if (checkFileExists(templatePath)) {
        copyFileSync(templatePath, implPlan);
      } else {
        // Create a basic plan file if template doesn't exist
        if (!existsSync(implPlan)) {
          mkdirSync(featureDir, { recursive: true });
        }
      }

      // Prepare result
      const result = {
        FEATURE_SPEC: featureSpec,
        IMPL_PLAN: implPlan,
        DESIGN_FILE: designFile,
        SPECS_DIR: featureDir,
        BRANCH: currentBranch,
        HAS_GIT: hasGit,
      };

      // Return in requested format
      if (json) {
        return JSON.stringify(result);
      }

      // Formatted text output
      return [
        `FEATURE_SPEC: ${result.FEATURE_SPEC}`,
        `IMPL_PLAN: ${result.IMPL_PLAN}`,
        `DESIGN_FILE: ${result.DESIGN_FILE}`,
        `SPECS_DIR: ${result.SPECS_DIR}`,
        `BRANCH: ${result.BRANCH}`,
        `HAS_GIT: ${result.HAS_GIT}`,
      ].join('\n');

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return json
        ? JSON.stringify({ error: errorMessage })
        : `ERROR: ${errorMessage}`;
    }
  },
});
