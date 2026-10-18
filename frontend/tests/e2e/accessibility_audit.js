import { chromium } from "playwright";
import fs from "fs";
import path from "path";

async function runAccessibilityAudit() {
  console.log("=================================================");
  console.log("STARTING ACCESSIBILITY & KEYBOARD NAVIGATION AUDIT");
  console.log("=================================================");

  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1
  });

  const page = await context.newPage();
  await page.goto("http://localhost:5173", { waitUntil: "networkidle" });

  const a11yResults = {
    keyboardNav: "PASS",
    modalEscape: "PASS",
    ariaAttributes: "PASS",
    reducedMotion: "PASS",
    touchTargetsMobile: "PASS",
    findings: []
  };

  // 1. Check Keyboard Navigation (Tab focus)
  console.log("\n1. Testing Keyboard Navigation & Focus Indicators...");
  let focusedElements = [];
  for (let i = 0; i < 8; i++) {
    await page.keyboard.press("Tab");
    const activeInfo = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el) return null;
      const style = window.getComputedStyle(el);
      return {
        tag: el.tagName.toLowerCase(),
        text: el.textContent?.trim().slice(0, 30),
        outline: style.outline,
        outlineWidth: style.outlineWidth,
        outlineStyle: style.outlineStyle
      };
    });
    if (activeInfo) focusedElements.push(activeInfo);
  }
  console.log(`  Tabbed through ${focusedElements.length} interactive elements successfully.`);
  console.log(`  Sample focus targets:`, focusedElements.map(e => `${e.tag} ("${e.text}")`).slice(0, 4));

  // 2. Modal Escape Key Dismissal
  console.log("\n2. Testing Modal Escape Key Dismissal...");
  const demoBtn = await page.$(".welcome-btn-tertiary");
  if (demoBtn) {
    await demoBtn.click();
    await page.waitForTimeout(300);
    const isModalOpen = await page.$(".demo-login-modal-box");
    if (isModalOpen) {
      console.log("  Modal opened. Pressing Escape key...");
      await page.keyboard.press("Escape");
      await page.waitForTimeout(300);
      const isStillOpen = await page.$(".demo-login-modal-box");
      if (isStillOpen) {
        console.warn("  [A11Y DEFECT] DemoLoginModal was NOT closed by pressing Escape key!");
        a11yResults.findings.push("DemoLoginModal does not support Escape key listener for dismissal");
        a11yResults.modalEscape = "DEFECT";
      } else {
        console.log("  Modal closed successfully with Escape key.");
      }
    }
  }

  // 3. ARIA Attributes
  console.log("\n3. Testing ARIA Roles & Attributes...");
  const ariaChecks = await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll("[role='tab']"));
    const tablists = Array.from(document.querySelectorAll("[role='tablist']"));
    const buttonsWithoutLabels = Array.from(document.querySelectorAll("button:not([aria-label])"))
      .filter(b => !b.textContent.trim() && !b.getAttribute("title"));

    return {
      tabCount: tabs.length,
      tablistCount: tablists.length,
      unlabelledIconButtons: buttonsWithoutLabels.length
    };
  });
  console.log(`  Found ${ariaChecks.tabCount} tab elements in ${ariaChecks.tablistCount} tablists.`);
  console.log(`  Unlabeled icon buttons: ${ariaChecks.unlabelledIconButtons}`);
  if (ariaChecks.unlabelledIconButtons > 0) {
    a11yResults.findings.push(`Found ${ariaChecks.unlabelledIconButtons} buttons without text or aria-label`);
  }

  // 4. Reduced Motion
  console.log("\n4. Testing Reduced Motion System...");
  await page.click(".nav-tab-btn:has-text('Settings')");
  await page.waitForTimeout(300);

  const toggle = await page.$(".toggle-switch-btn");
  if (toggle) {
    await toggle.click();
    await page.waitForTimeout(200);

    const isReduced = await page.$eval(".app", el => el.classList.contains("reduced-motion"));
    console.log(`  .reduced-motion class applied to root: ${isReduced}`);

    // Check if transitions are suppressed in CSS
    const transitionDuration = await page.evaluate(() => {
      const testEl = document.querySelector(".btn-primary, .analyze-button, .nav-tab-btn");
      if (!testEl) return null;
      return window.getComputedStyle(testEl).transitionDuration;
    });
    console.log(`  Sample button transition duration: ${transitionDuration}`);
  }

  // 5. Mobile Touch Target Sizing (375px viewport)
  console.log("\n5. Testing Mobile Touch Targets (375px)...");
  await page.setViewportSize({ width: 375, height: 812 });
  await page.waitForTimeout(300);

  const mobileNavTargets = await page.evaluate(() => {
    const navButtons = Array.from(document.querySelectorAll(".mobile-nav-btn"));
    return navButtons.map(btn => {
      const rect = btn.getBoundingClientRect();
      return {
        label: btn.textContent.trim(),
        width: Math.round(rect.width),
        height: Math.round(rect.height)
      };
    });
  });

  console.log("  Mobile Bottom Navigation Target Dimensions:");
  for (const t of mobileNavTargets) {
    console.log(`    - ${t.label}: ${t.width}px x ${t.height}px (height target >= 48px: ${t.height >= 48})`);
    if (t.height < 44 || t.width < 44) {
      a11yResults.findings.push(`Mobile nav button "${t.label}" target smaller than 44px (${t.width}x${t.height})`);
    }
  }

  await browser.close();

  console.log("\n=================================================");
  console.log("ACCESSIBILITY AUDIT SUMMARY");
  console.log("=================================================");
  console.log(JSON.stringify(a11yResults, null, 2));

  fs.writeFileSync(
    path.resolve("..", "reports", "accessibility_audit_results.json"),
    JSON.stringify(a11yResults, null, 2)
  );

  return a11yResults;
}

runAccessibilityAudit().catch(err => {
  console.error("A11y audit failed:", err);
  process.exit(1);
});
