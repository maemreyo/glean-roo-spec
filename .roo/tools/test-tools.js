#!/usr/bin/env node

/**
 * Simple test runner for Roo Tools
 * Run individual tools for testing
 */

const { execSync } = require('child_process');
const path = require('path');

const toolName = process.argv[2];

if (!toolName) {
  console.log('Usage: node test-tools.js <tool-name>');
  console.log('Available tools:');
  console.log('  git-branch-detector');
  console.log('  branch-name-generator');
  console.log('  git-branch-creator');
  console.log('  filesystem-directory-creator');
  console.log('  spec-content-generator');
  process.exit(1);
}

const tools = {
  'git-branch-detector': {
    file: 'src/git-branch-detector.ts',
    params: { specsDir: '../specs', hasGit: true }
  },
  'branch-name-generator': {
    file: 'src/branch-name-generator.ts',
    params: { featureDescription: 'Add user authentication system' }
  },
  'git-branch-creator': {
    file: 'src/git-branch-creator.ts',
    params: { branchName: '999-test-branch', repoRoot: '.' }
  },
  'filesystem-directory-creator': {
    file: 'src/filesystem-operations.ts',
    params: { dirPath: 'test-dir' }
  },
  'spec-content-generator': {
    file: 'src/spec-content-generator.ts',
    params: {
      featureDescription: 'Add user login',
      branchName: '001-user-login',
      templatePath: '../templates/spec-template.md'
    }
  }
};

const tool = tools[toolName];
if (!tool) {
  console.error(`Unknown tool: ${toolName}`);
  process.exit(1);
}

const toolPath = path.join(__dirname, tool.file);
const params = JSON.stringify(tool.params);

console.log(`Testing ${toolName}...`);
console.log(`File: ${tool.file}`);
console.log(`Params: ${params}`);
console.log('---');

try {
  const command = `npx ts-node -e "
    import('./${tool.file}').then(async (m) => {
      try {
        const result = await m.default.execute(${params});
        console.log('SUCCESS:');
        console.log(JSON.stringify(result, null, 2));
      } catch (error) {
        console.error('ERROR:', error.message);
      }
    }).catch(console.error);
  "`;

  execSync(command, { stdio: 'inherit', cwd: __dirname });
} catch (error) {
  console.error('Command failed:', error.message);
  process.exit(1);
}