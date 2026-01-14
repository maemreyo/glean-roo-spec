/**
 * setup_brainstorm_crazy - Initialize context for a "crazy" brainstorm session
 *
 * Creates a new brainstorm file with enhanced template support.
 * Extracts research focus keywords from user input and finds matching spec folders.
 * Uses brainstorm-template-crazy.md for output formatting.
 *
 * Ported from: .zo/scripts/python/setup-brainstorm-crazy.py
 *
 * @example
 * ```typescript
 * const result = await setup_brainstorm_crazy({ request: "improve login flow" })
 * // Returns: {"OUTPUT_FILE": "/path/to/brainstorms/improve-login-flow-2025-01-14.md", "RESEARCH_FOCUS": "improve-login-flow"}
 * ```
 *
 * @param request - Brainstorm request text (required)
 * @param json - Output results in JSON format (default: true)
 * @param dryRun - Show what would be found without creating files (default: false)
 *
 * @returns JSON object with output file path and related spec information
 *
 * @throws {Error} If execution environment validation fails
 * @throws {Error} If no brainstorm request is provided
 * @throws {Error} If research focus cannot be extracted
 *
 * @see {@link ../lib/util.ts} for path resolution utilities
 */

import { defineCustomTool } from '@roo-code/types';
import { parametersSchema as z } from '@roo-code/types';
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { checkFileExists, getRepoRoot, resolvePath, validateExecutionEnvironment } from './lib/util.js';

/**
 * Common words to remove when extracting research focus
 */
const COMMON_WORDS = new Set([
  'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when', 'at',
  'of', 'for', 'to', 'in', 'on', 'with', 'by', 'from', 'as', 'is', 'are',
  'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
  'did', 'will', 'would', 'could', 'should', 'might', 'must', 'may', 'might',
  'about', 'above', 'after', 'again', 'against', 'all', 'also', 'any',
  'around', 'as', 'at', 'because', 'been', 'before', 'being', 'below',
  'between', 'both', 'but', 'by', 'can', 'could', 'did', 'do', 'does',
  'doing', 'down', 'during', 'each', 'few', 'for', 'from', 'further',
  'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself',
  'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it',
  'its', 'itself', 'just', 'like', 'me', 'more', 'most', 'my', 'myself',
  'no', 'nor', 'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or',
  'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own',
  'same', 'she', 'should', 'since', 'so', 'some', 'such', 'than', 'that',
  'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these',
  'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up',
  'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while',
  'who', 'whom', 'why', 'with', 'would', 'you', 'your', 'yours', 'yourself',
  'yourselves',
]);

export default defineCustomTool({
  name: 'setup_brainstorm_crazy',

  description: `
    Initialize context for a "crazy" brainstorm session with enhanced template support.
    Creates brainstorm file in .zo/brainstorms/ with date-based naming.
    Extracts research focus keywords and finds related spec folders if they exist.
  `,

  parameters: z.object({
    request: z
      .string()
      .describe('Brainstorm request text (e.g., "improve login flow")'),
    json: z
      .boolean()
      .optional()
      .default(true)
      .describe('Output results in JSON format'),
    dryRun: z
      .boolean()
      .optional()
      .default(false)
      .describe('Show what would be found without creating files'),
  }),

  async execute({ request, json = true, dryRun = false }, _context) {
    try {
      // Validate execution environment
      if (!validateExecutionEnvironment()) {
        const errorMsg = 'ERROR: Execution environment validation failed.';
        return JSON.stringify({ error: errorMsg, created: false });
      }

      // Validate request parameter
      if (!request || request.trim() === '') {
        const errorMsg = 'ERROR: No brainstorm request provided.';
        return JSON.stringify({ error: errorMsg, created: false });
      }

      // Get paths
      const repoRoot = getRepoRoot();
      const specsDir = join(repoRoot, 'specs');
      const brainstormsDir = join(repoRoot, '.zo', 'brainstorms');
      const templatesDir = join(repoRoot, '.zo', 'templates');

      // Extract research focus
      const researchFocus = extractResearchFocus(request);
      if (!researchFocus) {
        const errorMsg = 'ERROR: Could not extract research focus from input.';
        return JSON.stringify({ error: errorMsg, created: false });
      }

      // Find matching spec folder
      const specFolder = findSpecFolder(researchFocus, specsDir);

      let specDir: string | null = null;
      let featureSpec: string | null = null;
      let implPlan: string | null = null;
      let tasks: string | null = null;

      if (specFolder) {
        specDir = join(specsDir, specFolder);
        const related = findRelatedFiles(specDir);
        featureSpec = related.featureSpec;
        implPlan = related.implPlan;
        tasks = related.tasks;
      }

      // Generate output file path
      const dateStr = new Date().toISOString().split('T')[0] || '';
      const outputFileName = `${researchFocus}-${dateStr}.md`;
      const outputFile = join(brainstormsDir, outputFileName);

      // Create directory if needed (only if not dry-run)
      if (!dryRun) {
        if (!existsSync(brainstormsDir)) {
          mkdirSync(brainstormsDir, { recursive: true });
        }

        // Use template if available
        const templatePath = join(templatesDir, 'brainstorm-template-crazy.md');

        if (existsSync(templatePath)) {
          // Read template
          const content = readFileSync(templatePath, 'utf-8');

          // Replace placeholders
          let processedContent = content.replace(/\{\{DATE\}\}/g, dateStr);
          processedContent = processedContent.replace(/\{\{FEATURE\}\}/g, researchFocus);

          // Write output file
          writeFileSync(outputFile, processedContent, 'utf-8');
        } else {
          // Fallback to empty file if template missing
          writeFileSync(outputFile, '', 'utf-8');
        }
      }

      // Output JSON
      const result = {
        OUTPUT_FILE: outputFile,
        FEATURE_SPEC: featureSpec,
        IMPL_PLAN: implPlan,
        TASKS: tasks,
        RESEARCH_FOCUS: researchFocus,
        SPEC_DIR: specDir || '',
        created: !dryRun,
      };

      return JSON.stringify(result);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return JSON.stringify({ error: errorMessage, created: false });
    }
  },
});

/**
 * Extract research focus from user input by removing common words
 *
 * Matches bash behavior for keyword extraction:
 * - Convert to lowercase
 * - Remove common words using word boundaries
 * - Normalize whitespace
 * - Remove punctuation
 * - Convert spaces to hyphens
 * - Remove duplicate hyphens
 */
function extractResearchFocus(inputText: string): string {
  // Convert to lowercase
  let focus = inputText.toLowerCase();

  // Remove common words using word boundaries
  for (const word of COMMON_WORDS) {
    const regex = new RegExp(`\\b${word}\\b`, 'g');
    focus = focus.replace(regex, ' ');
  }

  // Normalize whitespace
  focus = focus.replace(/\s+/g, ' ').trim();

  // Remove punctuation
  focus = focus.replace(/[.,!?:;()\[\]{}]/g, '');

  // Convert spaces to hyphens
  focus = focus.replace(/ /g, '-');

  // Remove duplicate hyphens
  focus = focus.replace(/-+/g, '-');

  // Remove leading/trailing hyphens
  focus = focus.replace(/^-+|-+$/g, '');

  return focus;
}

/**
 * Find matching spec folder based on research focus keywords
 *
 * Scores folders based on keyword matches and recency (numbered folders).
 * Returns the best matching folder name, or null if no match found.
 */
function findSpecFolder(focus: string, specsDir: string): string | null {
  if (!existsSync(specsDir)) {
    return null;
  }

  // Get list of spec folders, sorted in reverse (newest first)
  let folders: string[] = [];
  try {
    const entries = readdirSync(specsDir, { withFileTypes: true });
    folders = entries
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name)
      .sort()
      .reverse();
  } catch {
    return null;
  }

  let bestMatch: string | null = null;
  let bestScore = 0;

  // Split focus into keywords
  const keywords = focus.split('-');

  for (const folder of folders) {
    const folderName = folder.toLowerCase();
    let score = 0;

    // Score based on keyword matches
    for (const keyword of keywords) {
      if (keyword && folderName.includes(keyword)) {
        score += 1;
      }
    }

    // Bonus for numbered folders (higher number = more recent)
    const match = folder.match(/^(\d+)-/);
    if (match) {
      const num = Number.parseInt(match[1]!, 10);
      // Add score based on recency (normalized)
      score = score * 100 + num;
    }

    if (score > bestScore) {
      bestScore = score;
      bestMatch = folder;
    }
  }

  return bestMatch;
}

/**
 * Find related files (spec.md, plan.md, tasks.md) in spec directory
 *
 * Returns paths to existing files, or null for missing files.
 * Checks both lowercase and uppercase variants.
 */
function findRelatedFiles(specDir: string): {
  featureSpec: string | null;
  implPlan: string | null;
  tasks: string | null;
} {
  let featureSpec: string | null = null;
  let implPlan: string | null = null;
  let tasks: string | null = null;

  // Check for spec.md
  if (checkFileExists(join(specDir, 'spec.md'))) {
    featureSpec = join(specDir, 'spec.md');
  } else if (checkFileExists(join(specDir, 'SPEC.md'))) {
    featureSpec = join(specDir, 'SPEC.md');
  }

  // Check for plan.md
  if (checkFileExists(join(specDir, 'plan.md'))) {
    implPlan = join(specDir, 'plan.md');
  } else if (checkFileExists(join(specDir, 'PLAN.md'))) {
    implPlan = join(specDir, 'PLAN.md');
  }

  // Check for tasks.md
  if (checkFileExists(join(specDir, 'tasks.md'))) {
    tasks = join(specDir, 'tasks.md');
  } else if (checkFileExists(join(specDir, 'TASKS.md'))) {
    tasks = join(specDir, 'TASKS.md');
  }

  return { featureSpec, implPlan, tasks };
}
