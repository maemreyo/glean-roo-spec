# Code Standards for Roo Custom Tools

**Document:** 02-code-standards.md  
**Status:** DRAFT  
**Last Updated:** 2025-01-14

## Overview

This document defines coding standards for Roo Custom Tools, addressing parameter patterns, naming conventions, and documentation requirements.

---

## 1. Parameter Destructuring Pattern

### Issue (CRITICAL #1)

The original plan showed conflicting patterns:
- `async execute(args, context)` 
- `async execute({ url })`

### Standard: Destructure in Signature

**Always destructure parameters in the execute signature for type safety:**

```typescript
// ✅ CORRECT - Destructure in signature
export default defineCustomTool({
  name: 'check_prerequisites',
  parameters: z.object({
    json: z.boolean().optional(),
    requireTasks: z.boolean().optional(),
    includeTasks: z.boolean().optional(),
    pathsOnly: z.boolean().optional(),
  }),
  async execute({ json, requireTasks, includeTasks, pathsOnly }, context) {
    // Parameters are properly typed
    if (json) {
      return JSON.stringify({ /* ... */ })
    }
  }
})

// ❌ INCORRECT - Destructure in body
export default defineCustomTool({
  name: 'check_prerequisites',
  parameters: z.object({
    json: z.boolean().optional(),
  }),
  async execute(args, context) {
    const { json } = args  // No type safety
    // ...
  }
})
```

### Why This Matters

1. **Type Safety**: TypeScript infers types from Zod schema
2. **Early Errors**: Invalid parameter names caught at compile time
3. **Better IDE Support**: Autocomplete works correctly
4. **Consistency**: All tools follow the same pattern

### Complete Example with Context

```typescript
import { defineCustomTool } from '@roo-code/types'
import { parametersSchema as z } from '@roo-code/types'
import { getFeaturePaths } from '../lib/util.js'

export default defineCustomTool({
  name: 'check_prerequisites',
  description: 'Check feature prerequisites and available documentation',
  parameters: z.object({
    json: z.boolean().optional()
      .describe('Output in JSON format'),
    requireTasks: z.boolean().optional()
      .describe('Require tasks.md to exist'),
    includeTasks: z.boolean().optional()
      .describe('Include tasks.md in output'),
    pathsOnly: z.boolean().optional()
      .describe('Only output paths, no validation'),
  }),
  
  // Destructure all parameters in signature
  async execute(
    { json, requireTasks, includeTasks, pathsOnly }, 
    context
  ) {
    // context provides mode and task information
    const mode = context?.mode || 'unknown'
    
    // Get feature paths using shared utility
    const paths = getFeaturePaths()
    
    // Validate based on parameters
    const results = {
      FEATURE_DIR: paths.FEATURE_DIR,
      AVAILABLE_DOCS: [],
      HAS_TASKS: false,
    }
    
    // Return appropriate format
    return json ? JSON.stringify(results) : formatAsText(results)
  }
})
```

---

## 2. Tool Naming Conventions

### Issue (MINOR #13)

Need clear guidelines for naming tools.

### Standards

#### Tool File Names

Use **kebab-case** for file names:

```
✅ check-prerequisites.ts
✅ create-feature.ts
✅ setup-brainstorm.ts
✅ setup-roast-verify.ts

❌ checkPrerequisites.ts
❌ CreateFeature.ts
❌ setup_brainstorm.ts
```

#### Tool Names (in `defineCustomTool`)

Use **snake_case** for the `name` property (matching Python script names):

```typescript
export default defineCustomTool({
  name: 'check_prerequisites',  // ✅ snake_case
  // NOT: checkPrerequisites, CHECK-PREREQUISITES, etc.
})
```

#### Prefixing Conventions

| Prefix | Usage | Example |
|--------|-------|---------|
| `zo_` | Reserved for legacy compatibility | `zo_setup` |
| `check_` | Validation/verification tools | `check_prerequisites` |
| `setup_` | File/document creation tools | `setup_plan`, `setup_design` |
| `create_` | Feature/branch creation | `create_feature` |
| `get_` | Read-only information retrieval | `get_feature_paths` |

#### Matching Python Names

Where possible, tool names should match their Python equivalents:

| Python Script | TypeScript Tool | Notes |
|---------------|-----------------|-------|
| `check-prerequisites.py` | `check_prerequisites` | Direct match |
| `create-feature-from-idea.py` | `create_feature` | Combined with create-new-feature |
| `setup-brainstorm-crazy.py` | `setup_brainstorm_crazy` | Direct match |

---

## 3. Documentation Requirements

### Issue (MINOR #16)

Each tool needs comprehensive documentation.

### Required Documentation Elements

#### JSDoc Comments

Every tool file must have a JSDoc comment block:

```typescript
/**
 * check_prerequisites - Validate feature prerequisites
 * 
 * Checks if the current feature has required documentation files
 * and directories. Called by Roo modes before performing operations.
 * 
 * @example
 * ```typescript
 * const result = await check_prerequisites({
 *   json: true,
 *   requireTasks: false
 * })
 * ```
 * 
 * @param json - Output in JSON format (default: false)
 * @param requireTasks - Require tasks.md to exist (default: false)
 * @param includeTasks - Include tasks.md in output (default: false)
 * @param pathsOnly - Only output paths, skip validation (default: false)
 * 
 * @returns JSON object or formatted text with feature paths and available docs
 * 
 * @throws {Error} If not in a git repository
 * @throws {Error} If feature directory not found
 * 
 * @see {@link ../lib/util.ts#getFeaturePaths} for path resolution logic
 */
export default defineCustomTool({
  // ...
})
```

#### Inline Parameter Descriptions

Use Zod's `.describe()` for every parameter:

```typescript
parameters: z.object({
  featureDir: z.string().optional()
    .describe('Path to feature directory (defaults to current feature)'),
  json: z.boolean().optional()
    .describe('Output results as JSON instead of formatted text'),
  includeTasks: z.boolean().optional()
    .describe('Include task IDs and descriptions in output'),
})
```

#### Tool Description

The `description` field should:
- Start with a verb (Check, Create, Setup, etc.)
- Be 1-2 sentences max
- Mention any side effects (file writes, git operations)

```typescript
description: `
  Check if the current feature branch has required documentation files.
  Returns available docs (research.md, data-model.md, design.md) and
  validates prerequisites for operations.
`
```

### Usage Examples

Add examples for complex tools:

```typescript
/**
 * @example Basic usage
 * ```bash
 * # Check prerequisites for current feature
 * check_prerequisites --json
 * ```
 * 
 * @example With validation
 * ```bash
 * # Require tasks.md to exist
 * check_prerequisites --require-tasks
 * ```
 * 
 * @example Paths only
 * ```bash
 * # Get paths without validation
 * check_prerequisites --paths-only
 * ```
 */
```

### Return Value Documentation

Document the return value format:

```typescript
/**
 * @returns {string} JSON string or formatted text
 * 
 * **JSON format:**
 * ```json
 * {
 *   "FEATURE_DIR": "/path/to/specs/001-feature",
 *   "FEATURE_SPEC": "/path/to/specs/001-feature/spec.md",
 *   "AVAILABLE_DOCS": ["research.md", "data-model.md"],
 *   "HAS_TASKS": true
 * }
 * ```
 * 
 * **Text format:**
 * ```
 * Feature Directory: /path/to/specs/001-feature
 * Available Docs: research.md, data-model.md
 * Has Tasks: Yes
 * ```
 */
```

---

## 4. Complete Code Template

Here's a complete template following all standards:

```typescript
/**
 * tool_name - Brief description
 * 
 * Detailed description of what the tool does, when it's used,
 * and any important side effects or considerations.
 * 
 * @example
 * ```typescript
 * const result = await tool_name({
 *   param1: 'value1',
 *   param2: true
 * })
 * ```
 * 
 * @param paramName - Description of parameter
 * 
 * @returns Description of return value
 * 
 * @throws {Error} When and why error is thrown
 * 
 * @see {@link ../lib/util.ts} for related utilities
 */

import { defineCustomTool } from '@roo-code/types'
import { parametersSchema as z } from '@roo-code/types'
import { someUtility } from '../lib/util.js'

export default defineCustomTool({
  name: 'tool_name',  // snake_case
  
  description: `
    Brief description (1-2 sentences). Mention side effects
    like file writes, git operations, or external dependencies.
  `,
  
  parameters: z.object({
    // Use .describe() for every parameter
    requiredParam: z.string()
      .describe('Required parameter description'),
    optionalParam: z.boolean().optional()
      .describe('Optional parameter with default'),
    unionParam: z.string().or(z.number()).optional()
      .describe('Can be string or number'),
    arrayParam: z.array(z.string()).optional()
      .describe('Array of strings'),
  }),
  
  // Always destructure in signature
  async execute(
    { requiredParam, optionalParam, unionParam, arrayParam }, 
    context
  ) {
    // Access context if needed
    const mode = context?.mode
    
    // Use shared utilities
    const result = someUtility(requiredParam)
    
    // Return appropriate format
    return optionalParam ? JSON.stringify(result) : formatText(result)
  }
})
```

---

## 5. Quick Reference

### Naming Patterns

| Context | Convention | Example |
|---------|-----------|---------|
| File names | kebab-case | `check-prerequisites.ts` |
| Tool names | snake_case | `check_prerequisites` |
| Variables | camelCase | `featureDir`, `requireTasks` |
| Constants | UPPER_SNAKE_CASE | `MAX_BRANCH_LENGTH` |
| TypeScript types | PascalCase | `FeaturePaths`, `GitResult` |

### Import Paths

```typescript
// Import from lib (use .js extension!)
import { util1, util2 } from '../lib/util.js'
import { featureUtil } from '../lib/feature-utils.js'

// Import from @roo-code/types
import { defineCustomTool } from '@roo-code/types'
import { parametersSchema as z } from '@roo-code/types'
```

### Common Patterns

```typescript
// Optional boolean with default
z.boolean().optional().describe('Description')

// String with default value
z.string().default('default-value').describe('Description')

// Union type
z.string().or(z.number()).optional().describe('String or number')

// Array of items
z.array(z.string()).describe('List of strings')

// Enum-like
z.enum(['option1', 'option2', 'option3']).describe('Choose one')
```

---

## Summary Checklist

Each tool must:

- [ ] Use destructured parameters in execute signature
- [ ] Use snake_case for tool name
- [ ] Use kebab-case for file name
- [ ] Include JSDoc comment block
- [ ] Add `.describe()` for every parameter
- [ ] Document return value format
- [ ] Include usage examples for complex tools
- [ ] Import from `lib/` with `.js` extension

---

**Related Documents:**
- [01-critical-decisions.md](./01-critical-decisions.md) - Shared utility strategy
- [03-complete-example.md](./03-complete-example.md) - Full working tool
- [04-implementation-guide.md](./04-implementation-guide.md) - Implementation details
