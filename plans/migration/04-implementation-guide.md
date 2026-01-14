# Implementation Guide for Roo Custom Tools

**Document:** 04-implementation-guide.md  
**Status:** DRAFT  
**Last Updated:** 2025-01-14

## Overview

This document provides detailed implementation guidance for common patterns used in Roo Custom Tools, including context usage, environment handling, git operations, file system operations, and Zod schema best practices.

---

## 1. Context Object Utilization

### Issue (MAJOR #5)

The `context` parameter provides `mode` and `task` information but was never used in the original plan.

### Context Structure

```typescript
interface ToolContext {
  mode?: string      // Current Roo mode (architect, code, debug, etc.)
  task?: string      // Current task description or identifier
}
```

### When to Use Context

#### Example 1: Mode-Specific Behavior

```typescript
async execute({ featureDir }, context) {
  const mode = context?.mode || 'unknown'
  
  // Provide detailed output in architect mode
  if (mode === 'architect') {
    return this.detailedAnalysis(featureDir)
  }
  
  // Simplified output for other modes
  return this.basicOperation(featureDir)
}
```

#### Example 2: Task-Aware Operations

```typescript
async execute({ path }, context) {
  const task = context?.task
  
  if (task?.includes('create feature')) {
    // Feature creation - validate branch exists
    return this.createFeatureWithBranch(path)
  }
  
  // General file creation
  return this.createFile(path)
}
```

#### Example 3: Logging Based on Mode

```typescript
async execute(args, context) {
  const mode = context?.mode
  
  // Verbose logging in debug mode
  if (mode === 'debug') {
    console.debug('[DEBUG] Executing with args:', args)
  }
  
  // Normal operation
  const result = this.performOperation(args)
  
  return result
}
```

### Best Practices

1. **Always check if context exists**: `context?.mode` not `context.mode`
2. **Provide sensible defaults**: `|| 'unknown'` for missing values
3. **Document mode-specific behavior**: Explain why different modes behave differently
4. **Don't rely on context for critical logic**: Tools should work even if context is undefined

---

## 2. Environment Variable Detection

### Issue (MAJOR #6)

`process.env.PWD` and `process.env.WORKSPACE` are not standard Node.js environment variables.

### Standard Environment Variables

```typescript
/**
 * Get workspace path with fallbacks
 */
export function getWorkspacePath(): string {
  // Try VS Code's PWD first (when launched from VS Code)
  const pwd = process.env.PWD
  if (pwd && fs.existsSync(pwd)) {
    return path.resolve(pwd)
  }
  
  // Try WORKSPACE (custom environment variable)
  const workspace = process.env.WORKSPACE
  if (workspace && fs.existsSync(workspace)) {
    return path.resolve(workspace)
  }
  
  // Fallback to current working directory
  const cwd = process.cwd()
  if (fs.existsSync(cwd)) {
    return path.resolve(cwd)
  }
  
  // Last resort: HOME directory
  const home = process.env.HOME || ''
  if (home && fs.existsSync(home)) {
    return path.resolve(home)
  }
  
  throw new Error('Cannot determine workspace path')
}
```

### Environment-Specific Behavior

```typescript
/**
 * Detect execution environment
 */
export function getExecutionEnvironment(): {
  isVSCode: boolean
  isTerminal: boolean
  isCI: boolean
} {
  return {
    isVSCode: !!process.env.VSCODE_PID || !!process.env.TERM_PROGRAM,
    isTerminal: process.env.TERM !== undefined,
    isCI: process.env.CI === 'true' || !!process.env.CI,
  }
}
```

### Fallback Behavior Table

| Environment | Primary Source | Fallback 1 | Fallback 2 | Fallback 3 |
|-------------|---------------|------------|------------|------------|
| VS Code | `process.env.PWD` | `process.cwd()` | `process.env.HOME` | Error |
| Terminal | `process.cwd()` | `process.env.PWD` | `process.env.HOME` | Error |
| CI/CD | `process.env.WORKSPACE` | `process.cwd()` | `process.env.HOME` | Error |

### Validation Before Use

```typescript
// Validate environment before operations
export function validateExecutionEnvironment(): void {
  const env = getExecutionEnvironment()
  
  if (env.isCI && !process.env.WORKSPACE) {
    console.warn('Running in CI but WORKSPACE not set')
  }
  
  if (!fs.existsSync(process.cwd())) {
    throw new Error('Current working directory does not exist')
  }
}
```

---

## 3. Git Operations Error Handling

### Issue (MAJOR #8)

Missing comprehensive error handling for git operations.

### Complete Git Error Handling

```typescript
/**
 * Run git command with comprehensive error handling
 */
export function runGitCommand(args: string[]): GitResult {
  try {
    // Check if git is installed
    execSync('git --version', {
      stdio: ['pipe', 'pipe', 'pipe'],
    })
  } catch (error) {
    return {
      success: false,
      error: 'Git is not installed or not in PATH',
      code: 'GIT_NOT_FOUND',
    }
  }
  
  try {
    const result = execSync(`git ${args.join(' ')}`, {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 5000,
      maxBuffer: 10 * 1024 * 1024, // 10MB
    })
    
    return {
      success: true,
      output: result.trim(),
      code: 'SUCCESS',
    }
  } catch (error: any) {
    // Parse git error
    const stderr = error.stderr?.toString() || ''
    const stdout = error.stdout?.toString() || ''
    const exitCode = error.status || 1
    
    // Not in a git repository
    if (stderr.includes('not a git repository')) {
      return {
        success: false,
        error: 'Not in a git repository',
        code: 'NOT_GIT_REPO',
      }
    }
    
    // Permission denied
    if (exitCode === 128 && stderr.includes('permission')) {
      return {
        success: false,
        error: 'Permission denied. Check git repository permissions',
        code: 'PERMISSION_DENIED',
      }
    }
    
    // Specific command failures
    if (args[0] === 'branch' && exitCode !== 0) {
      return {
        success: false,
        error: `Branch operation failed: ${stderr}`,
        code: 'BRANCH_ERROR',
      }
    }
    
    // Generic git error
    return {
      success: false,
      error: `Git command failed: ${stderr || stdout}`,
      code: 'GIT_ERROR',
      details: { exitCode, args },
    }
  }
}

interface GitResult {
  success: boolean
  output?: string
  error?: string
  code: string
  details?: any
}
```

### Git Operation Scenarios

```typescript
/**
 * Get current branch with error handling
 */
export function getCurrentBranch(): string {
  const result = runGitCommand(['rev-parse', '--abbrev-ref', 'HEAD'])
  
  if (!result.success) {
    // Handle different error codes
    switch (result.code) {
      case 'GIT_NOT_FOUND':
        return 'unknown-git-not-installed'
      case 'NOT_GIT_REPO':
        return 'unknown-not-git-repo'
      default:
        return 'unknown-error'
    }
  }
  
  const branch = result.output || 'HEAD'
  
  // Handle detached HEAD
  if (branch === 'HEAD') {
    return 'HEAD-detached'
  }
  
  return branch
}

/**
 * Create git branch with validation
 */
export function createGitBranch(branchName: string): GitResult {
  // Validate branch name
  if (!/^[a-zA-Z0-9\-_]+$/.test(branchName)) {
    return {
      success: false,
      error: `Invalid branch name: ${branchName}`,
      code: 'INVALID_BRANCH_NAME',
    }
  }
  
  // Check if branch already exists
  const checkResult = runGitCommand(['branch', '--list', branchName])
  if (checkResult.success && checkResult.output) {
    return {
      success: false,
      error: `Branch already exists: ${branchName}`,
      code: 'BRANCH_EXISTS',
    }
  }
  
  // Create branch
  return runGitCommand(['checkout', '-b', branchName])
}
```

---

## 4. File System Operations

### Issue (MINOR #9)

Complete the file system operations table.

### Complete Python → Node.js Mapping

| Python Operation | Node.js Operation | Notes |
|------------------|-------------------|-------|
| `os.path.exists(path)` | `fs.existsSync(path)` | Returns boolean |
| `os.path.isfile(path)` | `fs.statSync(path).isFile()` | Throws if path doesn't exist |
| `os.path.isdir(path)` | `fs.statSync(path).isDirectory()` | Throws if path doesn't exist |
| `os.makedirs(path, exist_ok=True)` | `fs.mkdirSync(path, { recursive: true })` | Creates parent dirs |
| `os.mkdir(path)` | `fs.mkdirSync(path)` | Parent must exist |
| `shutil.copy(src, dst)` | `fs.copyFileSync(src, dst)` | Overwrites if exists |
| `Path(path).resolve()` | `path.resolve(path)` | Returns absolute path |
| `pathlib.Path(path).name` | `path.basename(path)` | Returns filename |
| `pathlib.Path(path).parent` | `path.dirname(path)` | Returns directory |
| `os.listdir(path)` | `fs.readdirSync(path)` | Returns array of filenames |
| `os.path.getsize(path)` | `fs.statSync(path).size` | Returns size in bytes |
| `os.path.getmtime(path)` | `fs.statSync(path).mtime` | Returns Date object |
| `os.path.abspath(path)` | `path.resolve(path)` | Returns absolute path |
| `os.path.join(a, b)` | `path.join(a, b)` | Joins path parts |
| `pathlib.Path(path).exists()` | `fs.existsSync(path)` | Returns boolean |

### Safe File Operations

```typescript
/**
 * Safe file read with error handling
 */
export function safeReadFile(filePath: string): string | null {
  try {
    if (!fs.existsSync(filePath)) {
      return null
    }
    return fs.readFileSync(filePath, 'utf-8')
  } catch (error) {
    console.error(`Error reading file ${filePath}:`, error)
    return null
  }
}

/**
 * Safe file write with atomic operation
 */
export function safeWriteFile(filePath: string, content: string): boolean {
  try {
    // Ensure parent directory exists
    const dir = path.dirname(filePath)
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true })
    }
    
    // Write to temp file first
    const tempPath = `${filePath}.tmp.${Date.now()}`
    fs.writeFileSync(tempPath, content, 'utf-8')
    
    // Atomic rename
    fs.renameSync(tempPath, filePath)
    
    return true
  } catch (error) {
    console.error(`Error writing file ${filePath}:`, error)
    return false
  }
}

/**
 * Safe directory listing with glob support
 */
export function safeListDirectory(
  dirPath: string,
  pattern?: string
): string[] {
  try {
    if (!fs.existsSync(dirPath)) {
      return []
    }
    
    const files = fs.readdirSync(dirPath)
    
    if (pattern) {
      const regex = new RegExp(pattern)
      return files.filter(file => regex.test(file))
    }
    
    return files
  } catch (error) {
    console.error(`Error listing directory ${dirPath}:`, error)
    return []
  }
}
```

---

## 5. Zod Schema Best Practices

### Issue (MINOR #10)

Add comprehensive Zod schema documentation.

### When to Use `.optional()` vs `.default()`

```typescript
// .optional() - Parameter can be omitted, returns undefined if not provided
parameters: z.object({
  name: z.string().optional(),  // Can be omitted or must be string
})

// .default() - Parameter can be omitted, returns default value if not provided
parameters: z.object({
  verbose: z.boolean().default(false),  // Defaults to false if not provided
  retries: z.number().default(3),       // Defaults to 3 if not provided
})

// Combining both (rare, but valid)
parameters: z.object({
  value: z.string().optional().default('default'),  // undefined or 'default'
})
```

### Union Types with `.or()`

```typescript
// String or number
parameters: z.object({
  count: z.string().or(z.number()).optional()
    .describe('Can be string "10" or number 10'),
})

// Multiple string options
parameters: z.object({
  format: z.enum(['json', 'text', 'yaml']).optional()
    .describe('Output format: json, text, or yaml'),
})

// Complex union
parameters: z.object({
  input: z.union([
    z.string(),
    z.number(),
    z.boolean(),
    z.array(z.string())
  ]).optional()
})

// Discriminated union (better type safety)
parameters: z.object({
  config: z.discriminatedUnion('type', [
    z.object({
      type: z.literal('local'),
      path: z.string(),
    }),
    z.object({
      type: z.literal('remote'),
      url: z.string(),
    }),
  ])
})
```

### Custom Error Messages

```typescript
// Built-in validation with custom error
parameters: z.object({
  email: z.string().email('Invalid email format'),
  age: z.number().min(18, 'Must be at least 18 years old'),
  username: z.string().min(3, 'Username too short')
                    .max(20, 'Username too long'),
})

// Custom validation with .refine()
parameters: z.object({
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .refine(
      (val) => /[A-Z]/.test(val),
      'Password must contain at least one uppercase letter'
    )
    .refine(
      (val) => /[0-9]/.test(val),
      'Password must contain at least one number'
    ),
})

// Custom error with .transform()
parameters: z.object({
  date: z.string()
    .transform((val) => new Date(val))
    .refine(
      (val) => !isNaN(val.getTime()),
      'Invalid date format'
    ),
})
```

### Array Parameters

```typescript
// Array of strings
parameters: z.object({
  tags: z.array(z.string()).optional()
    .describe('Array of tag strings'),
})

// Array with min/max
parameters: z.object({
  items: z.array(z.string())
    .min(1, 'At least one item required')
    .max(10, 'Maximum 10 items allowed'),
})

// Array of specific values
parameters: z.object({
  priorities: z.array(z.enum(['low', 'medium', 'high']))
    .optional(),
})

// Tuple (fixed length, specific types)
parameters: z.object({
  position: z.tuple([z.number(), z.number()])
    .describe('[x, y] coordinates'),
})
```

### Complete Schema Example

```typescript
parameters: z.object({
  // Required strings
  name: z.string().describe('Feature name (required)'),
  
  // Optional with default
  format: z.enum(['json', 'text']).default('text')
    .describe('Output format (default: text)'),
  
  // Optional boolean
  verbose: z.boolean().optional()
    .describe('Enable verbose output'),
  
  // Union type
  count: z.string().or(z.number()).optional()
    .describe('Count as string or number'),
  
  // Array with validation
  tags: z.array(z.string())
    .min(1, 'At least one tag required')
    .max(5, 'Maximum 5 tags')
    .optional()
    .describe('Feature tags (1-5 tags)'),
  
  // Custom validation
  branch: z.string()
    .min(3, 'Branch name too short')
    .refine(
      (val) => /^[a-z0-9-]+$/.test(val),
      'Branch name must be lowercase with hyphens only'
    )
    .describe('Branch name (lowercase, hyphens allowed)'),
  
  // Nested object
  config: z.object({
    enabled: z.boolean().default(true),
    retries: z.number().default(3),
  }).optional().describe('Optional configuration object'),
})
```

---

## Summary Checklist

Each tool implementation should:

- [ ] Use context parameter for mode-specific behavior when relevant
- [ ] Implement environment variable fallbacks
- [ ] Handle all git error scenarios (not installed, not repo, permissions, etc.)
- [ ] Use safe file operations with error handling
- [ ] Add `.describe()` to all Zod parameters
- [ ] Use `.optional()` for truly optional parameters
- [ ] Use `.default()` for parameters with sensible defaults
- [ ] Validate user input with `.refine()` when needed

---

**Related Documents:**
- [01-critical-decisions.md](./01-critical-decisions.md) - Critical decisions
- [02-code-standards.md](./02-code-standards.md) - Code standards
- [03-complete-example.md](./03-complete-example.md) - Complete tool example
- [05-testing-strategy.md](./05-testing-strategy.md) - Testing approach
