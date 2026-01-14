/**
 * setup_design - Initialize design documentation for a feature or global design system
 *
 * Creates design documentation either for a specific feature or for the
 * global design system. Uses templates when available.
 *
 * Ported from: .zo/scripts/python/setup-design.py
 *
 * @example
 * ```typescript
 * // Setup feature design
 * const result = await setup_design({ json: true })
 * // Returns: {"MODE":"feature","DESIGN_FILE":"/path/to/design.md",...}
 *
 * // Setup global design system
 * const result = await setup_design({ json: true, globalMode: true })
 * // Returns: {"MODE":"global","DESIGN_FILE":"/path/to/.zo/design-system.md"}
 * ```
 *
 * @param json - Output results in JSON format (default: false)
 * @param globalMode - Setup global design system at .zo/design-system.md (default: false)
 * @param featureDir - Optional feature directory path (defaults to current branch)
 *
 * @returns JSON object or formatted text with design file paths
 *
 * @throws {Error} If execution environment validation fails
 * @throws {Error} If feature directory cannot be determined (in feature mode)
 *
 * @see {@link ../lib/util.ts} for path resolution utilities
 */

import { defineCustomTool } from '@roo-code/types';
import { parametersSchema as z } from '@roo-code/types';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import {
  checkFileExists,
  getCurrentBranch,
  getFeaturePaths,
  getRepoRoot,
  resolvePath,
  validateExecutionEnvironment,
} from './lib/util.js';

export default defineCustomTool({
  name: 'setup_design',

  description: `
    Initialize design documentation for a feature or global design system.
    Creates design.md in the feature directory or .zo/design-system.md for global mode.
    Uses design templates when available.
  `,

  parameters: z.object({
    json: z
      .boolean()
      .optional()
      .describe('Output results in JSON format (compact)'),
    globalMode: z
      .boolean()
      .optional()
      .describe('Setup global design system (.zo/design-system.md)'),
    featureDir: z
      .string()
      .optional()
      .describe('Optional feature directory path (defaults to current branch)'),
  }),

  async execute({ json = false, globalMode = false, featureDir }, _context) {
    try {
      // Validate execution environment
      if (!validateExecutionEnvironment()) {
        const errorMsg = 'ERROR: Execution environment validation failed.';
        return json
          ? JSON.stringify({ error: errorMsg })
          : errorMsg;
      }

      const repoRoot = getRepoRoot();

      // Handle global vs feature mode
      if (globalMode) {
        return setupGlobalDesign(repoRoot, json);
      }

      return setupFeatureDesign(repoRoot, featureDir || '', json);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return json
        ? JSON.stringify({ error: errorMessage })
        : `ERROR: ${errorMessage}`;
    }
  },
});

/**
 * Setup global design system
 */
function setupGlobalDesign(repoRoot: string, jsonMode: boolean): string {
  const designFile = join(repoRoot, '.zo', 'design-system.md');
  const featureSpec = '';
  const featureDir = repoRoot;
  const featureName = 'global';

  // Use global design system template if available
  const templatePath = join(repoRoot, '.zo', 'templates', 'design-system-template.md');

  if (!checkFileExists(designFile) && checkFileExists(templatePath)) {
    const content = readFileSync(templatePath, 'utf-8');
    writeFileSync(designFile, content, 'utf-8');
  }

  const result = {
    MODE: 'global',
    DESIGN_FILE: designFile,
    FEATURE_SPEC: featureSpec,
    FEATURE_DIR: featureDir,
    FEATURE_NAME: featureName,
  };

  if (jsonMode) {
    return JSON.stringify(result);
  }

  return [
    `MODE: ${result.MODE}`,
    `DESIGN_FILE: ${result.DESIGN_FILE}`,
  ].join('\n');
}

/**
 * Setup feature design
 */
function setupFeatureDesign(repoRoot: string, featureArg: string, jsonMode: boolean): string {
  const currentBranch = getCurrentBranch();

  // Handle optional feature directory argument
  let featureDir: string;
  let featureSpec: string;
  let featureName: string;

  if (featureArg) {
    // User provided a feature directory
    if (existsSync(featureArg)) {
      // Absolute or relative path provided
      featureDir = resolve(featureArg);
      featureSpec = join(featureDir, 'spec.md');
      featureName = featureDir.split('/').pop() || currentBranch;
    } else if (existsSync(join(repoRoot, featureArg))) {
      // Path relative to repo root
      featureDir = resolve(join(repoRoot, featureArg));
      featureSpec = join(featureDir, 'spec.md');
      featureName = featureDir.split('/').pop() || currentBranch;
    } else {
      const errorMsg = `Directory '${featureArg}' not found.`;
      return jsonMode
        ? JSON.stringify({ error: errorMsg })
        : errorMsg;
    }
  } else {
    // Auto-detect context from current branch
    const branchMatch = currentBranch.match(/^\d{3}-/);
    if (branchMatch) {
      // Branch name is the feature name
      const paths = getFeaturePaths();
      featureDir = paths.FEATURE_DIR;
      featureSpec = paths.FEATURE_SPEC;
      featureName = currentBranch;
    } else {
      // Fallback to current directory if valid structure
      if (checkFileExists('spec.md')) {
        featureDir = process.cwd();
        featureSpec = join(featureDir, 'spec.md');
        featureName = featureDir.split('/').pop() || currentBranch;
      } else {
        const errorMsg = [
          'Could not determine feature context.',
          'Run inside a feature branch or specify directory.',
        ].join(' ');
        return jsonMode
          ? JSON.stringify({ error: errorMsg })
          : errorMsg;
      }
    }
  }

  // Define output file for feature design
  const designFile = join(featureDir, 'design.md');

  // Use feature design template if available
  const templatePath = join(repoRoot, '.zo', 'templates', 'design-template.md');

  if (!checkFileExists(designFile) && checkFileExists(templatePath)) {
    let content = readFileSync(templatePath, 'utf-8');
    // Replace basic placeholders
    content = content.replace('[FEATURE NAME]', featureName);
    writeFileSync(designFile, content, 'utf-8');
  }

  const result = {
    MODE: 'feature',
    DESIGN_FILE: designFile,
    FEATURE_SPEC: featureSpec,
    FEATURE_DIR: featureDir,
    FEATURE_NAME: featureName,
  };

  if (jsonMode) {
    return JSON.stringify(result);
  }

  return [
    `MODE: ${result.MODE}`,
    `DESIGN_FILE: ${result.DESIGN_FILE}`,
    `FEATURE_SPEC: ${result.FEATURE_SPEC}`,
    `FEATURE_DIR: ${result.FEATURE_DIR}`,
    `FEATURE_NAME: ${result.FEATURE_NAME}`,
  ].join('\n');
}
