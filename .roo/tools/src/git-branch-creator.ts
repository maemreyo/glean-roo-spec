import { parametersSchema as z, defineCustomTool } from "@roo-code/types";
import { execSync } from "child_process";
import * as path from "path";

export default defineCustomTool({
  name: "git_branch_creator",
  description: "Create and checkout a new git branch",
  parameters: z.object({
    branchName: z.string().describe("Name of the branch to create"),
    repoRoot: z.string().describe("Repository root directory"),
  }),
  async execute({ branchName, repoRoot }) {
    try {
      // Validate branch name format
      if (!/^\d{3}-/.test(branchName)) {
        return `Error: Branch name must follow format XXX-name (got: ${branchName})`;
      }

      // Check if branch already exists
      try {
        execSync(`git show-ref --verify --quiet refs/heads/${branchName}`, { cwd: repoRoot });
        return `Error: Branch '${branchName}' already exists`;
      } catch {
        // Branch doesn't exist, good to create
      }

      // Create and checkout branch
      execSync(`git checkout -b ${branchName}`, {
        cwd: repoRoot,
        stdio: "pipe"
      });

      return JSON.stringify({
        success: true,
        branchName,
        message: `Branch '${branchName}' created and checked out successfully`
      });
    } catch (error) {
      return `Error creating branch: ${error instanceof Error ? error.message : String(error)}`;
    }
  }
});