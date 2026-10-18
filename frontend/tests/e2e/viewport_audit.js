import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const VIEWPORTS = [
  { name: "mobile_xs", width: 320, height: 700 },
  { name: "mobile_s", width: 360, height: 800 },
  { name: "mobile_m", width: 375, height: 812 },
  { name: "mobile_std", width: 390, height: 844 },
  { name: "mobile_plus", width: 430, height: 932 },
  { name: "tablet_port", width: 768, height: 1024 },
  { name: "tablet_land", width: 1024, height: 768 },
  { name: "desktop_wide", width: 1440, height: 900 }
];

const TABS = ["welcome", "analyze", "history", "learn", "settings"];

const screenshotDir = path.resolve("..", "reports", "e2e_screenshots");
fs.mkdirSync(screenshotDir, { recursive: true });

async function runViewportAudit() {
  console.log("=================================================");
  console.log("STARTING RESPONSIVE VIEWPORT AUDIT (8 VIEWPORTS)");
  console.log("=================================================");

  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
  });

  const auditResults = [];

  for (const vp of VIEWPORTS) {
    console.log(`\nTesting Viewport: ${vp.name} (${vp.width}x${vp.height})...`);
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: 1
    });

    const page = await context.newPage();
    await page.goto("http://localhost:5173", { waitUntil: "networkidle" });

    // Handle auth screen by entering via guest access
    const authPage = await page.$(".auth-page-container");
    if (authPage) {
      const guestBtn = await page.$(".auth-guest-btn");
      if (guestBtn) {
        await guestBtn.click();
        await page.waitForTimeout(300);
        const check = await page.$("#guest-disclaimer-checkbox");
        if (check) await check.check();
        const submit = await page.$(".guest-submit-btn");
        if (submit) await submit.click();
        await page.waitForTimeout(400);
      }
    }

    // Dismiss onboarding modal if auto-opened
    const onboardingClose = await page.$(".onboarding-close-btn, .modal-close-btn");
    if (onboardingClose) {
      await onboardingClose.click();
      await page.waitForTimeout(200);
    }

    const vpResult = {
      viewport: `${vp.width}x${vp.height} (${vp.name})`,
      tabs: {},
      overflows: [],
      navCheck: true,
      errors: []
    };

    // Check nav visibility
    const isMobileNav = vp.width <= 768;
    const desktopNavVisible = await page.$eval(".navbar .nav-tabs", el => {
      const style = window.getComputedStyle(el);
      return style.display !== "none";
    }).catch(() => false);

    const mobileNavVisible = await page.$eval(".mobile-bottom-nav", el => {
      const style = window.getComputedStyle(el);
      return style.display !== "none";
    }).catch(() => false);

    if (isMobileNav) {
      if (desktopNavVisible) {
        vpResult.errors.push(`Desktop nav tabs visible on mobile/tablet (${vp.width}px)`);
      }
      if (!mobileNavVisible) {
        vpResult.errors.push(`Mobile bottom nav NOT visible on mobile/tablet (${vp.width}px)`);
      }
    } else {
      if (!desktopNavVisible) {
        vpResult.errors.push(`Desktop nav tabs NOT visible on desktop (${vp.width}px)`);
      }
      if (mobileNavVisible) {
        vpResult.errors.push(`Mobile bottom nav visible on desktop (${vp.width}px)`);
      }
    }

    // Iterate through all tabs and inspect overflow
    for (const tab of TABS) {
      // Click tab (either from mobile nav or desktop nav)
      await page.evaluate((targetTab) => {
        // Try desktop tab first if visible
        const desktopBtn = Array.from(document.querySelectorAll(".nav-tab-btn")).find(
          b => b.textContent.toLowerCase().includes(targetTab)
        );
        if (desktopBtn && window.getComputedStyle(desktopBtn).display !== "none") {
          desktopBtn.click();
          return true;
        }
        // Try mobile nav
        const mobileBtn = Array.from(document.querySelectorAll(".mobile-nav-btn")).find(
          b => b.textContent.toLowerCase().includes(targetTab)
        );
        if (mobileBtn && window.getComputedStyle(mobileBtn).display !== "none") {
          mobileBtn.click();
          return true;
        }
        return false;
      }, tab);

      await page.waitForTimeout(300);

      // Check horizontal overflow
      const overflowDetails = await page.evaluate(() => {
        const docWidth = document.documentElement.scrollWidth;
        const bodyWidth = document.body.scrollWidth;
        const winWidth = window.innerWidth;
        const hasOverflow = docWidth > winWidth || bodyWidth > winWidth;

        let offending = [];
        if (hasOverflow) {
          const allElements = Array.from(document.querySelectorAll("*"));
          for (const el of allElements) {
            const rect = el.getBoundingClientRect();
            if (rect.right > winWidth + 1) { // 1px tolerance
              const tag = el.tagName.toLowerCase();
              const cls = el.className && typeof el.className === "string" ? `.${el.className.split(" ").join(".")}` : "";
              const id = el.id ? `#${el.id}` : "";
              offending.push({
                selector: `${tag}${id}${cls}`,
                right: Math.round(rect.right),
                width: Math.round(rect.width),
                scrollWidth: el.scrollWidth
              });
            }
          }
        }
        return {
          hasOverflow,
          docWidth,
          winWidth,
          offending: offending.slice(0, 5) // top 5
        };
      }, vp.width);

      vpResult.tabs[tab] = {
        hasOverflow: overflowDetails.hasOverflow,
        docWidth: overflowDetails.docWidth,
        winWidth: overflowDetails.winWidth
      };

      if (overflowDetails.hasOverflow) {
        console.warn(`  [OVERFLOW] Tab "${tab}" at ${vp.width}px has overflow! docWidth: ${overflowDetails.docWidth}px > winWidth: ${overflowDetails.winWidth}px`);
        console.warn(`    Offending elements:`, JSON.stringify(overflowDetails.offending, null, 2));
        vpResult.overflows.push({
          tab,
          ...overflowDetails
        });
      }

      // Take screenshot of tab
      const screenshotPath = path.join(screenshotDir, `vp_${vp.width}x${vp.height}_${tab}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: false });
    }

    auditResults.push(vpResult);
    await context.close();
  }

  await browser.close();

  console.log("\n=================================================");
  console.log("VIEWPORT AUDIT SUMMARY");
  console.log("=================================================");
  let totalOverflowIssues = 0;
  let totalNavIssues = 0;

  for (const res of auditResults) {
    console.log(`Viewport ${res.viewport}:`);
    if (res.errors.length > 0) {
      console.log(`  Nav errors:`, res.errors);
      totalNavIssues += res.errors.length;
    } else {
      console.log(`  Nav visibility: OK`);
    }
    if (res.overflows.length > 0) {
      console.log(`  Horizontal overflows detected:`, res.overflows.length);
      for (const ov of res.overflows) {
        console.log(`    - Tab "${ov.tab}": docWidth=${ov.docWidth}px, winWidth=${ov.winWidth}px`);
      }
      totalOverflowIssues += res.overflows.length;
    } else {
      console.log(`  Horizontal overflow: NONE across all 5 tabs`);
    }
  }

  console.log(`\nTOTAL OVERFLOW ISSUES: ${totalOverflowIssues}`);
  console.log(`TOTAL NAV ISSUES: ${totalNavIssues}`);
  console.log("=================================================");

  // Write report to JSON
  fs.writeFileSync(
    path.resolve("..", "reports", "viewport_audit_results.json"),
    JSON.stringify(auditResults, null, 2)
  );

  return { totalOverflowIssues, totalNavIssues, auditResults };
}

runViewportAudit().catch(err => {
  console.error("Audit failed:", err);
  process.exit(1);
});
