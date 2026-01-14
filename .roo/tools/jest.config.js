/**
 * Jest configuration for Roo Custom Tools
 *
 * Configures Jest for testing TypeScript tools with ES modules support.
 * See plans/migration/05-testing-strategy.md for details.
 *
 * @see {@link plans/migration/05-testing-strategy.md}
 */

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
        tsconfig: './tsconfig.json',
      },
    ],
  },
  testMatch: [
    '**/tests/**/*.test.ts',
    '**/tests/**/*.spec.ts',
  ],
  collectCoverageFrom: [
    '.roo/tools/**/*.ts',
    '.roo/tools/lib/**/*.ts',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/dist/**',
    '!**/tests/**',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  verbose: true,
  testTimeout: 10000,
};
