import {
  ShieldCheck,
  ArrowRight,
  BookOpen,
  Camera,
  Layers,
  Activity,
  Lock,
  Compass,
  ClipboardList,
  AlertTriangle,
  FileText,
  Sparkles,
} from "lucide-react";

export default function WelcomeView({
  onGetStarted,
  onExplore,
  onNavigateTab,
}) {
  return (
    <div className="welcome-container">
      {/* ============================================================
       * SECTION B: HERO
       * ============================================================ */}
      <section className="welcome-hero">
        <div className="welcome-pill-badge">
          <ShieldCheck size={15} />
          <span>CLINICAL GUIDANCE & EDUCATION PLATFORM</span>
        </div>

        <h1 className="welcome-title">
          Understand your skin image with
          <span> AI-assisted insights</span>
        </h1>

        <p className="welcome-subtitle">
          Explore educational skin-image analysis with image-quality
          guidance, clear explanations, and important safety information.
        </p>

        {/* Primary and Secondary Action Group */}
        <div className="welcome-action-group">
          <button
            type="button"
            className="welcome-btn-primary"
            onClick={onGetStarted}
            aria-label="Get started with skin image analysis"
          >
            <span>Get Started</span>
            <ArrowRight size={16} />
          </button>

          <button
            type="button"
            className="welcome-btn-secondary"
            onClick={onExplore}
            aria-label="Explore the educational learning library"
          >
            <Compass size={16} />
            <span>Explore the Application</span>
          </button>
        </div>

        {/* Permanent Non-Diagnostic Disclaimer Strip */}
        <div className="welcome-disclaimer-strip" role="note">
          <ShieldCheck size={16} className="disclaimer-icon" />
          <p>
            <strong>Educational Scope:</strong> This application provides educational information based on AI-assisted image analysis. Its predictions are not medical diagnoses and should not replace evaluation by a qualified healthcare professional.
          </p>
        </div>
      </section>

      {/* ============================================================
       * SECTION C: HOW IT WORKS (FOUR-STEP WORKFLOW)
       * ============================================================ */}
      <section className="welcome-workflow-section" aria-labelledby="workflow-title">
        <div className="section-header-center">
          <span className="section-eyebrow">STEP-BY-STEP PROCESS</span>
          <h2 id="workflow-title" className="section-heading">How the Analysis Workflow Works</h2>
          <p className="section-subheading">
            A structured, multi-stage assessment designed to ensure photographic validity, clinical safety, and transparent explainability.
          </p>
        </div>

        <div className="welcome-workflow-grid">
          <div className="workflow-step-card">
            <div className="workflow-step-num">1</div>
            <div className="workflow-card-icon">
              <Camera size={22} />
            </div>
            <h3>Add a Skin Image</h3>
            <p>
              Upload a skin photo (JPG, PNG) or capture live with camera coaching guidance.
            </p>
          </div>

          <div className="workflow-step-card">
            <div className="workflow-step-num">2</div>
            <div className="workflow-card-icon">
              <ClipboardList size={22} />
            </div>
            <h3>Provide Optional Context</h3>
            <p>
              Answer optional sensation, pain, and timeline questions to refine safety triage.
            </p>
          </div>

          <div className="workflow-step-card">
            <div className="workflow-step-num">3</div>
            <div className="workflow-card-icon">
              <Activity size={22} />
            </div>
            <h3>Review AI Results</h3>
            <p>
              Inspect 7-class prediction, uncertainty score, quality checks, and Grad-CAM heatmap.
            </p>
          </div>

          <div className="workflow-step-card">
            <div className="workflow-step-num">4</div>
            <div className="workflow-card-icon">
              <ShieldCheck size={22} />
            </div>
            <h3>Understand Guidance</h3>
            <p>
              Examine safety triage advisories, classical references, and educational profiles.
            </p>
          </div>
        </div>
      </section>

      {/* ============================================================
       * SECTION D: WHAT THE APPLICATION PROVIDES (ACTUAL CAPABILITIES)
       * ============================================================ */}
      <section className="welcome-features-section" aria-labelledby="features-title">
        <div className="section-header-center">
          <span className="section-eyebrow">SYSTEM CAPABILITIES</span>
          <h2 id="features-title" className="section-heading">What the Application Provides</h2>
          <p className="section-subheading">
            The platform is calibrated specifically for seven common skin disease categories and incorporates transparent explainability safeguards.
          </p>
        </div>

        <div className="welcome-features-grid">
          <div className="welcome-feature-card">
            <div className="welcome-feature-icon">
              <Camera size={22} />
            </div>
            <h3>Image-Quality Feedback</h3>
            <p>
              Pre-inference validation calculates brightness, contrast, and Laplacian sharpness to flag underexposed or blurred inputs before classification.
            </p>
          </div>

          <div className="welcome-feature-card">
            <div className="welcome-feature-icon">
              <Layers size={22} />
            </div>
            <h3>7-Class Skin Classification</h3>
            <p>
              Trained EfficientNet-B0 convolutional network predicts across psoriasis, urticaria, molluscum contagiosum, warts, impetigo, acne vulgaris, and vitiligo.
            </p>
          </div>

          <div className="welcome-feature-card">
            <div className="welcome-feature-icon">
              <Sparkles size={22} />
            </div>
            <h3>Confidence & OOD Guardrails</h3>
            <p>
              Top-3 probability distribution and entropy-based out-of-distribution (OOD) abstention reliably reject non-skin images or ambiguous inputs.
            </p>
          </div>

          <div className="welcome-feature-card">
            <div className="welcome-feature-icon">
              <Activity size={22} />
            </div>
            <h3>Grad-CAM Explainability</h3>
            <p>
              Interactive gradient-weighted class activation mapping lets users inspect attention heatmaps side-by-side or as an opacity overlay directly against original skin tissue.
            </p>
          </div>

          <div className="welcome-feature-card">
            <div className="welcome-feature-icon">
              <BookOpen size={22} />
            </div>
            <h3>Educational Explanations</h3>
            <p>
              Integrated clinical disease encyclopedia detailing primary morphology, anatomical distributions, and differential considerations for all supported conditions.
            </p>
          </div>

          <div className="welcome-feature-card">
            <div className="welcome-feature-icon">
              <FileText size={22} />
            </div>
            <h3>Analysis History & Reports</h3>
            <p>
              Chronological session timeline with multi-attribute filtering, individual record deletion, and publication-ready PDF and CSV export generation.
            </p>
          </div>
        </div>
      </section>

      {/* ============================================================
       * SECTION E & F: RESPONSIBLE USE & PRIVACY SUMMARY
       * ============================================================ */}
      <section className="welcome-trust-grid" aria-label="Trust, safety and privacy">
        {/* Responsible Use */}
        <div className="trust-card responsible-use-card">
          <div className="trust-card-header">
            <div className="trust-icon-bubble trust-icon-amber">
              <AlertTriangle size={20} />
            </div>
            <div>
              <h3>Responsible Clinical Use</h3>
              <span className="trust-tag">NON-DIAGNOSTIC GUIDELINES</span>
            </div>
          </div>
          <div className="trust-card-body">
            <p>
              This application provides preliminary educational information based on AI image classification. Its mathematical predictions are not medical diagnoses and cannot reliably detect conditions outside its seven trained classes (such as melanomas or non-melanoma skin cancers).
            </p>
            <ul className="trust-bullet-list">
              <li>Always seek consultation with a board-certified dermatologist or physician for clinical evaluation.</li>
              <li>Sudden rash spreading, mucosal involvement, fever, or difficulty breathing require immediate emergency care.</li>
              <li>Never discontinue, alter, or delay prescribed medical treatments based on AI screening outputs.</li>
            </ul>
          </div>
        </div>

        {/* Privacy Summary */}
        <div className="trust-card privacy-summary-card">
          <div className="trust-card-header">
            <div className="trust-icon-bubble trust-icon-forest">
              <Lock size={20} />
            </div>
            <div>
              <h3>Local Privacy & Data Handling</h3>
              <span className="trust-tag">VERIFIED LOCAL ARCHITECTURE</span>
            </div>
          </div>
          <div className="trust-card-body">
            <p>
              We prioritize patient privacy through a restrained, local-first data architecture. Your medical images and personal answers are handled securely:
            </p>
            <ul className="trust-bullet-list">
              <li>Images are processed locally on your server session; no third-party cloud image repositories are utilized.</li>
              <li>Patient identifying details (names, contact details) are never required, logged, or requested.</li>
              <li>Analysis history is stored locally in a standard audit CSV file which you can review or permanently clear at any time in Settings.</li>
            </ul>
            {onNavigateTab && (
              <div className="trust-card-action">
                <button
                  type="button"
                  className="trust-link-btn"
                  onClick={() => onNavigateTab("settings")}
                >
                  <span>Review Privacy & Retention Settings</span>
                  <ArrowRight size={14} />
                </button>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ============================================================
       * SECTION G: FOOTER & NAVIGATION LINKS
       * ============================================================ */}
      <footer className="welcome-footer-section">
        <div className="welcome-footer-content">
          <div className="welcome-footer-brand">
            <div className="brand-icon-sm">
              <Sparkles size={16} />
            </div>
            <strong>AI Skin Analysis</strong>
            <span>Preliminary Clinical Guidance & Education</span>
          </div>

          <nav className="welcome-footer-links" aria-label="Welcome footer navigation">
            <button
              type="button"
              className="footer-nav-link"
              onClick={onGetStarted}
            >
              Analyze
            </button>
            <button
              type="button"
              className="footer-nav-link"
              onClick={() => onNavigateTab ? onNavigateTab("history") : onGetStarted()}
            >
              History
            </button>
            <button
              type="button"
              className="footer-nav-link"
              onClick={onExplore}
            >
              Learn Base
            </button>
            <button
              type="button"
              className="footer-nav-link"
              onClick={() => onNavigateTab ? onNavigateTab("settings") : onGetStarted()}
            >
              Privacy & Settings
            </button>
          </nav>
        </div>

        <div className="welcome-footer-bottom">
          <p>
            Research Prototype &bull; EfficientNet-B0 v2.0 &bull; Non-Diagnostic Educational Platform
          </p>
        </div>
      </footer>
    </div>
  );
}
