import { parametersSchema as z, defineCustomTool } from "@roo-code/types";
import { execSync } from "child_process";
import * as fs from "fs";
import * as path from "path";

export default defineCustomTool({
  name: "git_branch_detector",
  description: "Detect the highest feature branch number from git branches and spec directories",
  parameters: z.object({
    specsDir: z.string().describe("Path to specs directory"),
    hasGit: z.boolean().describe("Whether git repository is available"),
  }),
  async execute({ specsDir, hasGit }) {
    try {
      let numbers: number[] = [];

      // Check git branches if available
      if (hasGit) {
        try {
          // Fetch latest branches
          execSync("git fetch --all --prune", { stdio: "ignore" });

          // Get remote branches matching pattern [0-9]{3}-
          const remoteBranches = execSync(
            'git ls-remote --heads origin | grep -E "refs/heads/[0-9]{3}-" | sed "s/.*refs\\/heads\\/\\([0-9]\\{3\\}\\)-.*/\\1/"',
            { encoding: "utf-8" }
          ).trim().split('\n').filter(n => n);

          // Get local branches matching pattern [0-9]{3}-
          const localBranches = execSync(
            'git branch | grep -E "^[* ]*[0-9]{3}-" | sed "s/.*[0-9]\\{3\\}-.*/\\1/"',
            { encoding: "utf-8" }
          ).trim().split('\n').filter(n => n);

          numbers.push(...remoteBranches.map(n => parseInt(n, 10)));
          numbers.push(...localBranches.map(n => parseInt(n, 10)));
        } catch (error) {
          // Git commands might fail, continue with directory check
        }
      }

      // Check spec directories
      if (fs.existsSync(specsDir)) {
        const dirs = fs.readdirSync(specsDir, { withFileTypes: true })
          .filter(dirent => dirent.isDirectory())
          .map(dirent => dirent.name)
          .filter(name => /^\d{3}-/.test(name))
          .map(name => parseInt(name.substring(0, 3), 10));

        numbers.push(...dirs);
      }

      // Find highest number
      const highestNumber = numbers.length > 0 ? Math.max(...numbers) : 0;
      const nextNumber = highestNumber + 1;

      return JSON.stringify({
        highestNumber,
        nextNumber,
        sources: {
          git: hasGit,
          specsDir: specsDir,
          foundNumbers: numbers
        }
      });
    } catch (error) {
      return `Error detecting branch numbers: ${error instanceof Error ? error.message : String(error)}`;
    }
  }
});