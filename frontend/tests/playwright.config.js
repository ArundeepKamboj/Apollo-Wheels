const { defineConfig } = require('@playwright/test');
const path = require('path');
const fs = require('fs');
const projectRoot = path.resolve(__dirname, '../..');
const reportDirectory = path.join(projectRoot, 'reports');
fs.mkdirSync(reportDirectory, { recursive: true });

module.exports = defineConfig({
  testDir: projectRoot,
  testMatch: '**/*.spec.js',
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  expect: { timeout: 10000 },
  reporter: [['list'], ['json', { outputFile: path.join(reportDirectory, 'ui-results.json') }]],
  use: {
    baseURL: 'http://127.0.0.1:5174',
    browserName: 'chromium',
    headless: true,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: `uv run --project "${projectRoot}" python scripts/run_local.py --config config/test.env.example`,
    cwd: projectRoot,
    url: 'http://127.0.0.1:5174',
    reuseExistingServer: false,
    timeout: 120000,
    stdout: 'pipe',
    stderr: 'pipe',
  },
});
