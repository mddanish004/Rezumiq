import { test, expect } from "@playwright/test";

test("landing, signup, editor, share, public page, analytics, profile, ATS", async ({ page, browser, browserName }, testInfo) => {
  test.skip(browserName !== "chromium", "Chromium only");
  const stamp = Date.now();
  const email = `ui-${stamp}@example.com`;
  const password = "CorrectHorseBattery9!";

  await page.goto("/");
  await expect(page.getByRole("heading", { name: /write with precision/i })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("landing.png"), fullPage: true });

  if (testInfo.project.name === "mobile") {
    await page.goto("/signup");
  } else {
    await page.getByRole("link", { name: /start free/i }).first().click();
  }
  await expect(page).toHaveURL(/\/signup/);
  await page.locator('input[name="emailAddress"]').fill(email);
  await page.getByRole("button", { name: /continue/i }).first().click();
  await expect(page.locator('input[name="password"]').first()).toBeVisible({ timeout: 20_000 });
  await page.locator('input[name="password"]').first().fill(password);
  const confirm = page.locator('input[name="confirmPassword"]');
  if (await confirm.count()) await confirm.first().fill(password);
  await page.getByRole("button", { name: /continue/i }).click();

  await expect(page).toHaveURL(/\/app/, { timeout: 20_000 });
  await expect(page.getByRole("heading", { name: /welcome back/i })).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/no resumes yet/i).first()).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("dashboard-empty.png"), fullPage: true });

  await page.getByRole("button", { name: /new resume/i }).first().click();
  await page.getByPlaceholder("Backend Engineer - Stripe").fill("Backend Engineer - Stripe");
  await page.getByRole("button", { name: /^create resume$/i }).click();
  await expect(page).toHaveURL(/\/app\/resumes\/[^/]+\/edit/, { timeout: 30_000 });
  await expect(page.getByRole("heading", { name: /who is this resume for/i })).toBeVisible();

  await page.getByLabel("Full name").fill("Rohan Kulkarni");
  await page.getByLabel("Professional title").fill("Staff Infrastructure Engineer");
  await page.getByLabel("Email").fill("rohan@example.com");
  await page.getByRole("textbox", { name: "Location", exact: true }).fill("Bengaluru, India");

  await page.getByRole("button", { name: /add a section/i }).click();
  await page.getByRole("button", { name: "Experience", exact: true }).click();
  await page.getByRole("button", { name: /add role/i }).click();
  await page.getByLabel("Organization").fill("Razorpay");
  await page.getByLabel("Role").fill("Systems Architect");
  await page.getByLabel("Start").fill("2024-01");
  await page.getByLabel("End").fill("present");
  const saved = page.waitForResponse(
    (response) => response.url().includes("/versions") && response.request().method() === "POST",
    { timeout: 30_000 },
  );
  await page.getByRole("button", { name: /add bullet/i }).click();
  await page
    .getByPlaceholder(/start with a strong verb/i)
    .fill("Built a billing API handling two million daily requests.");
  await saved;
  await expect(page.getByText(/^(Saved|Saving)/i).first()).toBeVisible({ timeout: 30_000 });
  if (testInfo.project.name === "mobile") {
    await page.getByRole("button", { name: /preview/i }).first().click();
  }
  await expect(page.getByAltText("Resume page 1").last()).toBeVisible({ timeout: 60_000 });
  await expect(page.getByText(/1 compiled/i)).toBeVisible({ timeout: 30_000 });
  if (testInfo.project.name === "mobile") {
    await page.getByRole("button", { name: /^close$/i }).click();
  }
  await page.screenshot({ path: testInfo.outputPath("editor.png"), fullPage: true });

  await page.getByRole("button", { name: /history/i }).first().click();
  await expect(page.getByRole("heading", { name: /version history/i })).toBeVisible();
  await expect(page.getByText(/current head/i)).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("history.png"), fullPage: false });
  await page.getByRole("button", { name: /close history/i }).click();

  await page.getByRole("button", { name: /ask ai/i }).first().click();
  await expect(page.getByRole("dialog").getByText("Ask AI")).toBeVisible();
  await page.getByRole("button", { name: /close ai/i }).click();

  await page.getByRole("button", { name: "LaTeX", exact: true }).click();
  await expect(page.getByText("RESUME.TEX")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByAltText("Resume page 1").last()).toBeVisible({ timeout: 60_000 });
  await page.screenshot({ path: testInfo.outputPath("latex-editor.png"), fullPage: true });

  await page.goto("/ats-checker");
  await page.getByPlaceholder(/paste the resume text/i).fill(
    "Aarav Sharma\nBackend Engineer\naarav.sharma@example.com | +91 98765 43210 | Bengaluru\n" +
      "Summary\nBackend engineer with four years of experience building billing APIs in Go.\n" +
      "Skills\nGo, Python, Postgres, Redis, Docker\n" +
      "Experience\nAcme - Backend Engineer 2024 - present\n" +
      "Built a billing API in Go handling two million requests a day.\n" +
      "Reduced checkout latency by 40% with Redis caching.\n" +
      "Education\nNational Institute of Technology - B.Tech Computer Science 2020 - 2024",
  );
  await page.getByRole("button", { name: /run the ats report/i }).click();
  await expect(page.getByText(/ATS score/i).first()).toBeVisible({ timeout: 60_000 });
  await expect(page.locator("#ats-report")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("ats-report.png"), fullPage: true });

  await page.goto("/app/usage");
  await expect(page.getByRole("heading", { name: /what the plan has used/i })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("usage.png"), fullPage: true });

  await page.goto("/app/billing");
  await expect(page.getByRole("heading", { name: /one plan, spelled out/i })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("billing.png"), fullPage: true });

  await page.goto("/app/settings");
  await expect(page.getByRole("heading", { name: /account and keys/i })).toBeVisible();
  await expect(page.getByText(/no ai key saved yet/i)).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("settings.png"), fullPage: true });

  await page.goto("/app/import");
  await expect(page.getByRole("heading", { name: /bring a resume in/i })).toBeVisible();
  await page.getByRole("button", { name: /paste text/i }).click();
  await expect(page.getByPlaceholder(/paste the full resume here/i)).toBeVisible();
  await page.getByRole("button", { name: /write from notes/i }).click();
  await expect(page.getByPlaceholder(/b\.tech cse from bits/i)).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("import.png"), fullPage: true });

  await page.goto("/app/profile");
  await expect(page.getByRole("heading", { name: /the master profile/i })).toBeVisible();
  const profileSaved = page.waitForResponse(
    (response) => response.url().endsWith("/v1/profile") && response.request().method() === "PUT",
    { timeout: 30_000 },
  );
  await page.getByLabel("Professional title").fill("Staff Infrastructure Engineer");
  await profileSaved;
  await page.reload();
  await expect(page.getByLabel("Professional title")).toHaveValue("Staff Infrastructure Engineer", {
    timeout: 20_000,
  });
  await page.screenshot({ path: testInfo.outputPath("profile.png"), fullPage: true });

  await page.goto("/app/ats");
  await expect(page.getByRole("heading", { name: /read the page like a machine/i })).toBeVisible();
  await page.getByRole("button", { name: /run the check/i }).click();
  await expect(page.getByText("Parse rate").first()).toBeVisible({ timeout: 90_000 });
  await page.screenshot({ path: testInfo.outputPath("ats-signed-in.png"), fullPage: true });

  await page.goto("/app/resumes");
  await page.getByRole("button", { name: "Share resume" }).first().click();
  const share = page.getByRole("dialog");
  await share.getByRole("button", { name: /create a link/i }).click();
  await share.getByRole("button", { name: /^create link$/i }).click();
  const shareCode = share.locator("code").first();
  await expect(shareCode).toBeVisible({ timeout: 20_000 });
  const sharePath = new URL(`http://${await shareCode.innerText()}`).pathname;
  await page.screenshot({ path: testInfo.outputPath("share.png"), fullPage: false });
  await share.getByRole("button", { name: /close share/i }).click();

  const visitor = await browser.newContext({
    userAgent:
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  });
  const publicPage = await visitor.newPage();
  await publicPage.goto(sharePath);
  await expect(publicPage.getByAltText("Resume page 1").last()).toBeVisible({ timeout: 60_000 });
  await publicPage.screenshot({ path: testInfo.outputPath("public-resume.png"), fullPage: true });

  const me = await page.evaluate(async () => {
    const token = document.cookie.match(/(?:^|;\s*)__session=([^;]+)/)?.[1];
    const response = await fetch("http://localhost:8000/v1/me", {
      credentials: "include",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return (await response.json()).data as { username: string };
  });
  await publicPage.goto(`/${me.username}`);
  await expect(publicPage.getByRole("heading", { name: "Rohan Kulkarni" })).toBeVisible({ timeout: 20_000 });
  await publicPage.screenshot({ path: testInfo.outputPath("public-profile.png"), fullPage: true });
  await visitor.close();

  await page.goto("/app/analytics");
  await expect(page.getByRole("heading", { name: /what happens after you share/i })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("analytics.png"), fullPage: true });

  await page.goto("/app/admin");
  await expect(page).toHaveURL(/\/app$/, { timeout: 20_000 });
});
