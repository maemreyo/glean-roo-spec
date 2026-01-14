# Complete Working Example: setup-plan Tool

**Document:** 03-complete-example.md  
**Status:** DRAFT  
**Last Updated:** 2025-01-14

## Overview

This document provides a complete, working example of a Roo Custom Tool from start to finish. The example is based on the `setup-plan.py` Python script, which creates an implementation plan file for the current feature.

---

## Why This Example?

The `setup-plan` tool is ideal because it:
- Has simple, well-defined functionality
- Uses common patterns (template copying, path resolution)
- Demonstrates shared utility imports
- Shows error handling patterns
- Can be easily tested

---

## Complete Tool Implementation

### File: `.roo/tools/setup-plan.ts`

```typescript
/**
 * setup_plan - Initialize implementation plan for current feature
 * 
 * Creates plan.md file in the current feature directory by copying
 * from the template. Uses the feature path detection utilities to
 * locate the correct feature directory based on the current git branch.
 * 
 * @example
 * ```typescript
 * const result = await setup_plan({ json: true })
 * // Returns: {"IMPL_PLAN": "/path/to/feature/plan.md", "FEATURE_SPEC": "..."}
 * ```
 * 
 * @param json - Output results as JSON (default: false)
 * 
 * @returns JSON object or formatted text with created file paths
 * 
 * @throws {Error} If not in a git repository
 * @throws {Error} If feature directory not found
 * @throws {Error} If template file is missing
 * 
 * @see {@link ../lib/util.ts} for path resolution utilities
 * @see {@link ../lib/git-utils.ts} for git operations
 */

import { defineCustomTool } from '@roo-code/types'
import { parametersSchema as z } from '@roo-code/types'
import fs from 'fs'
import path from 'path'
import { getFeaturePaths, getRepoRoot, validateTemplatePath } from '../lib/util.js'

export default defineCustomTool({
  name: 'setup_plan',
  
  description: `
    Initialize implementation plan (plan.md) for the current feature.
    Copies from .zo/templates/plan-template.md to the feature directory.
    Detects feature path from current git branch name.
  `,
  
  parameters: z.object({
    json: z.boolean().optional()
      .describe('Output results as JSON instead of formatted text'),
  }),
  
  async execute({ json }, context) {
    try {
      // Get repository root
      const repoRoot = getRepoRoot()
      
      // Get feature paths using shared utility
      const featurePaths = getFeaturePaths()
      
      // Validate feature directory exists
      if (!fs.existsSync(featurePaths.FEATURE_DIR)) {
        throw new Error(
          `Feature directory not found: ${featurePaths.FEATURE_DIR}\n` +
          `Ensure you're on a feature branch (e.g., 001-feature-name)\n` +
          `Current branch: ${featurePaths.CURRENT_BRANCH}`
        )
      }
      
      // Define template path
      const templatePath = path.join(
        repoRoot,
        '.zo',
        'templates',
        'plan-template.md'
      )
      
      // Validate template exists
      validateTemplatePath(templatePath, 'setup-plan')
      
      // Define output path
      const outputPath = featurePaths.IMPL_PLAN
      
      // Check if plan.md already exists
      if (fs.existsSync(outputPath)) {
        const message = `Plan file already exists: ${outputPath}`
        return json 
          ? JSON.stringify({ error: message, exists: true, path: outputPath })
          : `⚠️  ${message}`
      }
      
      // Read template content
      const templateContent = fs.readFileSync(templatePath, 'utf-8')
      
      // Write to feature directory
      fs.writeFileSync(outputPath, templateContent, 'utf-8')
      
      // Prepare result
      const result = {
        IMPL_PLAN: outputPath,
        FEATURE_SPEC: featurePaths.FEATURE_SPEC,
        DESIGN_FILE: featurePaths.DESIGN_FILE,
        SPECS_DIR: featurePaths.FEATURE_DIR,
        BRANCH: featurePaths.CURRENT_BRANCH,
        HAS_GIT: featurePaths.HAS_GIT,
        created: true,
      }
      
      // Return in requested format
      if (json) {
        return JSON.stringify(result, null, 2)
      }
      
      // Formatted text output
      return [
        '✅ Implementation plan created successfully!',
        '',
        `Plan file: ${result.IMPL_PLAN}`,
        `Feature spec: ${result.FEATURE_SPEC}`,
        `Design file: ${result.DESIGN_FILE}`,
        `Feature dir: ${result.SPECS_DIR}`,
        `Branch: ${result.BRANCH}`,
        `Has git: ${result.HAS_GIT}`,
      ].join('\n')
      
    } catch (error) {
      // Handle errors with context
      const errorMessage = error instanceof Error ? error.message : String(error)
      
      if (json) {
        return JSON.stringify({
          error: errorMessage,
          created: false,
        }, null, 2)
      }
      
      return `❌ Error: ${errorMessage}`
    }
  }
})
```

---

## Required Shared Utilities

### File: `.roo/tools/lib/util.ts`

```typescript
/**
 * Shared utility functions for Roo Custom Tools
 * Converted from .zo/scripts/python/common.py
 */

import fs from 'fs'
import path from 'path'
import { execSync } from 'child_process'

/**
 * Get the repository root directory
 * @returns Absolute path to git repository root
 * @throws {Error} If not in a git repository
 */
export function getRepoRoot(): string {
  try {
    const result = execSync('git rev-parse --show-toplevel', {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    })
    return result.trim()
  } catch (error) {
    throw new Error('Not in a git repository')
  }
}

/**
 * Get the current git branch name
 * @returns Current branch name or 'HEAD' if detached
 */
export function getCurrentBranch(): string {
  try {
    const result = execSync('git rev-parse --abbrev-ref HEAD', {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    })
    const branch = result.trim()
    return branch === 'HEAD' ? 'HEAD' : branch
  } catch (error) {
    return 'unknown'
  }
}

/**
 * Check if current directory is a git repository
 * @returns true if in git repo, false otherwise
 */
export function hasGitRepo(): boolean {
  try {
    execSync('git rev-parse --git-dir', {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    })
    return true
  } catch {
    return false
  }
}

/**
 * Find feature directory by branch name prefix
 * @param repoRoot - Repository root directory
 * @param branchName - Current branch name
 * @returns Feature directory path
 */
export function findFeatureDirByPrefix(
  repoRoot: string,
  branchName: string
): string {
  // Extract feature number from branch (e.g., "001-feature-name" -> "001")
  const match = branchName.match(/^(\d{3})-/)
  if (!match) {
    // Not a feature branch, return repo root
    return repoRoot
  }
  
  const featureNum = match[1]
  const specsDir = path.join(repoRoot, 'specs')
  const featureDir = path.join(specsDir, featureNum)
  
  // Check if feature directory exists
  if (fs.existsSync(featureDir)) {
    return featureDir
  }
  
  // Fallback to repo root
  return repoRoot
}

/**
 * Get feature paths based on current git branch
 * @returns Object containing all feature-related paths
 */
export interface FeaturePaths {
  REPO_ROOT: string
  CURRENT_BRANCH: string
  HAS_GIT: string
  FEATURE_DIR: string
  FEATURE_SPEC: string
  IMPL_PLAN: string
  DESIGN_FILE: string
  TASKS: string
}

export function getFeaturePaths(): FeaturePaths {
  const hasGit = hasGitRepo()
  const repoRoot = hasGit ? getRepoRoot() : process.cwd()
  const currentBranch = hasGit ? getCurrentBranch() : 'unknown'
  
  const featureDir = findFeatureDirByPrefix(repoRoot, currentBranch)
  
  return {
    REPO_ROOT: path.resolve(repoRoot),
    CURRENT_BRANCH: currentBranch,
    HAS_GIT: hasGit ? 'true' : 'false',
    FEATURE_DIR: path.resolve(featureDir),
    FEATURE_SPEC: path.resolve(path.join(featureDir, 'spec.md')),
    IMPL_PLAN: path.resolve(path.join(featureDir, 'plan.md')),
    DESIGN_FILE: path.resolve(path.join(featureDir, 'design.md')),
    TASKS: path.resolve(path.join(featureDir, 'tasks.md')),
  }
}

/**
 * Validate that a template file exists
 * @param templatePath - Path to template file
 * @param toolName - Name of tool using the template
 * @throws {Error} If template file not found
 */
export function validateTemplatePath(
  templatePath: string,
  toolName: string
): void {
  if (!fs.existsSync(templatePath)) {
    throw new Error(
      `Template file not found for ${toolName}: ${templatePath}\n` +
      `Expected location: ${templatePath}\n` +
      `Ensure .zo/templates/ directory exists and contains required templates.`
    )
  }
}
```

---

## Configuration Files

### File: `.roo/tools/package.json`

```json
{
  "name": "roo-custom-tools",
  "version": "1.0.0",
  "description": "Roo Custom Tools for Spec-Driven Development",
  "type": "module",
  "main": "index.ts",
  "scripts": {
    "build": "tsc",
    "watch": "tsc --watch",
    "test": "jest",
    "lint": "eslint lib/**/*.ts tools/**/*.ts",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "@roo-code/types": "latest",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.3.0",
    "jest": "^29.0.0",
    "@types/jest": "^29.0.0",
    "eslint": "^8.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0"
  }
}
```

### File: `.roo/tools/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "rootDir": ".",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "types": ["node"]
  },
  "include": [
    "lib/**/*.ts",
    "tools/**/*.ts"
  ],
  "exclude": [
    "node_modules",
    "dist"
  ]
}
```

---

## Testing the Tool

### Test File: `tests/tools/setup-plan.test.ts`

```typescript
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals'
import fs from 'fs'
import path from 'path'
import { setup_plan } from '../../.roo/tools/setup-plan.js'

describe('setup_plan tool', () => {
  const testFeatureDir = path.join(process.cwd(), 'specs', '999-test')
  const testPlanFile = path.join(testFeatureDir, 'plan.md')
  
  beforeEach(() => {
    // Create test feature directory
    fs.mkdirSync(testFeatureDir, { recursive: true })
  })
  
  afterEach(() => {
    // Clean up test files
    if (fs.existsSync(testPlanFile)) {
      fs.unlinkSync(testPlanFile)
    }
    if (fs.existsSync(testFeatureDir)) {
      fs.rmdirSync(testFeatureDir)
    }
  })
  
  it('should create plan.md from template', async () => {
    const result = await setup_plan.execute({ json: true }, {})
    const parsed = JSON.parse(result)
    
    expect(parsed.created).toBe(true)
    expect(parsed.IMPL_PLAN).toBe(testPlanFile)
    expect(fs.existsSync(testPlanFile)).toBe(true)
  })
  
  it('should return error if feature dir not found', async () => {
    // Test with invalid feature
    const result = await setup_plan.execute({ json: true }, {})
    const parsed = JSON.parse(result)
    
    expect(parsed.created).toBe(false)
    expect(parsed.error).toContain('Feature directory not found')
  })
  
  it('should detect existing plan.md', async () => {
    // Create existing plan
    fs.writeFileSync(testPlanFile, '# Existing Plan')
    
    const result = await setup_plan.execute({ json: true }, {})
    const parsed = JSON.parse(result)
    
    expect(parsed.exists).toBe(true)
    expect(parsed.created).toBe(false)
  })
})
```

---

## Usage Examples

### Example 1: Basic Usage

```typescript
// Call the tool
const result = await setup_plan.execute({ json: false }, {})

console.log(result)
// Output:
// ✅ Implementation plan created successfully!
//
// Plan file: /path/to/specs/001-feature/plan.md
// Feature spec: /path/to/specs/001-feature/spec.md
// Design file: /path/to/specs/001-feature/design.md
// Feature dir: /path/to/specs/001-feature
// Branch: 001-feature-name
// Has git: true
```

### Example 2: JSON Output

```typescript
const result = await setup_plan.execute({ json: true }, {})
const data = JSON.parse(result)

console.log(data.IMPL_PLAN)  // "/path/to/specs/001-feature/plan.md"
console.log(data.created)     // true
```

### Example 3: Error Handling

```typescript
const result = await setup_plan.execute({ json: true }, {})
const data = JSON.parse(result)

if (data.error) {
  console.error('Failed:', data.error)
  // Handle error appropriately
} else if (data.exists) {
  console.log('Plan already exists:', data.path)
} else {
  console.log('Created:', data.IMPL_PLAN)
}
```

---

## Key Patterns Demonstrated

1. **Proper parameter destructuring** in execute signature
2. **Shared utility imports** from `lib/`
3. **Comprehensive error handling** with try-catch
4. **Template validation** before use
5. **Dual output formats** (JSON and text)
6. **Type-safe imports** from `@roo-code/types`
7. **JSDoc documentation** with examples
8. **Zod schema** with `.describe()` for all parameters

---

## Next Steps After This Example

1. **Test** this tool in your environment
2. **Verify** template file exists at `.zo/templates/plan-template.md`
3. **Run** from a feature branch (e.g., `001-test-feature`)
4. **Check** that `plan.md` is created in the feature directory
5. **Use** this as a template for other tools

---

**Related Documents:**
- [01-critical-decisions.md](./01-critical-decisions.md) - Shared utilities strategy
- [02-code-standards.md](./02-code-standards.md) - Coding standards
- [04-implementation-guide.md](./04-implementation-guide.md) - Implementation details
