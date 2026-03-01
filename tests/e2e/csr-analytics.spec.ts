import { test, expect } from '@playwright/test';
// import { signIn } from '../fixtures/auth';

/**
 * CSR Stage - Pipeline Kanban board tests.
 * Sign-in flow commented out for now — these tests require auth to run.
 */

// --- Sign-in dependent tests commented out for now ---
// test.describe('CSR Stage - Pipeline board and lead data', () => {
//   test.beforeEach(async ({ page }) => {
//     await signIn(page);
//     const sidebarButton = page.locator(
//       'button.flex.h-10.w-10.items-center.justify-center.rounded-full.border'
//     ).first();
//     await sidebarButton.click();
//     await page.getByRole('link', { name: /pipeline/i }).click();
//     await expect(page).toHaveURL(/pipeline/i, { timeout: 15_000 });
//   });
//
//   test('Pipeline page has main content area', async ({ page }) => {
//     const main = page.locator('main, [role="main"], .pipeline, [data-testid="pipeline"]').first();
//     await expect(main).toBeVisible({ timeout: 10_000 });
//   });
//
//   test('Pipeline Kanban columns are visible', async ({ page }) => {
//     const column = page.locator('text=/Unqualified|Qualified|Service Not Offered|Booked/i').first();
//     await expect(column).toBeVisible({ timeout: 15_000 });
//   });
//
//   test('Pipeline shows lead count summary', async ({ page }) => {
//     const summary = page.locator('text=/\\d+ leads/i');
//     await expect(summary).toBeVisible({ timeout: 15_000 });
//   });
// });
