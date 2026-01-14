/**
 * setup_brainstorm - Initialize a brainstorm session in .zo/brainstorms/ directory
 *
 * Creates a new brainstorm file with timestamp and optional topic.
 * Uses the brainstorm template when available.
 *
 * Ported from: .zo/scripts/python/setup-brainstorm.py
 *
 * @example
 * ```typescript
 * // With topic
 * const result = await setup_brainstorm({ json: true, topic: "improve login flow" })
 * // Returns: {"OUTPUT_FILE":"/path/to/.zo/brainstorms/improve-login-flow-2025-01-14-1200.md",...}
 *
 * // Without topic
 * const result = await setup_brainstorm({ json: true })
 * // Returns: {"OUTPUT_FILE":"/path/to/.zo/brainstorms/brainstorm-session-2025-01-14-1200.md",...}
 * ```
 *
 * @param json - Output results in JSON format (default: false)
 * @param topic - Optional brainstorm topic (will be slugified for filename)
 *
 * @returns JSON object or formatted text with created file path
 *
 * @throws {Error} If execution environment validation fails
 *
 * @see {@link ../lib/util.ts} for path resolution utilities
 */

import { defineCustomTool } from '@roo-code/types';
import { parametersSchema as z } from '@roo-code/types';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { getRepoRoot } from './lib/util.js';

export default defineCustomTool({
  name: 'setup_brainstorm',

  description: `
    Initialize a brainstorm session in .zo/brainstorms/ directory.
    Creates a new brainstorm file with timestamp and optional topic slug.
    Uses brainstorm template when available.
  `,

  parameters: z.object({
    json: z
      .boolean()
      .optional()
      .describe('Output results in JSON format (compact)'),
    topic: z
      .string()
      .optional()
      .describe('Brainstorm topic (will be slugified for filename)'),
  }),

  async execute({ json = false, topic = '' }, _context) {
    try {
      // Get repository root
      const repoRoot = getRepoRoot();

      // Determine output directory
      const brainstormDir = join(repoRoot, '.zo', 'brainstorms');
      if (!existsSync(brainstormDir)) {
        mkdirSync(brainstormDir, { recursive: true });
      }

      // Generate filename
      const now = new Date();
      const dateStr = now.toISOString().slice(0, 10) + '-' +
                      now.toTimeString().slice(0, 5).replace(':', '');
      const topicInput = topic;

      let filename: string;
      let nameTag: string;

      if (topicInput) {
        // Slugify the input topic
        const topicSlug = slugify(topicInput);
        // Create filename with date for uniqueness
        filename = `${topicSlug}-${dateStr}.md`;
        nameTag = topicSlug;
      } else {
        // Fallback if no topic provided
        filename = `brainstorm-session-${dateStr}.md`;
        nameTag = 'General Session';
      }

      const outputFile = join(brainstormDir, filename);

      // Use template if available
      const templatePath = join(repoRoot, '.zo', 'templates', 'brainstorm-template.md');

      if (existsSync(templatePath)) {
        let content = readFileSync(templatePath, 'utf-8');
        // Replace placeholders
        content = content.replace('{{DATE}}', dateStr);
        content = content.replace('{{FEATURE}}', nameTag);
        writeFileSync(outputFile, content, 'utf-8');
      } else {
        // Fallback to empty file if template missing
        writeFileSync(outputFile, '', 'utf-8');
      }

      // Prepare result
      const result = {
        OUTPUT_FILE: outputFile,
        BRAINSTORM_DIR: brainstormDir,
        TOPIC: nameTag,
      };

      // Return in requested format
      if (json) {
        return JSON.stringify(result);
      }

      return `OUTPUT_FILE: ${result.OUTPUT_FILE}`;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return json
        ? JSON.stringify({ error: errorMessage })
        : `ERROR: ${errorMessage}`;
    }
  },
});

/**
 * Convert text to a slug-safe filename.
 *
 * Matches bash behavior on macOS where sed doesn't collapse hyphens properly.
 * Replaces each non-alphanumeric character with a hyphen.
 *
 * @param text - Text to slugify
 * @returns Slugified string
 */
function slugify(text: string): string {
  // Convert to lowercase
  let result = text.toLowerCase();

  // Replace each non-alphanumeric character with a hyphen
  result = result.split('').map((c) => (/[a-z0-9]/.test(c) ? c : '-')).join('');

  // Remove leading/trailing hyphens
  result = result.replace(/^-+|-+$/g, '');

  return result;
}
