import { expect, test } from "@playwright/test";

/**
 * End-to-end smoke test: register -> land on dashboard -> open builder.
 * Requires the backend (http://localhost:8000) and frontend dev server to be
 * running. Run with: `npm run e2e`.
 */
test("register and reach the dashboard", async ({ page }) => {
  const unique = Date.now();
  await page.goto("/login");

  // Switch to register mode
  await page.getByRole("button", { name: "Register" }).click();
  await page.getByLabel("Email").fill(`e2e-${unique}@example.com`);
  await page.getByLabel("Username").fill(`e2e${unique}`);
  await page.getByLabel("Password").fill("supersecret123");
  await page.getByRole("button", { name: "Create account" }).click();

  await expect(page.getByText("Welcome back")).toBeVisible();

  // Open the pipeline builder
  await page.getByRole("link", { name: "+ New Pipeline" }).click();
  await expect(page.getByText("Module Library")).toBeVisible();
});
