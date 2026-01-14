# Roo Custom Tools

Custom tools for Roo AI - migrated from Python scripts to TypeScript.

## Overview

This package contains 9 custom tools for Roo AI that have been migrated from Python scripts to TypeScript. These tools support the Spec-Driven Development (SDD) workflow for feature development in the Roo ecosystem.

## Migration Status

| Tool | Python | TypeScript | Status |
|------|--------|------------|--------|
| [`check-prerequisites`](#check-prerequisites) | ✅ | ✅ | Complete |
| [`setup-plan`](#setup-plan) | ✅ | ✅ | Complete |
| [`setup-design`](#setup-design) | ✅ | ✅ | Complete |
| [`setup-brainstorm`](#setup-brainstorm) | ✅ | ✅ | Complete |
| [`setup-brainstorm-crazy`](#setup-brainstorm-crazy) | ✅ | ✅ | Complete |
| [`setup-roast`](#setup-roast) | ✅ | ✅ | Complete |
| [`setup-roast-verify`](#setup-roast-verify) | ✅ | ✅ | Complete |
| [`setup-specify-idea`](#setup-specify-idea) | ✅ | ✅ | Complete |
| [`create-feature`](#create-feature) | ✅ | ✅ | Complete |

## Installation

```bash
# From the project root
cd .roo/tools
npm install
```

## Requirements

- **Node.js**: >= 18.0.0
- **TypeScript**: >= 5.3.0
- **npm**: >= 9.0.0
- **Git**: >= 2.30.0 (for git-based operations)

## Available Scripts

```bash
# Build TypeScript to JavaScript
npm run build

# Watch mode for development
npm run watch

# Type checking without emitting
npm run typecheck

# Run tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage report
npm run test:coverage

# Run tests in CI mode
npm run test:ci

# Clean build output
npm run clean
```

## Tools Reference

### check-prerequisites

Validates feature prerequisites and available documentation files.

**Usage:**
```typescript
// Check if current feature has required documentation
await check_prerequisites({ json: false })

// Get JSON output
await check_prerequisites({ json: true })

// Require tasks.md to exist
await check_prerequisites({ json: true, requireTasks: true })

// Include tasks.md in available docs
await check_prerequisites({ json: true, includeTasks: true })

// Only output path variables
await check_prerequisites({ pathsOnly: true })
```

**Parameters:**
- `json` - Output in JSON format (default: `false`)
- `requireTasks` - Require tasks.md to exist (default: `false`)
- `includeTasks` - Include tasks.md in AVAILABLE_DOCS list (default: `false`)
- `pathsOnly` - Only output path variables (default: `false`)

**Example Output:**
```json
{
  "FEATURE_DIR": "specs/001-test-feature",
  "AVAILABLE_DOCS": ["research.md", "contracts/"],
  "HAS_TASKS": true,
  "VALID": true
}
```

### setup-plan

Creates implementation plan (plan.md) from template.

**Usage:**
```typescript
// Create plan from template
await setup_plan({ json: false })

// Get JSON output
await setup_plan({ json: true })
```

### setup-design

Creates design document (design.md) from template.

**Usage:**
```typescript
// Create design document
await setup_design({ json: false })

// Get JSON output
await setup_design({ json: true })
```

### setup-brainstorm

Creates brainstorming document (brainstorm.md) from template.

**Usage:**
```typescript
// Create brainstorming document
await setup_brainstorm({ json: false })

// Get JSON output
await setup_brainstorm({ json: true })
```

### setup-brainstorm-crazy

Creates "crazy ideas" brainstorming document.

**Usage:**
```typescript
// Create crazy ideas brainstorm
await setup_brainstorm_crazy({ json: false })

// Get JSON output
await setup_brainstorm_crazy({ json: true })
```

### setup-roast

Creates roast document for feature review.

**Usage:**
```typescript
// Create roast document
await setup_roast({ json: false })

// Get JSON output
await setup_roast({ json: true })
```

### setup-roast-verify

Creates verification document for roast review.

**Usage:**
```typescript
// Create roast verification document
await setup_roast_verify({ json: false })

// Get JSON output
await setup_roast_verify({ json: true })
```

### setup-specify-idea

Creates specification document for an idea.

**Usage:**
```typescript
// Create specification from idea
await setup_specify_idea({ json: false })

// Get JSON output
await setup_specify_idea({ json: true })
```

### create-feature

Creates a new feature from an idea description.

**Usage:**
```typescript
// Create feature from description
await create_feature({ 
  description: "Add user authentication",
  number: "001"
})

// Get JSON output
await create_feature({ 
  description: "Add user authentication",
  number: "001",
  json: true
})
```

**Parameters:**
- `description` - Feature description (required)
- `number` - Feature number (default: auto-generated)
- `json` - Output in JSON format (default: `false`)

## Shared Utilities

The tools use shared utilities from the `lib/` directory:

### lib/util.ts

Core utilities for path resolution, git operations, and file system operations.

**Key Functions:**
- `getFeaturePaths()` - Get feature directory paths
- `validateExecutionEnvironment()` - Validate runtime environment
- `checkFeatureBranch()` - Validate current branch
- `resolvePath()` - Resolve file paths
- `checkFileExists()` - Check if file exists
- `checkDirExistsWithFiles()` - Check if directory has files

### lib/feature-utils.ts

Feature-specific utilities for managing feature specifications.

**Key Functions:**
- `getNextFeatureNumber()` - Get next feature number
- `createFeatureBranch()` - Create feature branch
- `updateAgentContext()` - Update agent context files

## Development

### Project Structure

```
.roo/tools/
├── check-prerequisites.ts       # Check prerequisites tool
├── setup-plan.ts                # Setup plan tool
├── setup-design.ts              # Setup design tool
├── setup-brainstorm.ts          # Setup brainstorm tool
├── setup-brainstorm-crazy.ts    # Setup crazy brainstorm tool
├── setup-roast.ts               # Setup roast tool
├── setup-roast-verify.ts        # Setup roast verify tool
├── setup-specify-idea.ts        # Setup specify idea tool
├── create-feature.ts            # Create feature tool
├── lib/
│   ├── util.ts                  # Core utilities
│   ├── feature-utils.ts         # Feature utilities
│   └── index.ts                 # Barrel exports
├── tests/
│   └── tools/
│       └── check-prerequisites.test.ts  # Example test
├── jest.config.js               # Jest configuration
├── tsconfig.json                # TypeScript configuration
├── package.json                 # Package configuration
└── README.md                    # This file
```

### Testing

Tests are written using Jest with TypeScript support. See [`tests/tools/check-prerequisites.test.ts`](tests/tools/check-prerequisites.test.ts) for an example test file.

**Key Testing Patterns:**
- Mock file system operations with `jest.mock('node:fs')`
- Mock utility functions with `jest.mock('../lib/util.js')`
- Test success scenarios, error scenarios, and edge cases
- Use descriptive test names following the pattern "should [do something]"

### Adding New Tests

To add tests for a new tool:

1. Create a test file: `tests/tools/<tool-name>.test.ts`
2. Follow the template in [`check-prerequisites.test.ts`](tests/tools/check-prerequisites.test.ts)
3. Run tests: `npm test`

## Migration Documentation

See [`MIGRATION.md`](MIGRATION.md) for detailed information about:
- Migration approach and decisions
- Key differences between Python and TypeScript
- Known issues and limitations
- Future improvements

## API Reference

See [`API.md`](API.md) for detailed API documentation including:
- Complete tool reference
- Parameter specifications
- Return value documentation
- Usage patterns and best practices

## Contributing

When adding new tools or modifying existing ones:

1. Follow the existing code style (TypeScript strict mode)
2. Add JSDoc comments for all public functions
3. Write comprehensive tests
4. Update documentation (README.md, API.md)
5. Run `npm run typecheck` and `npm test` before committing

## License

Part of the Roo AI project. See project root for license information.

## Related Documentation

- [Migration Plan](../../plans/migration/)
- [Testing Strategy](../../plans/migration/05-testing-strategy.md)
- [Requirements](../../plans/migration/06-requirements.md)
- [Code Standards](../../plans/migration/02-code-standards.md)
