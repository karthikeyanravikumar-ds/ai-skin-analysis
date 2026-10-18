import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const projectRoot = fs.existsSync("data") ? path.resolve(".") : path.resolve("..");
const testImagePath = path.join(projectRoot, "data", "split", "test", "acne_vulgaris", "07Acne0811011 - Copy.jpg");

async function testSmallMobileLayout() {
  console.log("=================================================");
  console.log("TESTING ALL STATES AT 320px & 360px VIEWPORTS");
  console.log("=================================================");

  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
  });

  for (const width of [320, 360]) {
    console.log(`\n--- Testing width: ${width}px ---`);
    const context = await browser.newContext({
      viewport: { width, height: 700 },
      deviceScaleFactor: 1
    });

    const page = await context.newPage();
    await page.goto("http://localhost:5173", { waitUntil: "networkidle" });

    // Dismiss any modal
    const closeBtn = await page.$(".modal-close-btn");
    if (closeBtn) await closeBtn.click();

    // Check helper for overflow
    const checkOverflow = async (stage) => {
      const info = await page.evaluate(() => {
        const docW = document.documentElement.scrollWidth;
        const winW = window.innerWidth;
        const bodyW = document.body.scrollWidth;
        const hasOverflow = docW > winW || bodyW > winW;
        let offenders = [];
        if (hasOverflow) {
          const els = Array.from(document.querySelectorAll("*"));
          for (const el of els) {
            const rect = el.getBoundingClientRect();
            if (rect.right > winW + 1) {
              const tag = el.tagName.toLowerCase();
              const cls = el.className && typeof el.className === "string" ? `.${el.className.split(" ").join(".")}` : "";
              offenders.push({
                selector: `${tag}${cls}`,
                right: Math.round(rect.right),
                width: Math.round(rect.width)
              });
            }
          }
        }
        return { hasOverflow, docW, winW, bodyW, offenders: offenders.slice(0, 5) };
      }, width);

      if (info.hasOverflow) {
        console.warn(`  [OVERFLOW] At stage "${stage}" (${width}px): docW=${info.docW} > winW=${info.winW}`);
        console.warn(`    Offenders:`, info.offenders);
      } else {
        console.log(`  [OK] Stage "${stage}" (${width}px): docW=${info.docW} <= winW=${info.winW}`);
      }
      return info;
    };

    // 1. Welcome tab
    await checkOverflow("Welcome Page");

    // Test Demo Login Modal
    const demoBtn = await page.$(".welcome-btn-tertiary");
    if (demoBtn) {
      await demoBtn.click();
      await page.waitForTimeout(300);
      await checkOverflow("Demo Login Modal");
      const demoClose = await page.$(".modal-close-btn");
      if (demoClose) await demoClose.click();
    }

    // 2. Analyze tab (Empty state)
    await page.click(".mobile-nav-btn:has-text('Analyze')");
    await page.waitForTimeout(300);
    await checkOverflow("Analyze Tab (Empty)");

    // 3. Upload image
    const fileInput = await page.$("input[type='file']");
    await fileInput.setInputFiles(testImagePath);
    await page.waitForTimeout(400);
    await checkOverflow("Analyze Tab (Image Preview)");

    // 4. Open Questionnaire
    const questHdr = await page.$(".questionnaire-header");
    if (questHdr) {
      await questHdr.click();
      await page.waitForTimeout(300);
      await checkOverflow("Analyze Tab (Questionnaire Open)");
    }

    // 5. Pre-Analysis Review Card
    const reviewBtn = await page.$(".review-proceed-btn");
    if (reviewBtn) {
      await reviewBtn.click();
      await page.waitForTimeout(400);
      await checkOverflow("Pre-Analysis Review Screen");

      // 6. Confirm & Analyze to get Results
      const confirmBtn = await page.$(".review-confirm-btn");
      if (confirmBtn) {
        await confirmBtn.click();
        await page.waitForSelector(".card-prediction-primary", { timeout: 40000 });
        await checkOverflow("Results Screen");

        // Expand Classical Reference
        const classRefHdr = await page.$(".classical-reference-header");
        if (classRefHdr) {
          await classRefHdr.click();
          await page.waitForTimeout(300);
          await checkOverflow("Results with Classical Reference Expanded");
        }
      }
    }

    // 7. History tab
    await page.click(".mobile-nav-btn:has-text('History')");
    await page.waitForTimeout(400);
    await checkOverflow("History Tab (Timeline)");

    // Open mobile filter drawer
    const filterToggle = await page.$(".mobile-filters-toggle-btn");
    if (filterToggle) {
      await filterToggle.click();
      await page.waitForTimeout(300);
      await checkOverflow("History Tab (Mobile Filter Drawer)");
    }

    // Open History Detail Modal
    const histItem = await page.$(".history-item-card");
    if (histItem) {
      await histItem.click();
      await page.waitForTimeout(400);
      await checkOverflow("History Record Detail Modal");
      const modalClose = await page.$(".modal-close-btn");
      if (modalClose) await modalClose.click();
    }

    // 8. Learn tab
    await page.click(".mobile-nav-btn:has-text('Learn')");
    await page.waitForTimeout(300);
    await checkOverflow("Learn Tab");

    // 9. Settings tab
    await page.click(".mobile-nav-btn:has-text('Settings')");
    await page.waitForTimeout(300);
    await checkOverflow("Settings Tab");

    await context.close();
  }

  await browser.close();
  console.log("Small mobile layout check finished.");
}

testSmallMobileLayout().catch(err => {
  console.error(err);
  process.exit(1);
});
