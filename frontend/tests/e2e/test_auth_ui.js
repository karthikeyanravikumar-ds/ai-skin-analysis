import { chromium } from "playwright";

async function runAuthUITests() {
  console.log("=================================================");
  console.log("STARTING TEST SUITE: AUTH-UI-02 (AUTHENTICATION)");
  console.log("=================================================");

  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
  });

  const page = await context.newPage();
  const testResults = {};

  try {
    // -------------------------------------------------------------
    // 1. INITIAL LOAD & LOGIN PAGE VERIFICATION
    // -------------------------------------------------------------
    console.log("\n[TEST 1] Testing Initial Screen is Login Page...");
    // Clear any previous session
    await page.goto("http://localhost:5173", { waitUntil: "networkidle" });
    await page.evaluate(() => sessionStorage.clear());
    await page.reload({ waitUntil: "networkidle" });

    // Verify AuthView container is visible
    const authContainer = await page.$(".auth-page-container");
    console.log("  Auth page container present:", Boolean(authContainer));

    // Verify Branding Column elements
    const brandTitle = await page.textContent(".auth-brand-title");
    console.log(`  Brand Title: "${brandTitle?.trim()}"`);
    const benefitCount = await page.$$eval(".benefit-item", (els) => els.length);
    console.log(`  Clinical Benefit items rendered: ${benefitCount}`);

    // Verify Login Form Header
    const loginHeader = await page.textContent(".auth-form-header h2");
    console.log(`  Form Header: "${loginHeader?.trim()}"`);

    // Verify Workspace is completely unmounted before authentication
    const welcomeInDOM = await page.$(".welcome-container");
    const navTabsInDOM = await page.$(".nav-tabs");
    console.log("  Welcome view in DOM before login:", Boolean(welcomeInDOM));
    console.log("  Navigation tabs in DOM before login:", Boolean(navTabsInDOM));

    if (authContainer && loginHeader?.includes("Welcome back") && !welcomeInDOM && !navTabsInDOM) {
      testResults.initialScreenIsLogin = "PASS";
      console.log("  1. Initial screen is dedicated Login page: PASS");
    } else {
      testResults.initialScreenIsLogin = "FAIL";
    }

    // -------------------------------------------------------------
    // 2. REGISTRATION NAVIGATION
    // -------------------------------------------------------------
    console.log("\n[TEST 2] Testing Navigation to Registration...");
    const createAccountBtn = await page.$(".auth-switch-link:has-text('Create an Account')");
    await createAccountBtn.click();
    await page.waitForTimeout(300);

    const regHeader = await page.textContent(".auth-form-header h2");
    console.log(`  Registration Header: "${regHeader?.trim()}"`);
    const hasRegInputs = await page.evaluate(() => {
      return (
        Boolean(document.querySelector("#reg-name")) &&
        Boolean(document.querySelector("#reg-email")) &&
        Boolean(document.querySelector("#reg-password")) &&
        Boolean(document.querySelector("#reg-confirm")) &&
        Boolean(document.querySelector("#reg-terms"))
      );
    });
    console.log("  All registration fields present:", hasRegInputs);

    if (regHeader?.includes("Create an Account") && hasRegInputs) {
      testResults.registrationNavigation = "PASS";
      console.log("  2. Registration navigation: PASS");
    } else {
      testResults.registrationNavigation = "FAIL";
    }

    // -------------------------------------------------------------
    // 3. PASSWORD VISIBILITY TOGGLES
    // -------------------------------------------------------------
    console.log("\n[TEST 3] Testing Password Visibility Controls...");
    await page.fill("#reg-password", "SecretPass123");
    let pwType = await page.$eval("#reg-password", (el) => el.type);
    console.log(`  Initial password input type: "${pwType}"`);

    const eyeBtn = await page.$(".auth-input-group:has(#reg-password) .auth-eye-btn");
    await eyeBtn.click();
    await page.waitForTimeout(100);
    let pwTypeToggled = await page.$eval("#reg-password", (el) => el.type);
    console.log(`  Toggled password input type: "${pwTypeToggled}"`);

    await eyeBtn.click();
    await page.waitForTimeout(100);
    let pwTypeRestored = await page.$eval("#reg-password", (el) => el.type);

    if (pwType === "password" && pwTypeToggled === "text" && pwTypeRestored === "password") {
      testResults.passwordVisibilityControls = "PASS";
      console.log("  3. Password visibility toggle: PASS");
    } else {
      testResults.passwordVisibilityControls = "FAIL";
    }

    // -------------------------------------------------------------
    // 4. PASSWORD CONFIRMATION MATCH INDICATOR
    // -------------------------------------------------------------
    console.log("\n[TEST 4] Testing Password Confirmation Matching...");
    await page.fill("#reg-confirm", "Mismatch123");
    await page.waitForTimeout(100);
    let matchText = await page.textContent(".auth-match-indicator");
    console.log(`  Mismatch text: "${matchText?.trim()}"`);

    await page.fill("#reg-confirm", "SecretPass123");
    await page.waitForTimeout(100);
    let matchTextCorrect = await page.textContent(".auth-match-indicator");
    console.log(`  Match text: "${matchTextCorrect?.trim()}"`);

    if (matchText?.includes("do not match") && matchTextCorrect?.includes("match")) {
      testResults.passwordMatchValidation = "PASS";
      console.log("  4. Password confirmation validation: PASS");
    } else {
      testResults.passwordMatchValidation = "FAIL";
    }

    // -------------------------------------------------------------
    // 5. REGISTRATION VALIDATION (TERMS REQUIRED)
    // -------------------------------------------------------------
    console.log("\n[TEST 5] Testing Registration Terms Enforcement...");
    await page.fill("#reg-name", "Dr. Automated Tester");
    await page.fill("#reg-email", "auto.tester@clinic.org");
    const regSubmitBtn = await page.$(".auth-form-card .auth-primary-btn");
    await regSubmitBtn.click();
    await page.waitForTimeout(200);

    const termsError = await page.textContent(".auth-error-banner");
    console.log(`  Validation Banner without terms: "${termsError?.trim()}"`);

    if (termsError?.includes("terms and educational disclaimer")) {
      testResults.termsEnforcement = "PASS";
      console.log("  5. Terms of use requirement enforcement: PASS");
    } else {
      testResults.termsEnforcement = "FAIL";
    }

    // -------------------------------------------------------------
    // 6. SUCCESSFUL REGISTRATION & SESSION INITIALIZATION
    // -------------------------------------------------------------
    console.log("\n[TEST 6] Testing Successful Account Registration...");
    const uniqueEmail = `evaluator.${Date.now()}@medical.org`;
    await page.fill("#reg-email", uniqueEmail);
    await page.fill("#reg-password", "ClinicalPass2026");
    await page.fill("#reg-confirm", "ClinicalPass2026");
    await page.check("#reg-terms");
    await regSubmitBtn.click();
    await page.waitForTimeout(600);

    // Verify Welcome view now renders
    const welcomeHero = await page.textContent(".welcome-title");
    console.log(`  Welcome Hero Title: "${welcomeHero?.trim()?.replace(/\s+/g, " ")}"`);
    const sessionBadge = await page.textContent(".user-session-badge");
    console.log(`  Session Badge text: "${sessionBadge?.trim()?.replace(/\s+/g, " ")}"`);

    if (welcomeHero?.includes("Understand your skin image") && sessionBadge?.includes("Dr. Automated Tester")) {
      testResults.registrationSuccess = "PASS";
      console.log("  6. Registration successfully logs in user: PASS");
    } else {
      testResults.registrationSuccess = "FAIL";
    }

    // -------------------------------------------------------------
    // 7. SESSION LOGOUT
    // -------------------------------------------------------------
    console.log("\n[TEST 7] Testing Sign Out Action...");
    const signOutBtn = await page.$(".session-signout-btn");
    await signOutBtn.click();
    await page.waitForTimeout(400);

    const loginHeaderAfterSignOut = await page.textContent(".auth-form-header h2");
    console.log(`  After Sign Out header: "${loginHeaderAfterSignOut?.trim()}"`);

    if (loginHeaderAfterSignOut?.includes("Welcome back")) {
      testResults.signOutReturnsToLogin = "PASS";
      console.log("  7. Sign Out returns user to Login: PASS");
    } else {
      testResults.signOutReturnsToLogin = "FAIL";
    }

    // -------------------------------------------------------------
    // 8. DUPLICATE ACCOUNT PREVENTION
    // -------------------------------------------------------------
    console.log("\n[TEST 8] Testing Duplicate Account Prevention...");
    await page.click(".auth-switch-link:has-text('Create an Account')");
    await page.waitForTimeout(200);
    await page.fill("#reg-name", "Duplicate Person");
    await page.fill("#reg-email", uniqueEmail); // same email as before
    await page.fill("#reg-password", "AnotherPass2026");
    await page.fill("#reg-confirm", "AnotherPass2026");
    await page.check("#reg-terms");
    await page.click(".auth-form-card .auth-primary-btn");
    await page.waitForTimeout(400);

    const dupError = await page.textContent(".auth-error-banner");
    console.log(`  Duplicate error message: "${dupError?.trim()}"`);

    if (dupError?.includes("already exists")) {
      testResults.duplicatePrevention = "PASS";
      console.log("  8. Duplicate registration blocked safely: PASS");
    } else {
      testResults.duplicatePrevention = "FAIL";
    }

    // Return to Login
    await page.click(".auth-switch-link:has-text('Sign In')");
    await page.waitForTimeout(200);

    // -------------------------------------------------------------
    // 9. INVALID LOGIN ERROR REPORTING
    // -------------------------------------------------------------
    console.log("\n[TEST 9] Testing Invalid Login Error Reporting...");
    await page.fill("#login-email", uniqueEmail);
    await page.fill("#login-password", "IncorrectPassword999");
    await page.click(".auth-fields-form .auth-primary-btn");
    await page.waitForTimeout(400);

    const loginErr = await page.textContent(".auth-error-banner");
    console.log(`  Login error for wrong password: "${loginErr?.trim()}"`);

    if (loginErr?.includes("Invalid email or password")) {
      testResults.invalidLoginGenericError = "PASS";
      console.log("  9. Generic error reported for invalid credentials: PASS");
    } else {
      testResults.invalidLoginGenericError = "FAIL";
    }

    // -------------------------------------------------------------
    // 10. SUCCESSFUL LOGIN WITH REGISTERED ACCOUNT
    // -------------------------------------------------------------
    console.log("\n[TEST 10] Testing Valid Login...");
    await page.fill("#login-email", uniqueEmail);
    await page.fill("#login-password", "ClinicalPass2026");
    await page.click(".auth-fields-form .auth-primary-btn");
    await page.waitForTimeout(600);

    const welcomeAfterLogin = await page.$(".welcome-container");
    const userBadgeAfterLogin = await page.textContent(".user-session-badge");
    console.log(`  Logged in badge: "${userBadgeAfterLogin?.trim()?.replace(/\s+/g, " ")}"`);

    if (welcomeAfterLogin && userBadgeAfterLogin?.includes("Dr. Automated Tester")) {
      testResults.loginSuccess = "PASS";
      console.log("  10. Successful login opens Welcome page with session: PASS");
    } else {
      testResults.loginSuccess = "FAIL";
    }

    // -------------------------------------------------------------
    // 11. SESSION RESTORATION ON BROWSER REFRESH
    // -------------------------------------------------------------
    console.log("\n[TEST 11] Testing Session Persistence on Refresh...");
    await page.reload({ waitUntil: "networkidle" });
    await page.waitForTimeout(400);

    const welcomeAfterReload = await page.$(".welcome-container");
    const badgeAfterReload = await page.textContent(".user-session-badge");
    console.log(`  Restored session on reload: "${badgeAfterReload?.trim()?.replace(/\s+/g, " ")}"`);

    if (welcomeAfterReload && badgeAfterReload?.includes("Dr. Automated Tester")) {
      testResults.sessionPersistenceOnReload = "PASS";
      console.log("  11. Active authenticated session restored on reload: PASS");
    } else {
      testResults.sessionPersistenceOnReload = "FAIL";
    }

    // Sign out to test guest and forgot password flows
    await page.click(".session-signout-btn");
    await page.waitForTimeout(400);

    // -------------------------------------------------------------
    // 12. FORGOT PASSWORD STATUS AND GUIDANCE
    // -------------------------------------------------------------
    console.log("\n[TEST 12] Testing Forgot Password Screen...");
    await page.click(".auth-link-text:has-text('Forgot Password?')");
    await page.waitForTimeout(200);

    const forgotTitle = await page.textContent(".auth-form-header h2");
    const calloutTitle = await page.textContent(".status-callout-text strong");
    console.log(`  Forgot Header: "${forgotTitle?.trim()}"`);
    console.log(`  Status Callout: "${calloutTitle?.trim()}"`);

    // Verify it does NOT claim an email was sent
    const formText = await page.textContent(".auth-form-card");
    const claimsEmailSent = formText?.includes("email has been sent") || formText?.includes("check your inbox");
    console.log("  Claims email was sent (must be false):", claimsEmailSent);

    // Return to sign in
    await page.click(".auth-primary-btn:has-text('Return to Sign In')");
    await page.waitForTimeout(200);

    if (calloutTitle?.includes("Unavailable") && !claimsEmailSent) {
      testResults.forgotPasswordInformative = "PASS";
      console.log("  12. Forgot password correctly labelled as unavailable: PASS");
    } else {
      testResults.forgotPasswordInformative = "FAIL";
    }

    // -------------------------------------------------------------
    // 13. GUEST ACCESS & DISCLAIMER ENFORCEMENT
    // -------------------------------------------------------------
    console.log("\n[TEST 13] Testing Guest Access & Disclaimer Enforcement...");
    const guestBtn = await page.$(".auth-guest-btn");
    await guestBtn.click();
    await page.waitForTimeout(300);

    const guestModal = await page.$(".demo-login-modal-box");
    console.log("  Guest modal opened:", Boolean(guestModal));

    // Try submitting without checking disclaimer
    const guestSubmit = await page.$(".guest-submit-btn");
    await guestSubmit.click();
    await page.waitForTimeout(200);

    const disclaimerErr = await page.textContent(".demo-error-banner");
    console.log(`  Disclaimer validation banner: "${disclaimerErr?.trim()}"`);

    // Now check disclaimer and enter
    await page.check("#guest-disclaimer-checkbox");
    await page.waitForTimeout(100);
    await guestSubmit.click();
    await page.waitForTimeout(500);

    const guestBadge = await page.textContent(".user-session-badge");
    console.log(`  Active Guest Badge: "${guestBadge?.trim()?.replace(/\s+/g, " ")}"`);

    if (disclaimerErr?.includes("educational evaluation") && guestBadge?.includes("Guest User")) {
      testResults.guestAccessWithDisclaimer = "PASS";
      console.log("  13. Guest access with disclaimer enforcement: PASS");
    } else {
      testResults.guestAccessWithDisclaimer = "FAIL";
    }

    // -------------------------------------------------------------
    // 14. GUEST REFRESH POLICY & LOGOUT
    // -------------------------------------------------------------
    console.log("\n[TEST 14] Testing Guest Session Exit...");
    await page.click(".session-signout-btn");
    await page.waitForTimeout(400);

    const loginAfterGuestExit = await page.$(".auth-page-container");
    console.log("  Returned to Login after Guest exit:", Boolean(loginAfterGuestExit));

    if (loginAfterGuestExit) {
      testResults.guestExitReturnsToLogin = "PASS";
      console.log("  14. Guest exit returns to Login: PASS");
    } else {
      testResults.guestExitReturnsToLogin = "FAIL";
    }

    // -------------------------------------------------------------
    // 15. WORKSPACE TAB NAVIGATION FROM AUTHENTICATED SESSION
    // -------------------------------------------------------------
    console.log("\n[TEST 15] Testing Workspace Workflows from Authenticated Session...");
    // Log back in as guest to check tabs
    await page.click(".auth-guest-btn");
    await page.waitForTimeout(200);
    await page.check("#guest-disclaimer-checkbox");
    await page.click(".guest-submit-btn");
    await page.waitForTimeout(400);

    // Navigate to Learn tab
    await page.click(".nav-tab-btn:has-text('Learn')");
    await page.waitForTimeout(300);
    const learnTitle = await page.textContent(".learn-header h2");
    console.log(`  Learn view title: "${learnTitle?.trim()}"`);

    // Navigate to Settings tab
    await page.click(".nav-tab-btn:has-text('Settings')");
    await page.waitForTimeout(300);
    const settingsTitle = await page.textContent(".settings-header h2");
    console.log(`  Settings view title: "${settingsTitle?.trim()}"`);

    // Navigate to Analyze tab
    await page.click(".nav-tab-btn:has-text('Analyze')");
    await page.waitForTimeout(300);
    const analyzeCard = await page.$(".analysis-card");
    console.log("  Analyze input card present:", Boolean(analyzeCard));

    if (learnTitle && settingsTitle && analyzeCard) {
      testResults.workspaceFeaturesFunctional = "PASS";
      console.log("  15. All workspace features remain fully functional: PASS");
    } else {
      testResults.workspaceFeaturesFunctional = "FAIL";
    }

    // Exit back to login for mobile test
    await page.click(".session-signout-btn");
    await page.waitForTimeout(300);

    // -------------------------------------------------------------
    // 16. MOBILE RESPONSIVE LAYOUT VERIFICATION (320px, 375px, 430px)
    // -------------------------------------------------------------
    console.log("\n[TEST 16] Testing Mobile Responsive Layouts on Auth Page...");
    let mobilePass = true;
    for (const width of [320, 375, 430]) {
      await page.setViewportSize({ width, height: 750 });
      await page.waitForTimeout(200);

      const overflow = await page.evaluate(() => {
        const docW = document.documentElement.scrollWidth;
        const winW = window.innerWidth;
        const card = document.querySelector(".auth-card-wrapper");
        const cardRect = card ? card.getBoundingClientRect() : null;
        return {
          hasOverflow: docW > winW,
          docW,
          winW,
          cardWidth: cardRect ? Math.round(cardRect.width) : null,
        };
      });

      console.log(
        `  Viewport ${width}px: docWidth=${overflow.docW} <= winWidth=${overflow.winW}, cardWidth=${overflow.cardWidth}px (overflow: ${overflow.hasOverflow})`
      );

      if (overflow.hasOverflow) {
        mobilePass = false;
      }
    }

    if (mobilePass) {
      testResults.mobileLayoutPass = "PASS";
      console.log("  16. Mobile layouts (320px, 375px, 430px) pass with 0px overflow: PASS");
    } else {
      testResults.mobileLayoutPass = "FAIL";
    }

  } catch (err) {
    console.error("Test execution failed with error:", err);
  } finally {
    await browser.close();
  }

  console.log("\n=================================================");
  console.log("AUTH-UI-02 TEST SUMMARY");
  console.log("=================================================");
  console.log(JSON.stringify(testResults, null, 2));

  const allPassed = Object.values(testResults).every((v) => v === "PASS");
  if (!allPassed) {
    process.exit(1);
  }
}

runAuthUITests();
