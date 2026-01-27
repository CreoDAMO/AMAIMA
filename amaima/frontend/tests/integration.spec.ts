// frontend/tests/integration.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Complete User Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear local storage and cookies
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
  });

  test('user can register, login, and submit a query', async ({ page }) => {
    // 1. Register
    await page.goto('/register');
    await page.fill('input[name="name"]', 'Test User');
    await page.fill('input[name="email"]', `test${Date.now()}@example.com`);
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);

    // 2. Navigate to query page
    await page.click('text=New Query');
    await expect(page.locator('h1')).toContainText('New Query');

    // 3. Submit a query
    await page.fill(
      'textarea[placeholder*="Ask"]',
      'What are the main principles of quantum computing?'
    );
    await page.click('button:has-text("Submit")');

    // 4. Wait for response
    await expect(page.locator('text=quantum')).toBeVisible({ timeout: 60000 });

    // 5. Verify response metadata
    await expect(page.locator('text=Model:')).toBeVisible();
    await expect(page.locator('text=Latency:')).toBeVisible();
    await expect(page.locator('text=Confidence:')).toBeVisible();
  });

  test('WebSocket streaming updates display correctly', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/dashboard/);

    // Navigate to query with streaming
    await page.click('text=New Query');
    const textarea = page.locator('textarea[placeholder*="Ask"]');
    await textarea.fill('Write a detailed explanation of neural networks');
    await page.click('button:has-text("Submit")');

    // Verify streaming indicator
    await expect(page.locator('text=Streaming')).toBeVisible();

    // Verify content appears progressively
    await expect(page.locator('text=Neural networks')).toBeVisible({ timeout: 30000 });

    // Verify completion
    await expect(page.locator('text=completed')).toBeVisible({ timeout: 120000 });
  });

  test('file upload and processing', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/dashboard/);

    // Navigate to file upload
    await page.click('text=Upload');
    await page.setInputFiles('input[type="file"]', 'tests/fixtures/sample.pdf');

    // Verify upload progress
    await expect(page.locator('text=Upload complete')).toBeVisible({ timeout: 30000 });

    // Submit query with file
    await page.fill(
      'textarea[placeholder*="Ask"]',
      'Summarize the key points from the uploaded document'
    );
    await page.click('button:has-text("Submit")');

    // Verify response
    await expect(page.locator('text=Key Points')).toBeVisible({ timeout: 60000 });
  });
});
