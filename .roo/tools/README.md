# Roo Custom Tools

This directory contains TypeScript-based custom tools for Roo Code that replace Python/bash scripts in the `zo.specify` command workflow.

## Available Tools

### Git Management
- **`git_branch_detector`**: Detects highest branch numbers from git remotes, local branches, and spec directories
- **`git_branch_creator`**: Creates and checks out new git branches with validation

### Feature Creation
- **`branch_name_generator`**: Generates short branch names from feature descriptions using NLP filtering
- **`spec_content_generator`**: Generates basic specification content from templates and descriptions

### File System Operations
- **`filesystem_directory_creator`**: Creates directories and ensures parent directories exist
- **`filesystem_template_copier`**: Copies templates and fills placeholders

## Tool Architecture

Each tool follows this pattern:
```typescript
import { parametersSchema as z, defineCustomTool } from "@roo-code/types";

export default defineCustomTool({
  name: "tool_name",
  description: "What the tool does",
  parameters: z.object({
    param: z.string().describe("Parameter description")
  }),
  async execute({ param }) {
    // Implementation
    return "Result";
  }
});
```

## Building Tools

```bash
cd .roo/tools
npm install
npx tsc
```

Compiled tools are available in the `dist/` directory.

## Usage

Tools are automatically loaded by Roo Code when:
1. **Enable custom tools** is turned on in Settings → Experimental
2. **Restart VS Code** after enabling

Tools can then be invoked by name in command workflows.

## Development

### Adding New Tools
1. Create `src/new-tool.ts` following the pattern above
2. Add to `tsconfig.json` includes if needed
3. Compile with `npx tsc`
4. Restart VS Code to reload tools

### Error Handling
All tools include comprehensive error handling and return descriptive error messages.

### Type Safety
Tools use Zod schemas for parameter validation and TypeScript for type safety.

## Migration from Python Scripts

This toolset replaces the following Python workflow:
- `create-new-feature.py` → Multiple specialized TypeScript tools
- Bash git operations → `git_branch_detector` and `git_branch_creator`
- File operations → `filesystem_*` tools
- Template processing → `spec_content_generator` and `filesystem_template_copier`

## Benefits

- **Unified Language**: All tools in TypeScript
- **Type Safety**: Compile-time error checking
- **Better Integration**: Context-aware, auto-approved execution
- **Easier Maintenance**: Single language, consistent patterns
- **Enhanced Testing**: Jest integration support