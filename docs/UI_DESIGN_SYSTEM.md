# UI Design System: Clinical Minimalism Meets Editorial Healthcare Design

## 1. Visual Identity & Art Direction
The AI Skin Analysis application is designed as an educational, safety-focused, and non-diagnostic clinical guidance tool. The interface intentionally abandons generic AI dashboard aesthetics (no glowing purple/blue gradients, no neon buttons, no pseudo-metrics, no fake health scores) in favor of **calm, trustworthy, precision-engineered editorial healthcare design**.

### Key Principles
- **Clarity over Decoration**: Whitespace, crisp typography hierarchy, and subtle neutral borders replace decorative shadows and floating cards.
- **Dermatological Equity**: Color coding never implies clinical certainty or diagnostic finality. High model confidence is presented factually, not celebrated with glowing green banners.
- **Safety First**: Red flags and urgent triage guidance occupy top visual precedence with high-contrast, accessible emergency indicators.
- **Deterministic Transparency**: Non-diagnostic disclaimers, explainability (Grad-CAM), and image quality limitations are permanently visible and clearly contextualized.

---

## 2. Design Tokens

### 2.1 Color Palette
```css
:root {
  /* Primary Healthcare Brand */
  --color-primary-forest: #245C4F;
  --color-primary-forest-dark: #193F37;
  --color-primary-surface: #EAF2EE;
  --color-primary-muted: #D7E5DD;

  /* Surfaces & Backgrounds */
  --color-bg-main: #F7F8F6;
  --color-bg-secondary: #F0F3F0;
  --color-bg-card: #FFFFFF;
  --color-border: #E1E6E1;
  --color-border-subtle: #ECEFEA;

  /* Typography */
  --color-text-primary: #202824;
  --color-text-secondary: #69736D;
  --color-text-muted: #818A84;

  /* Interaction & Focus */
  --color-focus-ring: rgba(36, 92, 79, 0.4);
  --color-selection: #EAF2EE;

  /* Clinical Status & Safety Tiers */
  --color-status-routine-bg: #EAF2EE;
  --color-status-routine-text: #245C4F;
  --color-status-routine-border: #B7D1C4;

  --color-status-attention-bg: #FEF7EC;
  --color-status-attention-text: #8A5A12;
  --color-status-attention-border: #F6DFB6;

  --color-status-urgent-bg: #FEF3F2;
  --color-status-urgent-text: #B42318;
  --color-status-urgent-border: #FECDCA;
}
```

### 2.2 Typography Scale
- **Font Family**: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Page Headings (h1 / h2)**: 30–36px desktop (clamp `28px, 4vw, 36px`), line-height: 1.15, font-weight: 700.
- **Section Headings (h3)**: 20–24px, line-height: 1.25, font-weight: 600.
- **Component Headings (h4 / h5)**: 16–18px, line-height: 1.35, font-weight: 600.
- **Body Regular**: 14–16px, line-height: 1.6, font-weight: 400.
- **Supporting / Small Text**: 12–13px, line-height: 1.5, font-weight: 400.
- **Eyebrow / Category Tags**: 11–12px, letter-spacing: 0.05em, text-transform: uppercase, font-weight: 600.

### 2.3 Spacing, Borders, and Elevation
- **Spacing Grid**: 4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px, 64px.
- **Max Content Width**: 1180px with fluid gutter (min 16px, ideal 24px–32px).
- **Corner Radii**:
  - Buttons & Inputs: 8px.
  - Component Cards & Panels: 12px–14px.
  - Modals & Viewfinders: 14px–16px.
  - Pills & Badges: 9999px (pill-shaped).
- **Elevation**:
  - Flat base: border `1px solid var(--color-border)`.
  - Subtle Hover: `0 4px 16px rgba(32, 40, 36, 0.04)`.
  - Modal / Overlay: `0 16px 48px rgba(32, 40, 36, 0.12)`.

---

## 3. Screen Architecture & Navigation
1. **Application Shell (`AppHeader` + Navigation Bar)**:
   - Wordmark: "AI Skin Analysis" with subtle sub-brand "Clinical Guidance & Education".
   - Top Navigation Tabs:
     - **Analyze**: Guided photo input, questionnaire, and inference workflow.
     - **History**: Local session repository with multi-attribute filtering & export.
     - **Learn**: Clinical educational knowledge library explaining the 7 classes, Grad-CAM, image quality, and limitations.
     - **Settings & Privacy**: Local retention controls, audit info, and disclaimer.
   - Status Indicator: Calibrated system status ("System Ready • EfficientNet-B0 v2.0").

2. **Step-by-Step Guided Analysis Workflow**:
   - Step 1: Input Selection (Upload or Live Viewfinder).
   - Step 2: Quality Coaching & Best Practices.
   - Step 3: Contextual Symptom Questionnaire (Optional tri-state answers).
   - Step 4: Submission & Deterministic Safety Gate.
   - Step 5: Results & Explainability (Urgent Alert -> Prediction / OOD Abstention -> Safety Triage -> Top Predictions -> Grad-CAM Attention -> Quality Verification -> Educational Knowledge).

3. **History & Reporting**:
   - Filter bar: Class, Safety Tier, Clinical Decision, and Confidence.
   - Records list with clear timestamps, class labels, and safety chips.
   - Full Detail View Modal with keyboard accessibility (`Esc` close).
   - Direct publication-quality PDF report generation & sanitized CSV download.

4. **Learn & Educational Hub**:
   - Condition primer on the 7 supported classes.
   - Guide to interpreting Grad-CAM visual attention.
   - Understanding model confidence vs. clinical diagnosis.
   - Red-flag symptoms and emergency triage instructions.

5. **Settings & Privacy**:
   - On-device data handling principles.
   - Zero-server raw image retention verification.
   - Local history management (Clear all records).
