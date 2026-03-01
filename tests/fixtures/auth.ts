import { Page } from '@playwright/test';

const SIGN_IN_EMAIL = process.env.SIGN_IN_EMAIL || 'anthony@arizonaroofers.com';
const SIGN_IN_PASSWORD = process.env.SIGN_IN_PASSWORD || 'anthonybonomo';

/**
 * Signs in to gomotto staging and waits for redirect to Team dashboard.
 * Call this in beforeEach or at the start of tests that need to be logged in.
 */
export async function signIn(page: Page): Promise<void> {
  await page.goto('/sign-in');
  await page.getByLabel(/email/i).fill(SIGN_IN_EMAIL);
  await page.getByLabel(/password/i).fill(SIGN_IN_PASSWORD);
  await page.getByRole('button', { name: /sign in/i }).click();
  // Wait for navigation away from sign-in (e.g. Team dashboard)
  await page.waitForURL((url) => !url.pathname.includes('sign-in'), { timeout: 15_000 });
}
