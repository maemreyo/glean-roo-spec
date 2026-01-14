# Critical Decisions for Python to Roo Tools Migration

**Document:** 01-critical-decisions.md  
**Status:** DRAFT  
**Last Updated:** 2025-01-14

## Overview

This document captures critical architectural and security decisions that must be made **before** implementation begins. These decisions address technical review issues that could significantly impact the migration's success.

---

## Decision 1: Shared Utility Import Strategy

### Issue (CRITICAL #2)

Roo Custom Tools are auto-discovered. If `.roo/tools/shared/` contains `.ts` files, they must either:
- Export `default` with `defineCustomTool()` (won't work for utilities)
- OR be in a location Roo doesn't scan

### Decision

**Use `.roo/tools/lib/` for shared utilities** (not `.roo/tools/shared/`)

### Rationale

1. **Explicit Separation**: `lib/` clearly indicates internal utilities, not tool definitions
2. **Avoids Discovery Issues**: Files outside scan path won't cause auto-discovery problems
3. **Future-Proof**: Structural separation works even if Roo's scanning behavior changes
4. **Organizational Clarity**: Self-documenting structure for contributors

### Implementation

```
.roo/tools/
├── lib/                    # Shared utilities (NOT auto-discovered)
│   ├── util.ts            # Common utilities from common.py
│   ├── feature-utils.ts   # Feature utilities from feature_utils.py
│   ├── git-utils.ts       # Git operations
│   └── types.ts           # TypeScript types
├── check-prerequisites.ts  # Tool definitions (auto-discovered)
├── create-feature.ts
└── package.json
```

### Import Pattern

```typescript
// In tool files (e.g., check-prerequisites.ts)
import { resolvePath, getFeaturePaths } from '../lib/util.js'
import { generateBranchName } from '../lib/feature-utils.js'
```

**Important**: Use `.js` extension in imports (ESM requirement) even though source files are `.ts`.

### Verification Checklist

- [ ] Confirm `.roo/tools/lib/` is outside Roo's auto-discovery scan path
- [ ] Test that utility files in `lib/` are NOT registered as tools
- [ ] Verify imports work correctly with `.js` extension
- [ ] Document this pattern in project README

---

## Decision 2: Template File Management

### Issue (CRITICAL #3)

Tools depend on `.zo/templates/*.md` files but plan lacks:
- Template existence validation before tool execution
- Clear error messages when templates are missing
- Consideration for bundling critical templates

### Decision

**Hybrid approach: Validate + optional bundling**

### Strategy

#### 1. Template Existence Validation

Every tool that uses templates MUST validate before execution:

```typescript
// In lib/util.ts
export function validateTemplatePath(templatePath: string, toolName: string): void {
  if (!fs.existsSync(templatePath)) {
    throw new Error(
      `Template file not found for ${toolName}: ${templatePath}\n` +
      `Expected location: ${templatePath}\n` +
      `Ensure .zo/templates/ directory exists and contains required templates.`
    )
  }
}

// Usage in tools
export default defineCustomTool({
  name: 'setup_plan',
  async execute({ featureDir }) {
    const templatePath = path.join(
      getRepoRoot(), 
      '.zo', 
      'templates', 
      'plan-template.md'
    )
    
    validateTemplatePath(templatePath, 'setup-plan')
    // Continue with tool logic...
  }
})
```

#### 2. Standardized Error Messages

All template errors should include:
- Template path that was searched
- Tool name that requires it
- Suggested fix (e.g., "Run setup command" or "Copy from template")

#### 3. Optional Template Bundling (Phase 2)

Consider bundling critical templates as constants for:
- Tools used in CI/CD (no human intervention possible)
- Offline scenarios
- Backup when templates are deleted

```typescript
// In lib/templates.ts (optional, Phase 2)
export const DEFAULT_TEMPLATES = {
  PLAN_TEMPLATE: `# Implementation Plan

## Overview
...

## Tasks
- [ ] Task 1
`,
  // Add other critical templates
}

export function getTemplateContent(templatePath: string): string {
  if (fs.existsSync(templatePath)) {
    return fs.readFileSync(templatePath, 'utf-8')
  }
  
  // Fallback to bundled template
  const basename = path.basename(templatePath)
  const fallback = DEFAULT_TEMPLATES[basename.toUpperCase()]
  
  if (fallback) {
    return fallback
  }
  
  throw new Error(`Template not found: ${templatePath}`)
}
```

### Required Templates List

Document which templates each tool requires:

| Tool | Template File | Optional? |
|------|---------------|-----------|
| `setup-plan` | `.zo/templates/plan-template.md` | No |
| `setup-design` | `.zo/templates/design-template.md` | No |
| `setup-design` | `.zo/templates/design-system-template.md` | No |
| `setup-brainstorm` | `.zo/templates/brainstorm-template.md` | No |
| `setup-brainstorm-crazy` | `.zo/templates/brainstorm-template-crazy.md` | No |
| `setup-roast` | `.zo/templates/roast-template.md` | No |
| `create-feature` | `.zo/templates/spec-from-idea.md` | No |
| `create-feature` | `.zo/templates/spec-template.md` | No |

---

## Decision 3: Auto-Approval Security Policy

### Issue (CRITICAL #4)

Security implications of auto-approval behavior are insufficiently stressed. Tools that:
- Delete files
- Execute shell commands
- Modify git state

Require mandatory security review.

### Decision

**Implement mandatory Security Review for all tools before enabling auto-approval**

### Security Review Checklist

Every tool MUST pass this review BEFORE being used with auto-approval:

```markdown
## Security Review for [TOOL_NAME]

### Tool Capabilities
- [ ] Deletes files
- [ ] Executes shell commands
- [ ] Modifies git state
- [ ] Writes to filesystem
- [ ] Reads sensitive data

### Risk Assessment
- **What can go wrong?** [Describe worst case]
- **Who is affected?** [User data, repo state, etc.]
- **Can damage be undone?** [Yes/No and how]

### Mitigations in Place
- [ ] Input validation (Zod schema)
- [ ] Path traversal protection
- [ ] Command injection protection
- [ ] Confirmation prompts for destructive operations
- [ ] Rollback capability

### Auto-Approval Decision
- [ ] APPROVED for auto-approval
- [ ] DENIED - requires explicit user confirmation
- [ ] CONDITIONAL - approved only with safeguards

### Reviewer Approval
- Reviewed by: _____________ Date: _______
- Approved by: _____________ Date: _______
```

### High-Risk Tools (Require Extra Scrutiny)

| Tool | Risk Level | Why | Auto-Approval |
|------|------------|-----|---------------|
| `create-feature` | HIGH | Creates git branches, writes files | CONDITIONAL |
| `setup-roast` | MEDIUM | Writes to feature directories | YES |
| `check-prerequisites` | LOW | Read-only operations | YES |
| `setup-plan` | MEDIUM | Writes plan.md files | YES |

### Warnings to Add

Add prominent warnings to tool descriptions:

```typescript
export default defineCustomTool({
  name: 'create_feature',
  description: `
    Create a new feature branch and spec file.
    
    WARNING: This tool will:
    - Create a new git branch
    - Write files to your filesystem
    - Modify .git directory
    
    Only use with auto-approval if you trust the AI's branch name suggestions.
    Review the generated branch name before execution.
  `,
  // ...
})
```

### Implementation Requirements

1. **Phase 1**: All tools require explicit confirmation
2. **Phase 2**: Low-risk tools can use auto-approval
3. **Phase 3**: High-risk tools with proper safeguards can use auto-approval

---

## Summary of Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Shared utilities location | `.roo/tools/lib/` | Avoids auto-discovery issues |
| Template management | Validate + optional bundling | Clear errors + fallback safety |
| Auto-approval policy | Mandatory security review | Prevents accidental damage |

---

## Next Steps

1. **Verify** `.roo/tools/lib/` is outside Roo's scan path
2. **Create** security review template
3. **Document** required templates for each tool
4. **Implement** template validation in `lib/util.ts`
5. **Review** each tool against security checklist

---

**Related Documents:**
- [02-code-standards.md](./02-code-standards.md) - Parameter patterns and naming
- [03-complete-example.md](./03-complete-example.md) - Working tool example
- [04-implementation-guide.md](./04-implementation-guide.md) - Detailed implementation
