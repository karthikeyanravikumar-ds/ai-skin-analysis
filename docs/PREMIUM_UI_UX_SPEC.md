# Figma-Ready Specification: Premium Medical UI/UX Design System
**Project**: AI-Assisted Skin Image Analysis System  
**Document ID**: `docs/PREMIUM_UI_UX_SPEC.md`  
**Version**: 2.0 (Mobile-First Clinical Minimalism)  
**Target Viewports**: 320px, 360px, 375px, 390px, 430px, 768px, 1024px, 1280px, 1440px+

---

## 1. Design Direction & Core Philosophy

The AI Skin Analysis platform is an educational and clinical triage assistance tool designed according to **Clinical Minimalism**. The interface prioritizes calm authority, precision, and dermatological safety over decorative SaaS trends.

### Core Principles
1. **Clinical Responsibility Over Novelty**: No pseudo-medical health scores, glowing AI gradients, or decorative animations. High confidence is stated objectively, not celebrated.
2. **Mobile-First Utility**: Healthcare providers and users frequently capture images and review triage alerts on mobile devices. Every screen is engineered for one-handed thumb reach, zero horizontal scrolling, and touch targets $\ge 44 \times 44\text{px}$.
3. **Deterministic Safety Hierarchy**: Red-flag emergency symptoms (fever, cellulitis spread, mucosal lesions, breathing difficulty) always take supreme visual priority over mathematical CNN probabilities.
4. **Progressive Disclosure & Text Discipline**: Secondary explanations and extensive reference matrices are accessible on demand via collapsibles and tabs rather than forcing users to scroll past walls of text.

---

## 2. Design Tokens

### 2.1 Color Palette
```css
:root {
  /* Brand Primary */
  --color-primary-forest: #245C4F;       /* Primary interactive, main branding */
  --color-primary-forest-dark: #193F37;  /* Hover / active states, high-contrast headings */
  --color-primary-surface: #EAF2EE;      /* Selected tab backgrounds, icon containers */
  --color-primary-muted: #D7E5DD;        /* Subtle green borders and dividers */

  /* Neutral Surfaces & Backgrounds */
  --color-bg-main: #F7F8F6;              /* Soft clinical off-white canvas */
  --color-bg-secondary: #F0F3F0;         /* Segmented control backgrounds, light cards */
  --color-bg-card: #FFFFFF;              /* Primary white content surface */
  --color-border: #E1E6E1;               /* Structural component borders */
  --color-border-subtle: #ECEFEA;        /* Inner dividers and inactive lines */

  /* Typography */
  --color-text-primary: #202824;         /* High-contrast headings and primary text */
  --color-text-secondary: #69736D;       /* Subheadings, labels, secondary information */
  --color-text-muted: #818A84;           /* Metadata, timestamps, footnote text */

  /* Interaction & Focus */
  --color-focus-ring: rgba(36, 92, 79, 0.45);
  --color-selection: #EAF2EE;

  /* Safety & Clinical Tiers */
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
- **Font Stack**: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **H1 (Page Title)**: Desktop `32px` (line-height 1.2, weight 700) | Mobile `24px` (line-height 1.25)
- **H2 (Section Header)**: Desktop `24px` (line-height 1.3, weight 600) | Mobile `20px` (line-height 1.35)
- **H3 (Card Title)**: Desktop `18px` (line-height 1.35, weight 600) | Mobile `16px` (line-height 1.4)
- **H4 (Sub-component / Label)**: `14px` - `15px` (line-height 1.4, weight 600)
- **Body Regular**: `14px` (line-height 1.6, weight 400)
- **Body Small / Meta**: `12px` - `13px` (line-height 1.5, weight 400)
- **Eyebrow / Badge**: `11px` (line-height 1.2, weight 700, letter-spacing `0.06em`, uppercase)

### 2.3 Spacing Grid & Dimensions
- **Spacing Units**: `4px`, `8px`, `12px`, `16px`, `20px`, `24px`, `32px`, `48px`
- **Container Max-Width**: `1140px` (desktop centered)
- **Corner Radii**:
  - Buttons & Inputs: `8px`
  - Component Cards & Panels: `12px` - `14px`
  - Modals & Viewfinders: `16px`
  - Status Pills & Badges: `9999px`
- **Elevation**:
  - Card Default: `0 1px 3px rgba(32, 40, 36, 0.04)` with `1px solid var(--color-border)`
  - Card Hover (interactive): `0 4px 12px rgba(32, 40, 36, 0.06)`
  - Modal / Sheet: `0 16px 48px rgba(32, 40, 36, 0.14)`

---

## 3. Responsive Breakpoints

| Breakpoint Tier | Viewport Range | Layout Configuration |
| :--- | :--- | :--- |
| **Mobile XS** | $320\text{px} - 359\text{px}$ | Single column, compact buttons, bottom nav with compact labels, no multi-column grids |
| **Mobile Standard** | $360\text{px} - 429\text{px}$ | Single column, sticky bottom navigation bar, vertical questionnaire buttons |
| **Mobile Plus / Phablet**| $430\text{px} - 767\text{px}$ | Single column, expanded cards, bottom navigation bar active |
| **Tablet** | $768\text{px} - 1023\text{px}$| Top navbar active, 2-column dashboard grids, side-by-side actions |
| **Desktop Standard** | $1024\text{px} - 1279\text{px}$| Centered $1000\text{px}$ container, full multi-column layouts, expanded Grad-CAM |
| **Desktop Large** | $1280\text{px} - 1440\text{px}+$| Centered $1140\text{px}$ container, comfortable margins, max-width $75\text{ch}$ for paragraphs |

---

## 4. Global Navigation & Application Shell

### 4.1 Desktop Navigation ($> 768\text{px}$)
- **Top Sticky Navbar**: Height `68px`, border-bottom `1px solid var(--color-border)`.
- **Left**: Brand icon + "AI Skin Analysis" with subtext "Preliminary Image Guidance".
- **Center**: Segmented nav-tabs (`Welcome`, `Analyze`, `History`, `Learn`, `Settings`).
- **Right**: Demo access workspace pill + Calibrated AI System Ready indicator dot.

### 4.2 Mobile Bottom Navigation ($\le 768\text{px}$)
- **Top Bar**: Lean header showing brand mark and Demo/Status indicators.
- **Sticky Bottom Navigation Bar**:
  - `position: fixed; bottom: 0; left: 0; right: 0; z-index: 100;`
  - Background: `#FFFFFF` with top border `1px solid var(--color-border)` and backdrop blur.
  - Safe area inset: `padding-bottom: env(safe-area-inset-bottom)`.
  - 5 equal tab items:
    1. **Welcome** (`Home` icon)
    2. **Analyze** (`Sparkles` icon)
    3. **History** (`History` icon)
    4. **Learn** (`BookOpen` icon)
    5. **Settings** (`Settings` icon)
  - Touch targets: $48\text{px}$ height per item.
  - Active state: Primary forest green icon and bold text with indicator bar.
  - Main page content automatically receives `padding-bottom: calc(72px + env(safe-area-inset-bottom))` to prevent overlap.

---

## 5. Screen-by-Screen Specifications

### 5.1 Screen 1: Welcome & Onboarding
- **Hero Area**: Compact clinical guidance badge, high-contrast title, concise subtitle.
- **Action Group**: Primary "Get Started" (redirects to Analyze / Onboarding), Secondary "Explore Library" (Learn), Tertiary "Demo Access".
- **Non-Diagnostic Notice**: Compact permanent notice strip.
- **4-Step Workflow Grid**: 1-column on mobile, 2-column on tablet, 4-column on desktop.
- **Capabilities Matrix**: 6 cards highlighting real capabilities (7 classes, Grad-CAM, image quality, safety triage, history, reports).
- **Responsible Use & Privacy**: Side-by-side trust and safety principles.

### 5.2 Screen 2: Analyze Workflow
- **State A: Input Preparation (`!result`)**:
  - **Step 1: Add Skin Image**: Upload File tile and Use Camera tile side-by-side on desktop, stacked on mobile. Once selected: clean preview with image dimensions, file size, Replace, and Remove actions.
  - **Capture Coaching Accordion**: Collapsed by default, opens to explain lighting, focus, framing, and avoiding filters.
  - **Step 2: Optional Symptom Context**:
    - Clearly marked as "Optional Context".
    - Timeline & location inputs.
    - 4 boolean symptom groups (Sensation, Physical Signs, Lesion Progression, Systemic & Sensitive).
    - Compact Yes / No / Not sure controls with comfortable mobile touch targets.
  - **Step 3: Review Before Analysis**: "Review Before Analysis" primary action opens `PreAnalysisReviewCard` displaying image preview, answered symptoms summary, and non-diagnostic consent.
  - **Step 4: Submission**: "Start AI Analysis" button triggers inference with spinner and disables duplicate submissions.
- **State B: Results Display (`result`)**:
  - Automatically hides the input form so users immediately see their results.
  - Prominent "Analyze Another Image" re-entry buttons at top and bottom.

### 5.3 Screen 3: Results Experience
- **1. Urgent Safety Banner** (`EmergencyAlert`): Occupies supreme visual precedence if triage level is URGENT.
- **2. Results Header**: Status badge, non-diagnostic label, and quick Export actions (PDF report & CSV download).
- **3. Primary Prediction Card**: Predicted condition name, confidence pill, non-diagnostic label, and uncertainty boundaries.
- **4. Safety Decision Card**: Routine / Attention / Urgent decision tier with clear reasoning.
- **5. Top-3 Predictions Card**: Bar visualization of top classes.
- **6. Image Quality Card**: Sharpness, brightness, and contrast validation.
- **7. Reported Symptoms Card**: Summary of answered symptoms.
- **8. Educational Disease Information**: Clinical morphology and care instructions.
- **9. Classical Symptom Reference**: Collapsible educational reference matrix.
- **10. Grad-CAM Attention Viewer**: Side-by-side, interactive blend slider, and heatmap-only modes.
- **11. AI-Assisted Educational Explanation**: Structured explanation pairing Visual Attention and Uncertainty side-by-side with compact next steps and limitations.
- **12. Final Safety Disclaimer**: Comprehensive closing medical advisory.

### 5.4 Screen 4: History & Timeline
- **Summary Metrics**: Stored record count, latest analysis timestamp, and session overview.
- **Filter Bar**: Collapsible on mobile to save vertical space; multi-attribute filters for condition, safety tier, confidence, and date range.
- **Timeline Records**: Chronological cards with timestamp, condition badge, confidence, safety chip, and View Details action.
- **Detail Modal**: Accessible dialog with keyboard `Escape` closing, PDF/CSV download, and individual record deletion.

### 5.5 Screen 5: Learn Section
- **Educational Literacy Pillars**: 4 cards explaining Model Boundaries, Grad-CAM, Optical Factors, and Emergency Red Flags.
- **Search & Filter**: Real-time condition filter input.
- **Condition Catalog**: Left navigation list on desktop (dropdown / wrapped pills on mobile) paired with clean condition detail cards.

### 5.6 Screen 6: Settings & Privacy Centre
- **Application Preferences**: Accessible Reduced Motion toggle and Replay Onboarding button.
- **Analysis History Management**: Record count, Clear History button with two-step confirmation.
- **Privacy Disclosures**: Verified local retention statement (zero external image retention).
- **Model Governance**: Architecture details (EfficientNet-B0), training dataset provenance, and non-diagnostic legal disclaimer.

---

## 6. Interaction States & Accessibility Matrix

| Component | Default State | Hover State | Active / Pressed | Focus-Visible |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Buttons** | `#245C4F` background, white text, 8px radius | `#193F37` background | Scale `0.98` | 2px solid `#245C4F`, 2px offset |
| **Secondary Buttons**| White background, `#E1E6E1` border | `#F0F3F0` background | Scale `0.98` | 2px solid `#245C4F`, 2px offset |
| **Bottom Nav Tab** | `#69736D` text, 20px icon | `#245C4F` text | Scale `0.96` | 2px solid `#245C4F`, 2px offset |
| **Accordion Headers**| White background, subtle border | `#F7F8F6` background | Background `#EAF2EE`| 2px solid `#245C4F`, 2px offset |
| **Inputs / Selects** | White background, `#E1E6E1` border | `#CBD5E1` border | `#245C4F` border | 2px solid `rgba(36,92,79,0.25)` |

### Accessibility Standards
- **WCAG 2.1 AA Compliance**: All text elements satisfy a minimum contrast ratio of $4.5:1$ against their respective backgrounds ($7:1$ for primary headings).
- **Color Independence**: Status levels use icons + explicit text badges (`ROUTINE`, `ATTENTION`, `URGENT`) alongside color.
- **Keyboard Navigation**: Full tab ordering, `aria-expanded` on collapsibles, `role="tablist"` on navigation, and `aria-live="polite"` on results.
- **Safe Motion**: `@media (prefers-reduced-motion: reduce)` and the user-controlled Reduced Motion setting completely disable animations and transitions.
