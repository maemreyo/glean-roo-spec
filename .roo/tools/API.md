# API Reference

Complete API documentation for Roo Custom Tools.

## Table of Contents

- [Tools Reference](#tools-reference)
- [Shared Utilities](#shared-utilities)
- [Type Definitions](#type-definitions)
- [Usage Patterns](#usage-patterns)
- [Best Practices](#best-practices)

---

## Tools Reference

### check_prerequisites

Validates feature prerequisites and available documentation files.

**Tool Name:** `check_prerequisites`

**Source:** [`check-prerequisites.ts`](check-prerequisites.ts)

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `json` | `boolean` | No | `false` | Output in JSON format (compact, no indentation) |
| `requireTasks` | `boolean` | No | `false` | Require tasks.md to exist (for implementation phase) |
| `includeTasks` | `boolean` | No | `false` | Include tasks.md in AVAILABLE_DOCS list |
| `pathsOnly` | `boolean` | No | `false` | Only output path variables without validation |

**Return Value:**

When `json: true`, returns a JSON object:

```typescript
{
  FEATURE_DIR: string;        // Path to feature directory
  AVAILABLE_DOCS: string[];   // List of available docs
  HAS_TASKS: boolean;         // Whether tasks.md exists
  VALID: boolean;             // Whether validation passed
}
```

When `json: false`, returns formatted text output.

**Throws:**

- `Error` if execution environment validation fails
- `Error` if not on a valid feature branch
- `Error` if feature directory not found
- `Error` if plan.md not found
- `Error` if tasks.md required but not found

**Example Usage:**

```typescript
// Check prerequisites with JSON output
const result = await check_prerequisites({ json: true });
const data = JSON.parse(result);

if (data.VALID) {
  console.log(`Feature: ${data.FEATURE_DIR}`);
  console.log(`Docs: ${data.AVAILABLE_DOCS.join(', ')}`);
}

// Require tasks for implementation phase
const implCheck = await check_prerequisites({ 
  json: true, 
  requireTasks: true 
});

// Get only paths
const paths = JSON.parse(
  await check_prerequisites({ pathsOnly: true })
);
```

---

### setup_plan

Creates implementation plan (plan.md) from template.

**Tool Name:** `setup_plan`

**Source:** [`setup-plan.ts`](setup-plan.ts)

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `json` | `boolean` | No | `false` | Output in JSON format |

**Return Value:**

When `json: true`:

```typescript
{
  created: boolean;
  path: string;
  template?: string;
}
```

**Example Usage:**

```typescript
// Create plan from template
const result = await setup_plan({ json: true });
const data = JSON.parse(result);

if (data.created) {
  console.log(`Plan created at: ${data.path}`);
}
```

---

### setup_design

Creates design document (design.md) from template.

**Tool Name:** `setup_design`

**Source:** [`setup-design.ts`](setup-design.ts)

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `json` | `boolean` | No | `false` | Output in JSON format |

**Return Value:**

When `json: true`:

```typescript
{
  created: boolean;
  path: string;
  template?: string;
}
```

---

### setup_brainstorm

Creates brainstorming document (brainstorm.md) from template.

**Tool Name:** `setup_brainstorm`

**Source:** [`setup-brainstorm.ts`](setup-brainstorm.ts)

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `json` | `boolean` | No | `false` | Output in JSON format |

**Return Value:**

When `json: true`:

```typescript
{
  created: boolean;
  path: string;
  template?: string;
}
```

---

### setup_brainstorm_crazy

Creates "crazy ideas" brainstorming document.

**Tool Name:** `setup_brainstorm_crazy`

**Source:** [`setup-brainstorm-crazy.ts`](setup-brainstorm-crazy.ts)

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `json` | `boolean` | No | `false` | Output in JSON format |

**Return Value:**

When `json: true`:

```typescript
{
  created: boolean;
  path: string;
  template?: string;
}
```

---

### setup_roast

Creates roast document for feature review.

**Tool Name:** `setup_roast`

**Source:** [`setup-roast.ts`](setup-roast.ts)

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `json` | `boolean` | No | `false` | Output in JSON format |

**Return Value:**

When `json: true`:

```typescript
{
  created: boolean;
  path: string;
  template?: string;
}
```

---

### setup_roast_verify

Creates verification document for roast review.

**Tool Name:** `setup_roast_verify`

**Source:** [`setup-roast-verify.ts`](setup-roast-verify.ts)

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `json` | `boolean` | No | `false` | Output in JSON format |

**Return Value:**

When `json: true`:

```typescript
{
  created: boolean;
  path: string;
  template?: string;
}
```

---

### setup_specify_idea

Creates specification document for an idea.

**Tool Name:** `setup_specify_idea`

**Source:** [`setup-specify-idea.ts`](setup-specify-idea.ts)

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `json` | `boolean` | No | `false` | Output in JSON format |

**Return Value:**

When `json: true`:

```typescript
{
  created: boolean;
  path: string;
  template?: string;
}
```

---

### create_feature

Creates a new feature from an idea description.

**Tool Name:** `create_feature`

**Source:** [`create-feature.ts`](create-feature.ts)

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `description` | `string` | Yes | - | Feature description |
| `number` | `string` | No | auto | Feature number (e.g., "001") |
| `json` | `boolean` | No | `false` | Output in JSON format |

**Return Value:**

When `json: true`:

```typescript
{
  created: boolean;
  feature_number: string;
  feature_dir: string;
  branch?: string;
  error?: string;
}
```

**Example Usage:**

```typescript
// Create feature with auto-generated number
const result = await create_feature({ 
  description: "Add user authentication" 
});

// Create feature with specific number
const result = await create_feature({ 
  description: "Add user authentication",
  number: "001",
  json: true
});
const data = JSON.parse(result);

if (data.created) {
  console.log(`Feature ${data.feature_number} created`);
  console.log(`Directory: ${data.feature_dir}`);
  console.log(`Branch: ${data.branch}`);
}
```

---

## Shared Utilities

### lib/util.ts

Core utilities for path resolution, git operations, and file system operations.

**Source:** [`lib/util.ts`](lib/util.ts)

#### Environment Validation

```typescript
/**
 * Validates the execution environment
 * @returns true if environment is valid
 */
function validateExecutionEnvironment(): boolean;
```

#### Path Resolution

```typescript
/**
 * Gets feature directory paths based on current context
 * @returns Object containing all feature paths
 */
function getFeaturePaths(): FeaturePaths;
```

**FeaturePaths Interface:**

```typescript
interface FeaturePaths {
  REPO_ROOT: string;
  CURRENT_BRANCH: string;
  HAS_GIT: string;
  FEATURE_DIR: string;
  FEATURE_SPEC: string;
  IMPL_PLAN: string;
  TASKS: string;
  RESEARCH: string;
  DATA_MODEL: string;
  DESIGN_FILE: string;
  CONTRACTS_DIR: string;
  QUICKSTART: string;
}
```

```typescript
/**
 * Resolves a path relative to current working directory
 * @param path - Path to resolve
 * @returns Resolved absolute path
 */
function resolvePath(path: string): string;
```

#### Git Operations

```typescript
/**
 * Checks if current branch is a valid feature branch
 * @param branch - Current branch name
 * @param hasGit - Whether git is available
 * @returns Validation result with error message if invalid
 */
function checkFeatureBranch(
  branch: string,
  hasGit: string
): { isValid: boolean; error?: string };
```

#### File System

```typescript
/**
 * Checks if a file exists
 * @param path - File path to check
 * @returns true if file exists
 */
function checkFileExists(path: string): boolean;
```

```typescript
/**
 * Checks if a directory exists and contains files
 * @param path - Directory path to check
 * @returns true if directory exists with files
 */
function checkDirExistsWithFiles(path: string): boolean;
```

```typescript
/**
 * Checks if a directory contains specific files
 * @param dirPath - Directory path
 * @param files - Array of filenames to check
 * @returns true if all files exist in directory
 */
function checkDirExistsWithFiles(dirPath: string, files: string[]): boolean;
```

#### Path Utilities

```typescript
/**
 * Gets repository root directory
 * @returns Path to repository root
 */
function getRepoRoot(): string;
```

```typescript
/**
 * Gets current git branch name
 * @returns Current branch name or 'unknown'
 */
function getCurrentBranch(): string;
```

```typescript
/**
 * Checks if git is available
 * @returns true if git command is available
 */
function hasGit(): boolean;
```

---

### lib/feature-utils.ts

Feature-specific utilities for managing feature specifications.

**Source:** [`lib/feature-utils.ts`](lib/feature-utils.ts)

#### Feature Number Management

```typescript
/**
 * Gets the next available feature number
 * @returns Next feature number (e.g., "002")
 */
function getNextFeatureNumber(): string;
```

#### Branch Management

```typescript
/**
 * Creates a new feature branch
 * @param featureNumber - Feature number for branch name
 * @returns Created branch name
 */
function createFeatureBranch(featureNumber: string): string;
```

#### Context Management

```typescript
/**
 * Updates agent context files with feature information
 * @param featureNumber - Feature number
 * @param featureDir - Feature directory path
 * @returns true if update successful
 */
function updateAgentContext(
  featureNumber: string,
  featureDir: string
): boolean;
```

---

## Type Definitions

### FeaturePaths

```typescript
interface FeaturePaths {
  REPO_ROOT: string;           // Repository root directory
  CURRENT_BRANCH: string;       // Current git branch name
  HAS_GIT: string;             // 'true' or 'false'
  FEATURE_DIR: string;         // Feature directory path
  FEATURE_SPEC: string;        // Spec file path
  IMPL_PLAN: string;           // Implementation plan path
  TASKS: string;               // Tasks file path
  RESEARCH: string;            // Research doc path
  DATA_MODEL: string;          // Data model doc path
  DESIGN_FILE: string;         // Design doc path
  CONTRACTS_DIR: string;       // Contracts directory path
  QUICKSTART: string;          // Quickstart doc path
}
```

### ToolResult

```typescript
interface ToolResult {
  success: boolean;
  data?: Record<string, unknown>;
  error?: string;
}
```

### CreateFeatureResult

```typescript
interface CreateFeatureResult {
  created: boolean;
  feature_number: string;
  feature_dir: string;
  branch?: string;
  error?: string;
}
```

### CheckPrerequisitesResult

```typescript
interface CheckPrerequisitesResult {
  FEATURE_DIR: string;
  AVAILABLE_DOCS: string[];
  HAS_TASKS: boolean;
  VALID: boolean;
}
```

---

## Usage Patterns

### Pattern 1: Validation Before Operation

```typescript
// Always validate prerequisites before performing operations
const check = await check_prerequisites({ json: true });
const result = JSON.parse(check);

if (!result.VALID) {
  console.error('Prerequisites not met');
  return;
}

// Proceed with operation
await setup_plan({ json: true });
```

### Pattern 2: Error Handling

```typescript
// Always parse JSON output with error handling
try {
  const result = await create_feature({ 
    description: "New feature",
    json: true 
  });
  const data = JSON.parse(result);
  
  if (data.error) {
    console.error(`Error: ${data.error}`);
    return;
  }
  
  console.log(`Success: ${data.feature_dir}`);
} catch (error) {
  console.error(`Parse error: ${error}`);
}
```

### Pattern 3: Batch Operations

```typescript
// Create multiple docs at once
const tools = [
  setup_plan,
  setup_design,
  setup_brainstorm,
  setup_roast
];

for (const tool of tools) {
  const result = await tool({ json: true });
  const data = JSON.parse(result);
  
  if (data.created) {
    console.log(`Created: ${data.path}`);
  }
}
```

### Pattern 4: Feature Workflow

```typescript
// Complete feature creation workflow
async function createNewFeature(description: string) {
  // 1. Create feature
  const feature = await create_feature({ 
    description,
    json: true 
  });
  const featureData = JSON.parse(feature);
  
  if (!featureData.created) {
    throw new Error(featureData.error);
  }
  
  // 2. Check prerequisites
  const check = await check_prerequisites({ json: true });
  const checkData = JSON.parse(check);
  
  // 3. Create documentation
  await setup_plan({ json: true });
  await setup_design({ json: true });
  await setup_brainstorm({ json: true });
  
  return featureData;
}
```

---

## Best Practices

### 1. Always Use JSON for Programmatic Access

```typescript
// Good
const result = JSON.parse(await tool({ json: true }));

// Avoid
const text = await tool({ json: false });
```

### 2. Validate Before Operating

```typescript
// Good
const check = JSON.parse(await check_prerequisites({ json: true }));
if (check.VALID) {
  await setup_plan({ json: true });
}

// Avoid
await setup_plan({ json: true }); // May fail if prerequisites not met
```

### 3. Handle Errors Gracefully

```typescript
// Good
try {
  const result = JSON.parse(await tool({ json: true }));
  if (result.error) {
    console.error(`Tool error: ${result.error}`);
    return;
  }
  // Use result
} catch (error) {
  console.error(`Parse error: ${error}`);
}

// Avoid
const result = JSON.parse(await tool({ json: true })); // May throw
```

### 4. Use Type Guards for Error Handling

```typescript
// Good
const errorMessage = error instanceof Error 
  ? error.message 
  : String(error);

// Avoid
const message = error.message; // May not exist
```

### 5. Check Return Values

```typescript
// Good
const result = JSON.parse(await tool({ json: true }));
if (result.created) {
  console.log(`Created at ${result.path}`);
} else {
  console.log('Not created');
}

// Avoid
const result = JSON.parse(await tool({ json: true }));
console.log(`Created at ${result.path}`); // May be undefined
```

### 6. Use Absolute Paths

```typescript
// Good
const resolvedPath = resolvePath(relativePath);

// Avoid
const absolute = path.resolve(relativePath); // May fail in some contexts
```

### 7. Respect Git State

```typescript
// Good
const paths = getFeaturePaths();
if (paths.HAS_GIT === 'true') {
  // Git-specific operations
} else {
  // Fallback behavior
}

// Avoid
// Assume git is always available
```

### 8. Document Custom Parameters

```typescript
// Good
/**
 * Custom tool that extends check_prerequisites
 */
async function myCustomCheck(options: {
  requireTasks?: boolean;
  customCheck?: boolean;
}) {
  return check_prerequisites({ 
    json: true,
    requireTasks: options.requireTasks 
  });
}

// Avoid
// No documentation
```

---

## Related Documentation

- [README.md](README.md) - Overview and quick start
- [MIGRATION.md](MIGRATION.md) - Migration details
- [Testing Strategy](../plans/migration/05-testing-strategy.md) - Testing approach
- [Requirements](../plans/migration/06-requirements.md) - Version and performance requirements
