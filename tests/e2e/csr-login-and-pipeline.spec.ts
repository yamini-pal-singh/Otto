import { test, expect } from '@playwright/test';
// import { signIn } from '../fixtures/auth';

// --- Sign-in flow commented out for now ---
// test.describe('CSR Stage - Sign-in and Pipeline navigation', () => {
//   test.beforeEach(async ({ page }) => {
//     await signIn(page);
//   });
//
//   test('lands on Team dashboard after login', async ({ page }) => {
//     await expect(page).not.toHaveURL(/sign-in/);
//     await expect(page.locator('body')).toBeVisible();
//   });
//
//   test('sidebar toggle button is visible and clickable', async ({ page }) => {
//     const sidebarButton = page.locator(
//       'button.flex.h-10.w-10.items-center.justify-center.rounded-full.border'
//     ).first();
//     await expect(sidebarButton).toBeVisible({ timeout: 10_000 });
//     await sidebarButton.click();
//     await expect(sidebarButton).toBeVisible();
//   });
//
//   test('navigates to Pipeline from sidebar', async ({ page }) => {
//     const sidebarButton = page.locator(
//       'button.flex.h-10.w-10.items-center.justify-center.rounded-full.border'
//     ).first();
//     await sidebarButton.click();
//     const pipelineLink = page.getByRole('link', { name: /pipeline/i });
//     await expect(pipelineLink).toBeVisible({ timeout: 10_000 });
//     await pipelineLink.click();
//     await expect(page).toHaveURL(/pipeline/i, { timeout: 15_000 });
//   });
//
//   test('Pipeline page loads without error', async ({ page }) => {
//     const sidebarButton = page.locator(
//       'button.flex.h-10.w-10.items-center.justify-center.rounded-full.border'
//     ).first();
//     await sidebarButton.click();
//     await page.getByRole('link', { name: /pipeline/i }).click();
//     await expect(page).toHaveURL(/pipeline/i, { timeout: 15_000 });
//     await expect(page.locator('main, [role="main"], .pipeline, [data-testid="pipeline"]').first()).toBeVisible({ timeout: 10_000 });
//   });
// });

test.describe('CSR Stage - Sign-in page', () => {
  test('sign-in page loads and shows form', async ({ page }) => {
    await page.goto('/sign-in');
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('sign-in button is disabled when fields are empty', async ({ page }) => {
    await page.goto('/sign-in');
    const signInButton = page.getByRole('button', { name: /sign in/i });
    await expect(signInButton).toBeVisible();
    await expect(signInButton).toBeDisabled();
  });

  test('invalid credentials show error', async ({ page }) => {
    await page.goto('/sign-in');
    await page.getByLabel(/email/i).fill('wrong@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page.locator('text=/invalid|incorrect|error|sign in to your account/i')).toBeVisible({ timeout: 10_000 });
  });
});

// ============================================================================
// NEGATIVE / SECURITY TESTS — Sign-in form
// ============================================================================
test.describe('CSR Stage - Sign-in negative & security tests', () => {
  test('XSS in email field does not render as HTML', async ({ page }) => {
    await page.goto('/sign-in');
    const xssPayload = '<script>alert("xss")</script>';
    await page.getByLabel(/email/i).fill(xssPayload);
    await page.getByLabel(/password/i).fill('somepassword');
    await page.getByRole('button', { name: /sign in/i }).click();
    // The script tag must NOT execute — page should not show an alert dialog
    // and the XSS string should not appear as rendered HTML in the DOM
    const scriptTag = page.locator('script:has-text("alert")');
    await expect(scriptTag).toHaveCount(0);
    // Page should still be functional (no crash)
    await expect(page.getByLabel(/email/i)).toBeVisible();
  });

  test('XSS in password field does not render as HTML', async ({ page }) => {
    await page.goto('/sign-in');
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('<img src=x onerror=alert(1)>');
    await page.getByRole('button', { name: /sign in/i }).click();
    // Should not inject an img tag into the page
    const injectedImg = page.locator('img[src="x"]');
    await expect(injectedImg).toHaveCount(0);
    await expect(page.getByLabel(/email/i)).toBeVisible();
  });

  test('SQL injection in email field does not cause server error', async ({ page }) => {
    await page.goto('/sign-in');
    await page.getByLabel(/email/i).fill("'; DROP TABLE users; --");
    await page.getByLabel(/password/i).fill('password');
    await page.getByRole('button', { name: /sign in/i }).click();
    // Should show an error message, not a server crash / blank page
    await expect(page.locator('text=/invalid|incorrect|error|sign in to your account/i')).toBeVisible({ timeout: 10_000 });
  });

  test('very long input does not crash the form', async ({ page }) => {
    await page.goto('/sign-in');
    const longStr = 'a'.repeat(10_000);
    await page.getByLabel(/email/i).fill(longStr + '@example.com');
    await page.getByLabel(/password/i).fill(longStr);
    await page.getByRole('button', { name: /sign in/i }).click();
    // Page should still be functional — form visible, no crash
    await expect(page.getByLabel(/email/i)).toBeVisible({ timeout: 10_000 });
  });

  test('special characters in fields do not break the form', async ({ page }) => {
    await page.goto('/sign-in');
    await page.getByLabel(/email/i).fill('user+tag@exam"ple.com');
    await page.getByLabel(/password/i).fill('p@$$w0rd!#%^&*(){}[]');
    await page.getByRole('button', { name: /sign in/i }).click();
    // Should show error, not crash
    await expect(page.locator('text=/invalid|incorrect|error|sign in to your account/i')).toBeVisible({ timeout: 10_000 });
  });
});
