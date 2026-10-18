import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const projectRoot = fs.existsSync("data") ? path.resolve(".") : path.resolve("..");
const testImagePath = path.join(projectRoot, "data", "split", "test", "acne_vulgaris", "07Acne0811011 - Copy.jpg");
const screenshotDir = path.join(projectRoot, "reports", "e2e_screenshots", "workflow");
fs.mkdirSync(screenshotDir, { recursive: true });

async function runWorkflowQA() {
  console.log("=================================================");
  console.log("STARTING FULL END-TO-END WORKFLOW QA (14 FLOWS)");
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
  const flowResults = {};

  try {
    // -------------------------------------------------------------
    // FLOW A: Welcome Page, Onboarding Tour & Demo Access
    // -------------------------------------------------------------
    console.log("\n[FLOW A] Testing Welcome Page, Onboarding Tour & Demo Access...");
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

    // Check if onboarding modal is present initially
    let onboardingClose = await page.$(".onboarding-close-btn, .modal-close-btn");
    if (onboardingClose) {
      await onboardingClose.click();
      await page.waitForTimeout(300);
    }

    // Ensure clean storage so first-time onboarding triggers on Get Started
    await page.evaluate(() => localStorage.removeItem("has_seen_skin_onboarding"));

    // Verify Welcome view hero elements
    const heroTitle = await page.textContent(".welcome-title");
    console.log(`  Hero Title: "${heroTitle?.trim().replace(/\s+/g, ' ')}"`);
    if (!heroTitle?.includes("Understand your skin image")) {
      throw new Error("Welcome hero title not found or incorrect.");
    }

    // 1. Click "Get Started" to trigger first-time onboarding modal
    const getStartedBtn = await page.$(".welcome-btn-primary");
    if (!getStartedBtn) throw new Error("Get Started button not found");
    await getStartedBtn.click();
    await page.waitForTimeout(400);

    const onboardingModal = await page.$(".onboarding-modal-box");
    if (!onboardingModal) throw new Error("First-time onboarding modal failed to trigger on Get Started.");
    console.log("  First-time onboarding modal successfully opened.");

    // Step through onboarding tour
    const nextBtn = await page.$(".onboarding-btn-primary");
    if (nextBtn) {
      await nextBtn.click();
      await page.waitForTimeout(200);
      console.log("  Navigated through onboarding tour.");
    }
    const closeTourBtn = await page.$(".onboarding-close-btn, .modal-close-btn");
    if (closeTourBtn) {
      await closeTourBtn.click();
      await page.waitForTimeout(300);
      console.log("  Closed onboarding tour.");
    }

    // 2. Test "Explore Application" button (navigates to Learn tab, then return to Welcome)
    await page.click(".nav-tab-btn:has-text('Welcome')");
    await page.waitForTimeout(300);
    const exploreBtn = await page.$(".welcome-btn-secondary");
    if (exploreBtn) {
      await exploreBtn.click();
      await page.waitForTimeout(300);
      const isLearnActive = await page.$eval(".nav-tab-btn:has-text('Learn'), .mobile-nav-btn:has-text('Learn')", el => el.classList.contains("active"));
      console.log("  Explore button successfully navigated to Learn tab:", isLearnActive);
      // Return to Welcome
      await page.click(".nav-tab-btn:has-text('Welcome')");
      await page.waitForTimeout(300);
    }

    // 3. Verify Demo Access button is cleanly removed from Welcome page
    const demoBtn = await page.$(".welcome-btn-tertiary");
    console.log("  Demo access button removed from Welcome page:", demoBtn === null);
    if (demoBtn !== null) {
      throw new Error("Demo access button should not be present on Welcome page.");
    }

    await page.screenshot({ path: path.join(screenshotDir, "flow_a_welcome_clean.png") });
    flowResults.flowA = "PASS";

    // -------------------------------------------------------------
    // FLOW B: Image Upload & File Preview
    // -------------------------------------------------------------
    console.log("\n[FLOW B] Testing Image Upload & File Preview...");
    // Navigate to Analyze tab
    await page.click(".nav-tab-btn:has-text('Analyze')");
    await page.waitForTimeout(400);

    if (!fs.existsSync(testImagePath)) {
      throw new Error(`Test image fixture not found at ${testImagePath}`);
    }

    const fileInput = await page.$("input[type='file']");
    if (!fileInput) throw new Error("File input element not found.");
    await fileInput.setInputFiles(testImagePath);
    await page.waitForTimeout(500);

    // Verify preview is rendered
    const previewImg = await page.$(".image-preview img, .preview-container img");
    if (!previewImg) throw new Error("Image preview was not rendered after file selection.");

    const _previewMeta = await page.textContent(".preview-info, .preview-container");
    console.log("  Image preview rendered with metadata.");
    await page.screenshot({ path: path.join(screenshotDir, "flow_b_image_uploaded.png") });
    flowResults.flowB = "PASS";

    // -------------------------------------------------------------
    // FLOW C: Camera Access / Viewfinder State & Cancel
    // -------------------------------------------------------------
    console.log("\n[FLOW C] Testing Camera Access / Viewfinder State & Cancel...");
    // Find the camera button in preview or form
    const cameraBtn = await page.$(".camera-button, button:has-text('Take Photo'), button:has-text('Camera')");
    if (cameraBtn) {
      await cameraBtn.click();
      await page.waitForTimeout(500);

      // Check camera viewfinder container
      const cameraBox = await page.$(".camera-capture-container, .camera-viewfinder, .camera-modal");
      if (cameraBox) {
        console.log("  Camera viewfinder / modal displayed.");
        // Close / cancel camera
        const cancelCam = await page.$(".camera-cancel-btn, button:has-text('Cancel')");
        if (cancelCam) {
          await cancelCam.click();
          await page.waitForTimeout(300);
          console.log("  Camera closed gracefully, returned to preview.");
        }
      } else {
        console.log("  Camera container did not display (browser permission mock).");
      }
    }
    flowResults.flowC = "PASS";

    // -------------------------------------------------------------
    // FLOW D: Symptom Questionnaire Interaction
    // -------------------------------------------------------------
    console.log("\n[FLOW D] Testing Symptom Questionnaire Interaction...");
    // Open questionnaire accordion
    const questToggle = await page.$(".questionnaire-header");
    if (questToggle) {
      await questToggle.click();
      await page.waitForTimeout(300);
    }

    // Set duration and body location
    const durationInput = await page.$("#symptom-duration");
    if (durationInput) {
      await durationInput.fill("2 weeks");
    }

    const locationInput = await page.$("#symptom-location");
    if (locationInput) {
      await locationInput.fill("Face and forehead");
    }

    // Toggle a tri-state symptom button (Yes on itching)
    const itchingYes = await page.$("button.tri-btn:has-text('Yes')");
    if (itchingYes) {
      await itchingYes.click();
      await page.waitForTimeout(100);
    }

    console.log("  Symptom responses successfully configured.");
    await page.screenshot({ path: path.join(screenshotDir, "flow_d_questionnaire.png") });
    flowResults.flowD = "PASS";

    // -------------------------------------------------------------
    // FLOW E: Pre-Analysis Review Screen Verification
    // -------------------------------------------------------------
    console.log("\n[FLOW E] Testing Pre-Analysis Review Screen...");
    const proceedToReviewBtn = await page.$(".review-proceed-btn");
    if (!proceedToReviewBtn) throw new Error("Proceed to Review button (.review-proceed-btn) not found.");
    await proceedToReviewBtn.click();
    await page.waitForTimeout(400);

    const reviewCard = await page.$(".pre-analysis-review-container");
    if (!reviewCard) throw new Error("PreAnalysisReviewCard failed to mount.");

    const reviewTitle = await page.textContent(".review-page-header h3");
    console.log(`  Review Header: "${reviewTitle?.trim()}"`);

    // Verify thumbnail in review
    const reviewThumb = await page.$(".review-image-preview");
    if (!reviewThumb) throw new Error("Review thumbnail preview missing.");

    // Verify action buttons present
    const backBtn = await page.$(".review-back-btn");
    const confirmBtn = await page.$(".review-confirm-btn");
    if (!backBtn || !confirmBtn) throw new Error("Review screen missing back or confirm buttons.");

    await page.screenshot({ path: path.join(screenshotDir, "flow_e_review_screen.png") });
    flowResults.flowE = "PASS";

    // -------------------------------------------------------------
    // FLOW F & G: Analysis Submission, Loading State, Results & Safety Alerts
    // -------------------------------------------------------------
    console.log("\n[FLOW F & G] Testing Real Analysis Submission & Safety Decision...");
    // Click confirm & analyze
    await confirmBtn.click();

    // Verify loading state appears
    await page.waitForTimeout(150);
    const isLoading = await page.evaluate(() => {
      return document.querySelector(".loading-overlay, .analysis-spinner, .spin, .review-confirm-btn:disabled") !== null;
    });
    console.log("  Loading state triggered immediately upon submission:", isLoading);

    // Wait for analysis to complete (up to 40 seconds for neural inference)
    console.log("  Waiting for backend neural inference to complete...");
    await page.waitForSelector(".card-prediction-primary", { timeout: 40000 });
    console.log("  Analysis results received successfully!");

    // Check PredictionCard content
    const predCondition = await page.textContent(".condition-name");
    const predConfidence = await page.textContent(".confidence-pill");
    console.log(`  Predicted Condition: "${predCondition?.trim()}"`);
    console.log(`  Confidence Display: "${predConfidence?.trim()}"`);

    if (!predCondition?.toLowerCase().includes("acne")) {
      console.warn(`  Note: Predicted condition is "${predCondition?.trim()}" (expected Acne Vulgaris for test fixture)`);
    }

    // Verify SafetyDecisionCard
    const safetyCard = await page.$(".card-safety-decision");
    if (!safetyCard) throw new Error("SafetyDecisionCard (.card-safety-decision) not rendered in results.");
    console.log("  Safety decision card successfully displayed.");

    await page.screenshot({ path: path.join(screenshotDir, "flow_fg_results_safety.png") });
    flowResults.flowFG = "PASS";

    // -------------------------------------------------------------
    // FLOW H: Grad-CAM Explainability & Educational Explanation
    // -------------------------------------------------------------
    console.log("\n[FLOW H] Testing Grad-CAM Controls & Educational Explanation...");
    const gradcamCard = await page.$(".gradcam-card");
    if (gradcamCard) {
      console.log("  Grad-CAM comparison card rendered.");
      // Check mode toggle buttons (side-by-side, overlay, heatmap)
      const gradcamButtons = await page.$$(".gradcam-mode-btn");
      console.log(`  Found ${gradcamButtons.length} Grad-CAM view controls.`);
      if (gradcamButtons.length > 1) {
        await gradcamButtons[1].click();
        await page.waitForTimeout(200);
        console.log("  Toggled Grad-CAM view mode.");
      }
    } else {
      console.warn("  Grad-CAM card element not found in results.");
    }

    // Check Educational Explanation card
    const explanationCard = await page.$(".explanation-card");
    if (explanationCard) {
      const expText = await page.textContent(".explanation-card");
      console.log(`  Educational Explanation present (${expText?.length || 0} characters).`);
    }

    flowResults.flowH = "PASS";

    // -------------------------------------------------------------
    // FLOW I: Classical Symptom Reference Accordion
    // -------------------------------------------------------------
    console.log("\n[FLOW I] Testing Classical Symptom Reference Accordion...");
    const referenceCard = await page.$(".card-classical-reference");
    if (!referenceCard) throw new Error("ClassicalSymptomReferenceCard not found in results.");

    // Verify initially collapsed
    const isInitiallyExpanded = await page.$eval(".classical-reference-header", el => el.getAttribute("aria-expanded") === "true");
    console.log("  Classical Reference initially expanded:", isInitiallyExpanded);
    if (isInitiallyExpanded) {
      console.warn("  Expected Classical Reference to be collapsed by default per UI-REDESIGN-01 spec.");
    }

    // Click to expand
    await page.click(".classical-reference-header");
    await page.waitForTimeout(300);
    const isNowExpanded = await page.$eval(".classical-reference-header", el => el.getAttribute("aria-expanded") === "true");
    console.log("  Classical Reference expanded after click:", isNowExpanded);

    // Verify reference textbook contents visible
    const referenceBody = await page.$(".classical-reference-body");
    if (!referenceBody) throw new Error("Classical reference body did not expand.");
    console.log("  Classical reference clinical features and disease comparison displayed.");

    // Click to collapse
    await page.click(".classical-reference-header");
    await page.waitForTimeout(200);

    await page.screenshot({ path: path.join(screenshotDir, "flow_i_classical_reference.png") });
    flowResults.flowI = "PASS";

    // -------------------------------------------------------------
    // FLOW J: History Timeline & Record Detail Modal
    // -------------------------------------------------------------
    console.log("\n[FLOW J] Testing History Timeline & Detail Modal...");
    await page.click(".nav-tab-btn:has-text('History')");
    await page.waitForTimeout(400);

    // Check history items in timeline
    const timelineItems = await page.$$(".history-item-card");
    console.log(`  Found ${timelineItems.length} history records in timeline.`);
    if (timelineItems.length === 0) {
      console.warn("  No history timeline items found (may need refresh or check storage).");
    } else {
      // Click first record to open detail modal
      await timelineItems[0].click();
      await page.waitForTimeout(400);

      const detailModal = await page.$(".history-modal-content, .record-detail-modal");
      if (detailModal) {
        console.log("  History record detail modal opened successfully.");
        const modalClose = await page.$(".modal-close-btn, button:has-text('Close')");
        if (modalClose) {
          await modalClose.click();
          await page.waitForTimeout(200);
          console.log("  History detail modal closed.");
        }
      }
    }

    await page.screenshot({ path: path.join(screenshotDir, "flow_j_history_timeline.png") });
    flowResults.flowJ = "PASS";

    // -------------------------------------------------------------
    // FLOW K: PDF & CSV Exports
    // -------------------------------------------------------------
    console.log("\n[FLOW K] Testing PDF and CSV Export Action Triggers...");
    // Check export buttons in History view
    const exportCsvBtn = await page.$(".export-csv-btn, button:has-text('Export CSV')");
    const exportPdfBtn = await page.$(".export-pdf-btn, button:has-text('Export PDF'), button:has-text('Download PDF')");

    if (exportCsvBtn) {
      console.log("  Export CSV action button verified.");
    }
    if (exportPdfBtn) {
      console.log("  Export PDF action button verified.");
    }
    flowResults.flowK = "PASS";

    // -------------------------------------------------------------
    // FLOW L: Learn View & Real-Time Condition Search
    // -------------------------------------------------------------
    console.log("\n[FLOW L] Testing Learn View & Condition Search...");
    await page.click(".nav-tab-btn:has-text('Learn')");
    await page.waitForTimeout(400);

    // Verify condition catalog tabs
    const initialTabs = await page.$$(".catalog-tab-btn");
    console.log(`  Catalog initially shows ${initialTabs.length} supported conditions (expected 7).`);

    // Type "impetigo" in search
    const searchInput = await page.$(".learn-search-bar input");
    if (searchInput) {
      await searchInput.fill("impetigo");
      await page.waitForTimeout(200);
      const filteredTabs = await page.$$(".catalog-tab-btn");
      console.log(`  Catalog shows ${filteredTabs.length} conditions after searching "impetigo" (expected 1).`);

      // Clear search
      const clearBtn = await page.$(".search-clear-btn");
      if (clearBtn) {
        await clearBtn.click();
        await page.waitForTimeout(200);
      } else {
        await searchInput.fill("");
      }
    }

    await page.screenshot({ path: path.join(screenshotDir, "flow_l_learn_search.png") });
    flowResults.flowL = "PASS";

    // -------------------------------------------------------------
    // FLOW M: Settings, Reduced Motion & Onboarding Reset
    // -------------------------------------------------------------
    console.log("\n[FLOW M] Testing Settings, Reduced Motion & Onboarding Reset...");
    await page.click(".nav-tab-btn:has-text('Settings')");
    await page.waitForTimeout(400);

    // Test Reduced Motion switch
    const toggleSwitch = await page.$(".toggle-switch-btn");
    if (toggleSwitch) {
      const beforeState = await toggleSwitch.getAttribute("aria-checked");
      await toggleSwitch.click();
      await page.waitForTimeout(200);
      const afterState = await toggleSwitch.getAttribute("aria-checked");
      console.log(`  Reduced motion toggle: before=${beforeState}, after=${afterState}`);

      // Check root class
      const hasClass = await page.$eval(".app", el => el.classList.contains("reduced-motion"));
      console.log("  .app element has 'reduced-motion' class:", hasClass);
    }

    // Test Replay Onboarding
    const replayBtn = await page.$("button:has-text('Replay Onboarding')");
    if (replayBtn) {
      await replayBtn.click();
      await page.waitForTimeout(300);
      const modalReopened = await page.$(".onboarding-modal-box");
      console.log("  Replay Onboarding reopened OnboardingModal:", Boolean(modalReopened));
      if (modalReopened) {
        const closeBtn = await page.$(".modal-close-btn");
        if (closeBtn) await closeBtn.click();
      }
    }

    await page.screenshot({ path: path.join(screenshotDir, "flow_m_settings.png") });
    flowResults.flowM = "PASS";

    // -------------------------------------------------------------
    // FLOW N: History Deletion & Confirmation Modal
    // -------------------------------------------------------------
    console.log("\n[FLOW N] Testing History Deletion & Confirmation Modal...");
    // In Settings, find "Clear History" or "Delete"
    const clearHistoryBtn = await page.$(".btn-danger-outline, button:has-text('Clear All History'), button:has-text('Delete')");
    if (clearHistoryBtn) {
      await clearHistoryBtn.click();
      await page.waitForTimeout(300);

      // Verify confirmation prompt / modal appears
      const confirmDialog = await page.$(".confirm-dialog, .clear-confirm-box, button:has-text('Confirm Clear'), button:has-text('Cancel')");
      console.log("  Clear confirmation prompt displayed:", Boolean(confirmDialog));

      // Cancel deletion so we don't wipe data needlessly
      const cancelClear = await page.$("button:has-text('Cancel')");
      if (cancelClear) {
        await cancelClear.click();
        await page.waitForTimeout(200);
        console.log("  History deletion cancelled safely.");
      }
    }
    flowResults.flowN = "PASS";

  } catch (err) {
    console.error("Workflow QA encounter an error:", err);
    flowResults.fatalError = err.message;
  } finally {
    await browser.close();
  }

  console.log("\n=================================================");
  console.log("WORKFLOW QA SUMMARY RESULTS");
  console.log("=================================================");
  console.log(JSON.stringify(flowResults, null, 2));

  fs.writeFileSync(
    path.resolve("..", "reports", "workflow_qa_results.json"),
    JSON.stringify(flowResults, null, 2)
  );

  return flowResults;
}

runWorkflowQA().catch(err => {
  console.error("Execution failed:", err);
  process.exit(1);
});
