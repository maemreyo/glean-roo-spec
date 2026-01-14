#!/usr/bin/env node

// Simple runner for check-prerequisites functionality
// This bypasses the TypeScript compilation issues

import { execSync } from 'node:child_process';
import { existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

// Get current directory
const __dirname = fileURLToPath(new URL('.', import.meta.url));

// Check if we're on a feature branch by checking git
function checkFeatureBranch() {
  try {
    const branch = execSync('git branch --show-current', { encoding: 'utf8' }).trim();
    const hasGit = existsSync(join(__dirname, '..', '..', '.git'));
    
    if (!hasGit) {
      return { isValid: false, error: 'Not a git repository' };
    }
    
    // Check if it's a feature branch (contains digits followed by -)
    const featureBranchRegex = /^\d{3}-/;
    if (!featureBranchRegex.test(branch)) {
      return { isValid: false, error: `Not on a feature branch (current: ${branch})` };
    }
    
    return { isValid: true, branch };
  } catch (error) {
    return { isValid: false, error: 'Failed to check git branch: ' + error.message };
  }
}

// Get feature directory path
function getFeatureDir() {
  try {
    const branch = execSync('git branch --show-current', { encoding: 'utf8' }).trim();
    return join(__dirname, '..', '..', 'specs', branch);
  } catch (error) {
    return null;
  }
}

// Check available documentation files
function checkAvailableDocs(featureDir) {
  const availableDocs = [];
  
  const docs = [
    { name: 'research.md', path: join(featureDir, 'research.md') },
    { name: 'data-model.md', path: join(featureDir, 'data-model.md') },
    { name: 'design.md', path: join(featureDir, 'design.md') },
    { name: 'quickstart.md', path: join(featureDir, 'quickstart.md') },
    { name: 'tasks.md', path: join(featureDir, 'tasks.md') },
  ];
  
  const contractsDir = join(featureDir, 'contracts');
  
  docs.forEach(doc => {
    if (existsSync(doc.path)) {
      availableDocs.push(doc.name);
    }
  });
  
  if (existsSync(contractsDir) && readdirSync(contractsDir).length > 0) {
    availableDocs.push('contracts/');
  }
  
  return availableDocs;
}

// Main function
function main() {
  const args = process.argv.slice(2);
  const jsonOutput = args.includes('--json');
  
  // Check if we're on a feature branch
  const branchValidation = checkFeatureBranch();
  if (!branchValidation.isValid) {
    if (jsonOutput) {
      console.log(JSON.stringify({ error: branchValidation.error, valid: false }));
    } else {
      console.log(`ERROR: ${branchValidation.error}`);
    }
    return;
  }
  
  const featureDir = getFeatureDir();
  
  if (!existsSync(featureDir)) {
    const errorMsg = `ERROR: Feature directory not found: ${featureDir}`;
    if (jsonOutput) {
      console.log(JSON.stringify({ error: errorMsg, valid: false }));
    } else {
      console.log(errorMsg);
    }
    return;
  }
  
  // Check required files
  const requiredFiles = ['plan.md'];
  const missingRequired = requiredFiles.filter(file => !existsSync(join(featureDir, file)));
  
  if (missingRequired.length > 0) {
    const errorMsg = `ERROR: Missing required files: ${missingRequired.join(', ')}`;
    if (jsonOutput) {
      console.log(JSON.stringify({ error: errorMsg, valid: false }));
    } else {
      console.log(errorMsg);
    }
    return;
  }
  
  // Check available docs
  const availableDocs = checkAvailableDocs(featureDir);
  
  // Output results
  if (jsonOutput) {
    const result = {
      FEATURE_DIR: featureDir,
      AVAILABLE_DOCS: availableDocs,
      HAS_TASKS: availableDocs.includes('tasks.md'),
      VALID: true,
    };
    console.log(JSON.stringify(result));
  } else {
    console.log(`FEATURE_DIR: ${featureDir}`);
    console.log('AVAILABLE_DOCS:');
    availableDocs.forEach(doc => {
      console.log(`  ✓ ${doc}`);
    });
    console.log(`VALID: true`);
  }
}

// Run the main function
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}