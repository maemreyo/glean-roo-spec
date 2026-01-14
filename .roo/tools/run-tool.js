#!/usr/bin/env node

/**
 * Helper script to run Roo Tools directly with TypeScript
 * Usage: node run-tool.js <tool-file> [json-args]
 *
 * Examples:
 * node run-tool.js src/git-branch-detector.ts '{"specsDir":"specs","hasGit":true}'
 * node run-tool.js src/branch-name-generator.ts '{"featureDescription":"Add user auth"}'
 */

const { execSync } = require('child_process');
const path = require('path');

const [,, toolFile, argsJson] = process.argv;

if (!toolFile) {
  console.error('Usage: node run-tool.js <tool-file> [json-args]');
  console.error('Example: node run-tool.js src/git-branch-detector.ts \'{"specsDir":"specs","hasGit":true}\'');
  process.exit(1);
}

const toolPath = path.resolve(toolFile);

try {
  // Parse args if provided
  let args = {};
  if (argsJson) {
    args = JSON.parse(argsJson);
  }

  // Run with ts-node
  const argsStr = JSON.stringify(args);
  const command = `npx ts-node -e "
  const tool = require('${toolPath}');
  const args = ${argsStr};
  tool.default.execute(args).then((result) => {
    console.log(JSON.stringify(result, null, 2));
  }).catch((error) => {
    console.error('Tool execution failed:', error.message);
    process.exit(1);
  });
  "`;

  execSync(command, { stdio: 'inherit', cwd: __dirname });
} catch (error) {
  console.error('Failed to run tool:', error.message);
  process.exit(1);
}