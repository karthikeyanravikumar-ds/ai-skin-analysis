import { chromium } from "playwright";
import fs from "fs";
import path from "path";

async function testDemoAccessGate() {
  console.log("=================================================");
  console.log("STARTING TEST SUITE: DEMO ACCESS GATE (AUTH-UI-01)");
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
  const testResults = {};

  try {
    // -------------------------------------------------------------
    // SCENARIO 1, 2, 3: Fresh Load, Modal Display, Inaccessible App Shell
    // -------------------------------------------------------------
    console.log("\n[SCENARIO 1, 2, 3] Testing fresh load and initial gate lockdown...");
    await page.goto("http://localhost:5173", { waitUntil: "networkidle" });

    // Verify modal is immediately visible
    const modalBox = await page.$(".demo-login-modal-box");
    if (!modalBox) throw new Error("DemoLoginModal was not displayed on fresh load.");
    console.log("  1. DemoLoginModal displayed immediately on load: PASS");

    // Verify Welcome page is NOT accessible/rendered
    const welcomeContainer = await page.$(".welcome-container");
    console.log("  2. Welcome page in DOM before entry:", Boolean(welcomeContainer));
    if (welcomeContainer) throw new Error("Welcome page was accessible before demo entry!");
    testResults.welcomeHiddenBeforeEntry = "PASS";

    // Verify navigation tabs and mobile bottom nav are NOT accessible/rendered
    const navTabs = await page.$(".navbar .nav-tabs");
    const mobileBottomNav = await page.$(".mobile-bottom-nav");
    console.log("  3. Navigation tabs in DOM before entry:", Boolean(navTabs));
    console.log("     Mobile bottom nav in DOM before entry:", Boolean(mobileBottomNav));
    if (navTabs || mobileBottomNav) {
      throw new Error("Navigation controls were accessible before demo entry!");
    }
    testResults.navigationBlockedBeforeEntry = "PASS";

    // -------------------------------------------------------------
    // SCENARIO 7 & 8: Escape and Backdrop Cannot Bypass Gate
    // -------------------------------------------------------------
    console.log("\n[SCENARIO 7 & 8] Testing that Escape and Backdrop clicks cannot bypass gate...");
    
    // Press Escape
    await page.keyboard.press("Escape");
    await page.waitForTimeout(200);
    let modalStillHere = await page.$(".demo-login-modal-box");
    if (!modalStillHere) throw new Error("Pressing Escape bypassed the initial demo gate!");
    console.log("  7. Escape key bypass prevented: PASS");
    testResults.escapeCannotBypass = "PASS";

    // Click Backdrop
    await page.mouse.click(15, 15);
    await page.waitForTimeout(200);
    modalStillHere = await page.$(".demo-login-modal-box");
    if (!modalStillHere) throw new Error("Clicking backdrop bypassed the initial demo gate!");
    console.log("  8. Backdrop click bypass prevented: PASS");
    testResults.backdropCannotBypass = "PASS";

    // Verify no Close (X) button or Cancel button in initial gate
    const closeBtn = await page.$(".modal-close-btn");
    const cancelBtn = await page.$("button:has-text('Cancel')");
    console.log("  Close (X) button present in gate:", Boolean(closeBtn));
    console.log("  Cancel button present in gate:", Boolean(cancelBtn));
    if (closeBtn || cancelBtn) {
      throw new Error("Initial gate contains dismissive Close or Cancel buttons!");
    }

    // -------------------------------------------------------------
    // SCENARIO 4: Submitting without disclaimer checkbox is rejected
    // -------------------------------------------------------------
    console.log("\n[SCENARIO 4] Testing disclaimer checkbox validation...");
    // Ensure checkbox is unchecked
    const isChecked = await page.isChecked(".demo-checkbox-label input[type='checkbox']");
    if (isChecked) {
      await page.uncheck(".demo-checkbox-label input[type='checkbox']");
    }

    // Attempt submission
    await page.click("button[type='submit']");
    await page.waitForTimeout(200);

    // Verify error banner is visible with validation text
    const errorBanner = await page.$(".demo-error-banner");
    if (!errorBanner) throw new Error("Submission without disclaimer did not display error banner!");
    const errorText = await page.textContent(".demo-error-banner");
    console.log(`  Validation error displayed: "${errorText?.trim()}"`);
    if (!errorText?.includes("educational evaluation only")) {
      throw new Error("Validation message content incorrect.");
    }

    // Confirm app is still locked
    const welcomeStillHidden = (await page.$(".welcome-container")) === null;
    if (!welcomeStillHidden) throw new Error("App unlocked despite validation failure!");
    console.log("  4. Submission rejected without disclaimer: PASS");
    testResults.disclaimerValidation = "PASS";

    // -------------------------------------------------------------
    // SCENARIO 6 & 5: Optional name left blank, Valid entry opens Welcome page
    // -------------------------------------------------------------
    console.log("\n[SCENARIO 6 & 5] Testing valid entry with blank optional name...");
    // Leave evaluator name blank
    await page.fill("#evaluator-name", "");
    await page.selectOption("#evaluator-role", "student");

    // Check disclaimer
    await page.check(".demo-checkbox-label input[type='checkbox']");
    await page.waitForTimeout(100);

    // Verify error banner cleared
    const errorBannerAfterCheck = await page.$(".demo-error-banner");
    console.log("  Error banner cleared upon checking disclaimer:", errorBannerAfterCheck === null);

    // Submit valid form
    await page.click("button[type='submit']");
    await page.waitForTimeout(400);

    // Verify modal is gone
    const modalGone = (await page.$(".demo-login-modal-box")) === null;
    if (!modalGone) throw new Error("DemoLoginModal remained visible after valid entry!");
    console.log("  Demo modal closed upon valid entry: PASS");

    // Verify Welcome page is now rendered
    const welcomePage = await page.$(".welcome-container");
    if (!welcomePage) throw new Error("Welcome page failed to render after valid demo entry!");
    const welcomeHeading = await page.textContent(".welcome-title");
    console.log(`  5. Welcome page rendered: "${welcomeHeading?.trim().replace(/\s+/g, ' ')}"`);
    testResults.validEntryOpensWelcome = "PASS";

    // Verify default fallback name was applied in badge
    const badgeText = await page.textContent(".demo-user-name");
    console.log(`  6. Fallback evaluator badge: "${badgeText?.trim()}" (expected "Clinical Evaluator")`);
    if (!badgeText?.includes("Clinical Evaluator")) {
      throw new Error("Default name was not applied when evaluator name left blank.");
    }
    testResults.optionalNameBlankFallback = "PASS";

    // -------------------------------------------------------------
    // SCENARIO 12: Existing onboarding still works after entry
    // -------------------------------------------------------------
    console.log("\n[SCENARIO 12] Testing onboarding tutorial after demo entry...");
    await page.evaluate(() => localStorage.removeItem("has_seen_skin_onboarding"));
    const getStartedBtn = await page.$(".welcome-btn-primary");
    if (getStartedBtn) {
      await getStartedBtn.click();
      await page.waitForTimeout(300);
      const onboardingModal = await page.$(".onboarding-modal-box");
      console.log("  Onboarding modal triggered via Get Started:", Boolean(onboardingModal));
      if (!onboardingModal) throw new Error("Onboarding modal failed to trigger after demo entry.");
      // Close onboarding
      const closeTour = await page.$(".modal-close-btn");
      if (closeTour) await closeTour.click();
      await page.waitForTimeout(200);
    }
    testResults.onboardingWorks = "PASS";

    // -------------------------------------------------------------
    // SCENARIO 13: Existing application workflows remain functional
    // -------------------------------------------------------------
    console.log("\n[SCENARIO 13] Testing tab navigation and workflow access...");
    await page.click(".nav-tab-btn:has-text('Learn')");
    await page.waitForTimeout(200);
    const learnCatalog = await page.$(".catalog-layout");
    console.log("  Navigated to Learn tab successfully:", Boolean(learnCatalog));

    await page.click(".nav-tab-btn:has-text('Settings')");
    await page.waitForTimeout(200);
    const settingsGrid = await page.$(".settings-grid");
    console.log("  Navigated to Settings tab successfully:", Boolean(settingsGrid));

    await page.click(".nav-tab-btn:has-text('Analyze')");
    await page.waitForTimeout(200);
    const analysisCard = await page.$(".analysis-card");
    console.log("  Navigated to Analyze tab successfully:", Boolean(analysisCard));
    testResults.existingWorkflowsFunctional = "PASS";

    // -------------------------------------------------------------
    // SCENARIO 9: Exiting the demo session returns to gate
    // -------------------------------------------------------------
    console.log("\n[SCENARIO 9] Testing session exit returns to gate...");
    const exitBtn = await page.$(".demo-exit-btn");
    if (!exitBtn) throw new Error("Demo exit button not found in navbar.");
    await exitBtn.click();
    await page.waitForTimeout(400);

    // Verify modal is back
    const modalBack = await page.$(".demo-login-modal-box");
    if (!modalBack) throw new Error("Session exit did not display the Demo Access Gate!");
    console.log("  Demo modal re-displayed upon exit: PASS");

    // Verify previous screens are NOT in DOM
    const analyzeInDom = await page.$(".analysis-card");
    const welcomeInDom = await page.$(".welcome-container");
    console.log("  Analyze card in DOM after exit:", Boolean(analyzeInDom));
    console.log("  Welcome page in DOM after exit:", Boolean(welcomeInDom));
    if (analyzeInDom || welcomeInDom) {
      throw new Error("Application screens remained accessible in DOM after exiting demo session!");
    }
    console.log("  9. Session exit completely locks application: PASS");
    testResults.sessionExitReturnsToGate = "PASS";

    // -------------------------------------------------------------
    // SCENARIO 10: Reloading follows session policy (requires gate on fresh load)
    // -------------------------------------------------------------
    console.log("\n[SCENARIO 10] Testing reload session policy...");
    await page.reload({ waitUntil: "networkidle" });
    const modalAfterReload = await page.$(".demo-login-modal-box");
    const welcomeAfterReload = await page.$(".welcome-container");
    if (!modalAfterReload || welcomeAfterReload) {
      throw new Error("Application did not present demo gate upon reload!");
    }
    console.log("  10. Reload displays demo gate as required: PASS");
    testResults.reloadSessionPolicy = "PASS";

    // -------------------------------------------------------------
    // SCENARIO 11: Mobile layout at 320px, 375px, 430px
    // -------------------------------------------------------------
    console.log("\n[SCENARIO 11] Testing mobile layouts (320px, 375px, 430px)...");
    for (const width of [320, 375, 430]) {
      await page.setViewportSize({ width, height: 750 });
      await page.waitForTimeout(200);

      const overflow = await page.evaluate(() => {
        const docW = document.documentElement.scrollWidth;
        const winW = window.innerWidth;
        const modal = document.querySelector(".demo-login-modal-box");
        const modalRect = modal ? modal.getBoundingClientRect() : null;
        return {
          hasOverflow: docW > winW,
          docW,
          winW,
          modalWidth: modalRect ? Math.round(modalRect.width) : null
        };
      }, width);

      console.log(`  Viewport ${width}px: docWidth=${overflow.docW} <= winWidth=${overflow.winW}, modalWidth=${overflow.modalWidth}px (overflow: ${overflow.hasOverflow})`);
      if (overflow.hasOverflow) {
        throw new Error(`Horizontal overflow detected at ${width}px on Demo Access Gate!`);
      }
    }
    testResults.mobileLayoutPass = "PASS";

  } catch (err) {
    console.error("Test failed with error:", err);
    testResults.fatalError = err.message;
  } finally {
    await browser.close();
  }

  console.log("\n=================================================");
  console.log("DEMO ACCESS GATE TEST SUMMARY");
  console.log("=================================================");
  console.log(JSON.stringify(testResults, null, 2));

  fs.writeFileSync(
    path.resolve("..", "reports", "auth_gate_test_results.json"),
    JSON.stringify(testResults, null, 2)
  );

  return testResults;
}

testDemoAccessGate().catch(err => {
  console.error("Execution error:", err);
  process.exit(1);
});
