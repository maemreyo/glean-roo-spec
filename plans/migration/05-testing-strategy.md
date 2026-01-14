# Testing Strategy for Roo Custom Tools

**Document:** 05-testing-strategy.md  
**Status:** DRAFT  
**Last Updated:** 2025-01-14

## Overview

This document defines the testing strategy for Roo Custom Tools, including test framework specification, mocking strategies, test structure, and rollback procedures.

---

## 1. Test Framework Specification

### Issue (MINOR #11)

Need to specify test framework and provide examples.

### Recommended Stack

| Component | Recommendation | Version |
|-----------|---------------|---------|
| Test Runner | **Jest** | 29.x+ |
| Type Checking | TypeScript | 5.3+ |
| Mocking | `jest.mock()` | Built-in |
| Coverage | `istanbul` (via Jest) | Built-in |

### Why Jest?

- **Built-in mocking**: Excellent support for mocking Node.js modules
- **TypeScript support**: Works seamlessly with `ts-jest`
- **Snapshot testing**: Useful for output consistency validation
- **Wide adoption**: Familiar to most TypeScript developers
- **CI/CD integration**: Easy to set up in GitHub Actions

---

## 2. Project Setup for Testing

### Package.json Scripts

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --maxWorkers=2"
  }
}
```

### Jest Configuration

```javascript
// jest.config.js
export default {
  preset: 'ts-jest/presets/default-esm',
  testEnvironment: 'node',
  extensionsToTreatAsEsm: ['.ts'],
  moduleNameMapper: {
    '^(\\.{1,2}/.*)\\.js$': '$1',
  },
  transform: {
    '^.+\\.tsx?$': [
      'ts-jest',
      {
        useESM: true,
      },
    ],
  },
  testMatch: [
    '**/tests/tools/**/*.test.ts',
    '**/tests/lib/**/*.test.ts',
  ],
  collectCoverageFrom: [
    '.roo/tools/**/*.ts',
    '.roo/tools/lib/**/*.ts',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
}
```

---

## 3. Mocking Strategies

### Mocking File System (`fs`)

```typescript
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals'
import fs from 'fs'

// Mock fs module
jest.mock('fs', () => ({
  existsSync: jest.fn(),
  readFileSync: jest.fn(),
  writeFileSync: jest.fn(),
  mkdirSync: jest.fn(),
  readdirSync: jest.fn(),
  statSync: jest.fn(),
}))

describe('setup_plan tool', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks()
  })

  it('should create plan when feature dir exists', async () => {
    // Mock file system responses
    ;(fs.existsSync as jest.Mock).mockImplementation((path: string) => {
      if (path.includes('specs/999-test')) return true
      if (path.includes('.zo/templates')) return true
      return false
    })

    ;(fs.readFileSync as jest.Mock).mockReturnValue('# Template Content')
    
    // Import and test tool
    const setupPlan = await import('../../.roo/tools/setup-plan.js')
    const result = await setupPlan.default.execute({ json: true }, {})
    const parsed = JSON.parse(result)

    expect(parsed.created).toBe(true)
    expect(fs.writeFileSync).toHaveBeenCalled()
  })
})
```

### Mocking Child Process (`git` commands)

```typescript
import { execSync } from 'child_process'

jest.mock('child_process', () => ({
  execSync: jest.fn(),
}))

describe('git operations', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should get current branch', () => {
    ;(execSync as jest.Mock).mockReturnValue('001-feature-branch\n')

    const branch = getCurrentBranch()

    expect(branch).toBe('001-feature-branch')
    expect(execSync).toHaveBeenCalledWith(
      'git rev-parse --abbrev-ref HEAD',
      expect.any(Object)
    )
  })

  it('should handle git not installed', () => {
    ;(execSync as jest.Mock).mockImplementation(() => {
      throw new Error('git: command not found')
    })

    const result = runGitCommand(['status'])

    expect(result.success).toBe(false)
    expect(result.code).toBe('GIT_NOT_FOUND')
  })
})
```

### Mocking Path Module

```typescript
import path from 'path'

jest.mock('path', () => ({
  join: jest.fn(),
  resolve: jest.fn(),
  basename: jest.fn(),
  dirname: jest.fn(),
}))

describe('path utilities', () => {
  it('should resolve paths correctly', () => {
    ;(path.join as jest.Mock).mockImplementation((...args: string[]) => {
      return args.join('/')
    })

    const result = path.join('a', 'b', 'c')
    expect(result).toBe('a/b/c')
  })
})
```

---

## 4. Test Structure

### Basic Test Template

```typescript
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals'

describe('Tool Name', () => {
  // Setup: Create test fixtures
  beforeEach(() => {
    // Initialize test data
    // Mock external dependencies
  })

  // Teardown: Clean up
  afterEach(() => {
    // Remove test files
    // Clear mocks
  })

  // Test cases
  describe('success scenarios', () => {
    it('should perform operation correctly', async () => {
      // Arrange
      const input = { /* test data */ }

      // Act
      const result = await tool.execute(input, {})

      // Assert
      expect(result).toBeDefined()
      // More assertions...
    })
  })

  describe('error scenarios', () => {
    it('should handle missing input', async () => {
      // Test error handling
    })

    it('should handle file not found', async () => {
      // Test error handling
    })
  })

  describe('edge cases', () => {
    it('should handle empty input', async () => {
      // Test edge case
    })

    it('should handle special characters', async () => {
      // Test edge case
    })
  })
})
```

### Complete Example

```typescript
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals'
import fs from 'fs'
import path from 'path'
import { execSync } from 'child_process'

jest.mock('fs')
jest.mock('path')
jest.mock('child_process')

import { getFeaturePaths } from '../../.roo/tools/lib/util.js'

describe('getFeaturePaths', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('when in git repository', () => {
    beforeEach(() => {
      // Mock git commands
      ;(execSync as jest.Mock).mockImplementation((cmd: string) => {
        if (cmd.includes('rev-parse --git-dir')) return '.git'
        if (cmd.includes('rev-parse --show-toplevel')) return '/repo/root'
        if (cmd.includes('rev-parse --abbrev-ref HEAD')) return '001-test-feature'
        return ''
      })

      // Mock path functions
      ;(path.join as jest.Mock).mockImplementation((...args: string[]) => {
        return args.filter(Boolean).join('/')
      })

      ;(path.resolve as jest.Mock).mockImplementation((p: string) => p)
    })

    it('should return all feature paths', () => {
      ;(fs.existsSync as jest.Mock).mockReturnValue(true)

      const paths = getFeaturePaths()

      expect(paths).toMatchObject({
        REPO_ROOT: '/repo/root',
        CURRENT_BRANCH: '001-test-feature',
        HAS_GIT: 'true',
      })
    })

    it('should detect feature directory', () => {
      ;(fs.existsSync as jest.Mock)
        .mockImplementation((p: string) => p.includes('specs/001'))

      const paths = getFeaturePaths()

      expect(paths.FEATURE_DIR).toContain('specs/001')
    })
  })

  describe('when not in git repository', () => {
    it('should use current working directory', () => {
      ;(execSync as jest.Mock).mockImplementation(() => {
        throw new Error('Not a git repository')
      })

      const paths = getFeaturePaths()

      expect(paths.HAS_GIT).toBe('false')
      expect(paths.CURRENT_BRANCH).toBe('unknown')
    })
  })
})
```

---

## 5. Testing Tools That Require Git Repositories

### Setup Test Git Repository

```typescript
import { execSync } from 'child_process'
import fs from 'fs'
import path from 'path'
import { tmpdir } from 'os'

describe('Git-based tools', () => {
  let testRepoPath: string

  beforeEach(() => {
    // Create temporary directory
    testRepoPath = path.join(tmpdir(), `test-repo-${Date.now()}`)
    fs.mkdirSync(testRepoPath, { recursive: true })

    // Initialize git repository
    execSync('git init', { cwd: testRepoPath, stdio: 'pipe' })
    execSync('git config user.email "test@example.com"', { cwd: testRepoPath })
    execSync('git config user.name "Test User"', { cwd: testRepoPath })

    // Create initial commit
    fs.writeFileSync(path.join(testRepoPath, 'README.md'), '# Test')
    execSync('git add .', { cwd: testRepoPath })
    execSync('git commit -m "Initial commit"', { cwd: testRepoPath })

    // Create feature branch
    execSync('git checkout -b 001-test-feature', { cwd: testRepoPath })
  })

  afterEach(() => {
    // Clean up test repository
    if (fs.existsSync(testRepoPath)) {
      fs.rmSync(testRepoPath, { recursive: true, force: true })
    }
  })

  it('should create feature branch', async () => {
    // Test in actual git repository
    const result = await createFeature({
      description: 'test feature',
      number: '002',
    })

    expect(result).toContain('Branch created: 002-test-feature')
  })
})
```

---

## 6. Snapshot Testing

### Snapshot Test Template

```typescript
import {toMatchSnapshot} from '@jest/globals'

describe('Tool output snapshots', () => {
  it('should match expected output format', async () => {
    const result = await tool.execute(
      { param1: 'value1' },
      { mode: 'code' }
    )

    // Snapshot for text output
    expect(result).toMatchSnapshot()
  })

  it('should match JSON output snapshot', async () => {
    const result = await tool.execute(
      { json: true, param1: 'value1' },
      {}
    )

    const parsed = JSON.parse(result)
    expect(parsed).toMatchSnapshot()
  })
})
```

### Update Snapshots

```bash
# Update snapshots after intentional changes
npm test -- -u

# Review snapshot changes interactively
npm test -- --watch
```

---

## 7. Rollback Strategy

### Issue (MINOR #12)

How to revert to Python scripts if migration fails.

### Rollback Procedures

#### Phase 1: Parallel Operation (Transition Period)

```markdown
## Migration Status

| Tool | Python | TypeScript | Status |
|------|--------|------------|--------|
| check-prerequisites | ✅ | ✅ | Both available |
| setup-plan | ✅ | ✅ | Both available |
| create-feature | ✅ | 🚧 | Testing |

**Legend:**
- ✅ = Available and working
- 🚧 = In development/testing
- ❌ = Not working
```

#### Rollback Decision Matrix

| Scenario | Action | Procedure |
|----------|--------|-----------|
| **Critical Bug** | Immediate rollback | Delete `.roo/tools/*.ts`, use Python |
| **Performance Issue** | Temporary rollback | Comment out TypeScript tool in `.roo/tools/` |
| **Missing Feature** | Use Python fallback | Document in tool description |
| **Successful Migration** | Deprecate Python | Add deprecation notice |

#### Rollback Script

```typescript
// .roo/tools/scripts/rollback.ts
import fs from 'fs'
import path from 'path'

interface RollbackConfig {
  toolsToRollback: string[]
  backupDir: string
}

export function rollbackToPython(config: RollbackConfig): void {
  const { toolsToRollback, backupDir } = config

  for (const tool of toolsToRollback) {
    const toolPath = path.join('.roo/tools', `${tool}.ts`)
    const backupPath = path.join(backupDir, `${tool}.ts.bak`)

    // Backup TypeScript tool
    if (fs.existsSync(toolPath)) {
      fs.copyFileSync(toolPath, backupPath)
      fs.unlinkSync(toolPath)
      console.log(`Rolled back ${tool}: TypeScript tool removed`)
    }
  }

  console.log('Rollback complete. Python scripts will be used.')
}
```

#### Avoiding Partial Migration State

```typescript
// Migration validation script
export function validateMigration(): {
  canProceed: boolean
  issues: string[]
} {
  const issues: string[] = []

  // Check all required tools exist
  const requiredTools = [
    'check-prerequisites',
    'setup-plan',
    'setup-design',
  ]

  for (const tool of requiredTools) {
    const toolPath = path.join('.roo/tools', `${tool}.ts`)
    if (!fs.existsSync(toolPath)) {
      issues.push(`Missing tool: ${tool}`)
    }
  }

  // Check lib utilities exist
  const requiredLibs = ['util.ts', 'git-utils.ts']
  for (const lib of requiredLibs) {
    const libPath = path.join('.roo/tools/lib', lib)
    if (!fs.existsSync(libPath)) {
      issues.push(`Missing library: ${lib}`)
    }
  }

  return {
    canProceed: issues.length === 0,
    issues,
  }
}
```

### Rollback Testing

```typescript
describe('Rollback procedures', () => {
  it('should successfully rollback to Python', () => {
    const result = rollbackToPython({
      toolsToRollback: ['setup-plan'],
      backupDir: '.roo/tools/backup',
    })

    expect(fs.existsSync('.roo/tools/setup-plan.ts')).toBe(false)
    expect(fs.existsSync('.roo/tools/backup/setup-plan.ts.bak')).toBe(true)
  })

  it('should validate migration state', () => {
    const validation = validateMigration()

    if (!validation.canProceed) {
      console.error('Migration issues:', validation.issues)
    }

    expect(validation.canProceed).toBe(true)
  })
})
```

---

## 8. Coverage Requirements

### Minimum Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Lines | 80% | Core logic well-tested |
| Branches | 75% | Error paths covered |
| Functions | 85% | All functions exercised |
| Statements | 80% | Overall coverage |

### Coverage Exclusions

```javascript
// jest.config.js
collectCoverageFrom: [
  '.roo/tools/**/*.ts',
  '.roo/tools/lib/**/*.ts',
  '!**/*.d.ts',
  '!**/node_modules/**',
  '!**/tests/**',           // Exclude test files
  '!**/dist/**',            // Exclude build output
  '!**/index.ts',           // Exclude barrel exports
],
```

---

## Summary Checklist

- [ ] Jest configured with TypeScript support
- [ ] Mock utilities created for `fs`, `child_process`, `path`
- [ ] Test fixtures for git repositories
- [ ] Snapshot tests for output validation
- [ ] Coverage targets defined
- [ ] Rollback procedures documented
- [ ] Migration validation script created

---

**Related Documents:**
- [03-complete-example.md](./03-complete-example.md) - Complete tool with tests
- [04-implementation-guide.md](./04-implementation-guide.md) - Implementation details
- [06-requirements.md](./06-requirements.md) - Version and performance requirements
