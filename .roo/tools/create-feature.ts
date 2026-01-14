/**
 * create_feature - Create a new feature from a description
 *
 * Combines functionality of create-feature-from-idea.py and create-new-feature.py.
 * Creates a new feature branch and spec file from a feature description.
 * Auto-detects the next branch number, generates a branch name from the description,
 * and creates the spec file from the appropriate template.
 *
 * Ported from: .zo/scripts/python/create-feature-from-idea.py and create-new-feature.py
 *
 * @example
 * ```typescript
 * // Create feature from idea (uses spec-from-idea.md template)
 * const result = await create_feature({
 *   json: true,
 *   mode: 'idea',
 *   featureDescription: 'Add user authentication system'
 * })
 * // Returns: {"BRANCH_NAME":"001-user-auth","SPEC_FILE":"/path/to/spec.md",...}
 *
 * // Create new feature (uses spec-template.md template)
 * const result = await create_feature({
 *   json: true,
 *   mode: 'new',
 *   featureDescription: 'Implement OAuth2 integration',
 *   shortName: 'oauth2',
 *   number: '5'
 * })
 * ```
 *
 * @param json - Output results in JSON format (default: false)
 * @param mode - 'idea' uses spec-from-idea.md template, 'new' uses spec-template.md (default: 'idea')
 * @param featureDescription - Feature description (required)
 * @param shortName - Optional custom short name (2-4 words) for the branch
 * @param number - Optional branch number to manually specify (overrides auto-detection)
 *
 * @returns JSON object or formatted text with created branch and spec file info
 *
 * @throws {Error} If feature description is not provided
 * @throws {Error} If repository root cannot be determined
 *
 * @see {@link ../lib/util.ts} for path resolution utilities
 * @see {@link ../lib/feature-utils.ts} for feature creation utilities
 */

import { defineCustomTool } from '@roo-code/types';
import { parametersSchema as z } from '@roo-code/types';
import { copyFileSync, existsSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import {
  checkExistingBranches,
  cleanBranchName,
  createGitBranch,
  generateBranchName,
  getRepoRoot,
  hasGit,
  truncateBranchName,
} from './lib/feature-utils.js';
import { getRepoRoot as getRepoRootUtil, validateExecutionEnvironment } from './lib/util.js';

export default defineCustomTool({
  name: 'create_feature',

  description: `
    Create a new feature branch and spec file from a feature description.
    Combines 'create-feature-from-idea' and 'create-new-feature' workflows.
    Auto-detects next branch number, generates branch name from description,
    and creates spec file from appropriate template.
  `,

  parameters: z.object({
    json: z
      .boolean()
      .optional()
      .describe('Output results in JSON format (compact)'),
    mode: z
      .enum(['idea', 'new'])
      .optional()
      .describe('Template mode: "idea" uses spec-from-idea.md, "new" uses spec-template.md'),
    featureDescription: z
      .string()
      .describe('Feature description (required)'),
    shortName: z
      .string()
      .optional()
      .describe('Optional custom short name (2-4 words) for the branch'),
    number: z
      .string()
      .optional()
      .describe('Optional branch number to manually specify (overrides auto-detection)'),
  }),

  async execute({ json = false, mode = 'idea', featureDescription, shortName, number }, _context) {
    try {
      // Validate execution environment
      if (!validateExecutionEnvironment()) {
        const errorMsg = 'ERROR: Execution environment validation failed.';
        return json
          ? JSON.stringify({ error: errorMsg })
          : errorMsg;
      }

      // Validate feature description
      if (!featureDescription || featureDescription.trim() === '') {
        const errorMsg = 'ERROR: Feature description is required.';
        return json
          ? JSON.stringify({ error: errorMsg })
          : errorMsg;
      }

      // Get repository root
      const repoRoot = getRepoRootUtil();

      // Check if git is available
      const hasGitRepo = hasGit(repoRoot);

      // Set up specs directory
      const specsDir = join(repoRoot, 'specs');
      if (!existsSync(specsDir)) {
        mkdirSync(specsDir, { recursive: true });
      }

      // Generate branch name suffix
      let branchSuffix: string;
      if (shortName && shortName.trim() !== '') {
        // Use provided short name, just clean it up
        branchSuffix = cleanBranchName(shortName);
      } else {
        // Generate from description with smart filtering
        branchSuffix = generateBranchName(featureDescription);
      }

      // Determine branch number
      let branchNumber: number;
      if (number && number.trim() !== '') {
        // User provided a number - force decimal interpretation
        branchNumber = Number.parseInt(number.trim(), 10);
      } else if (hasGitRepo) {
        // Check existing branches on remotes
        branchNumber = checkExistingBranches(specsDir);
      } else {
        // Fall back to local directory check
        const { getHighestFromSpecs } = await import('./lib/feature-utils.js');
        const highest = getHighestFromSpecs(specsDir);
        branchNumber = highest + 1;
      }

      // Format feature number as 3-digit with leading zeros
      const featureNum = `${branchNumber.toString().padStart(3, '0')}`;

      // Build branch name
      let branchName = `${featureNum}-${branchSuffix}`;

      // Truncate if exceeds GitHub limit
      branchName = truncateBranchName(branchName);

      // Create git branch if available
      if (hasGitRepo) {
        createGitBranch(branchName, repoRoot);
      }

      // Create feature directory
      const featureDir = join(specsDir, branchName);
      if (!existsSync(featureDir)) {
        mkdirSync(featureDir, { recursive: true });
      }

      // Determine which template to use based on mode
      const templateName = mode === 'idea' ? 'spec-from-idea.md' : 'spec-template.md';
      const templatePath = join(repoRoot, '.zo', 'templates', templateName);
      const specFile = join(featureDir, 'spec.md');

      // Copy template to spec file
      if (existsSync(templatePath)) {
        copyFileSync(templatePath, specFile);
      } else {
        // Create empty file if template doesn't exist
        const { writeFileSync } = await import('node:fs');
        writeFileSync(specFile, '', 'utf-8');
      }

      // Set SPECIFY_FEATURE environment variable
      process.env.SPECIFY_FEATURE = branchName;

      // Prepare result
      const result = {
        BRANCH_NAME: branchName,
        SPEC_FILE: specFile,
        FEATURE_NUM: featureNum,
        MODE: mode,
        SPECIFY_FEATURE: branchName,
      };

      // Return in requested format
      if (json) {
        return JSON.stringify(result);
      }

      // Formatted text output
      return [
        `BRANCH_NAME: ${result.BRANCH_NAME}`,
        `SPEC_FILE: ${result.SPEC_FILE}`,
        `FEATURE_NUM: ${result.FEATURE_NUM}`,
        `MODE: ${result.MODE}`,
        `SPECIFY_FEATURE environment variable set to: ${result.SPECIFY_FEATURE}`,
      ].join('\n');

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return json
        ? JSON.stringify({ error: errorMessage })
        : `ERROR: ${errorMessage}`;
    }
  },
});
