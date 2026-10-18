import React, { useState } from "react";
import {
  ShieldCheck,
  Activity,
  FileText,
  Lock,
  Mail,
  User,
  Eye,
  EyeOff,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  UserCheck,
  CheckCircle2,
  Sparkles,
  Info
} from "lucide-react";

/**
 * AuthView
 *
 * Professional, clinical-minimalist medical technology authentication screen.
 * Implements:
 * - Left side: Healthcare branding, three key benefits, and educational medical disclaimer.
 * - Right side: Login form, Registration form, and Forgot Password notice.
 * - Guest access trigger: Clear separation for instant guest evaluation without an account.
 */
export default function AuthView({ onLoginSuccess, onOpenGuestModal }) {
  const [authMode, setAuthMode] = useState("login"); // "login" | "register" | "forgot"

  // Login Form State
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [isSubmittingLogin, setIsSubmittingLogin] = useState(false);

  // Register Form State
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regConfirmPassword, setRegConfirmPassword] = useState("");
  const [showRegPassword, setShowRegPassword] = useState(false);
  const [showRegConfirm, setShowRegConfirm] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [regError, setRegError] = useState("");
  const [isSubmittingReg, setIsSubmittingReg] = useState(false);

  // Password Strength Calculations
  const hasMinLength = regPassword.length >= 8;
  const hasLetter = /[a-zA-Z]/.test(regPassword);
  const hasNumber = /\d/.test(regPassword);
  const passwordsMatch = regPassword.length > 0 && regPassword === regConfirmPassword;

  // Handle Login Submission
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginError("");

    if (!loginEmail.trim() || !loginPassword) {
      setLoginError("Please enter your email address and password.");
      return;
    }

    setIsSubmittingLogin(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: loginEmail.trim(),
          password: loginPassword,
        }),
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        setLoginError(data.error || "Invalid email or password.");
        return;
      }

      // Successful login
      if (data.token) {
        sessionStorage.setItem("auth_token", data.token);
      }
      onLoginSuccess(data.user, data.token);
    } catch {
      setLoginError("Unable to reach the authentication service. Please check your connection.");
    } finally {
      setIsSubmittingLogin(false);
    }
  };

  // Handle Register Submission
  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setRegError("");

    if (!regName.trim()) {
      setRegError("Please provide your full name.");
      return;
    }

    if (!regEmail.trim()) {
      setRegError("Please enter a valid email address.");
      return;
    }

    if (!hasMinLength || !hasLetter || !hasNumber) {
      setRegError("Password does not meet the minimum security requirements.");
      return;
    }

    if (regPassword !== regConfirmPassword) {
      setRegError("Passwords do not match. Please verify both password entries.");
      return;
    }

    if (!acceptedTerms) {
      setRegError("You must acknowledge the terms and educational disclaimer to create an account.");
      return;
    }

    setIsSubmittingReg(true);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: regName.trim(),
          email: regEmail.trim(),
          password: regPassword,
        }),
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        setRegError(data.error || "Account registration failed. Please try again.");
        return;
      }

      // Successful registration: auto-sign in
      if (data.token) {
        sessionStorage.setItem("auth_token", data.token);
      }
      onLoginSuccess(data.user, data.token);
    } catch {
      setRegError("Network error occurred during registration. Please verify connection.");
    } finally {
      setIsSubmittingReg(false);
    }
  };

  return (
    <div className="auth-page-container">
      <div className="auth-card-wrapper">
        {/* ============================================================ */}
        {/* LEFT COLUMN: BRANDING, BENEFITS & MEDICAL DISCLAIMER        */}
        {/* ============================================================ */}
        <div className="auth-brand-column">
          <div className="auth-brand-header">
            <div className="auth-brand-badge">
              <Activity size={18} />
              <span>AI SKIN ANALYSIS</span>
            </div>
            <h1 className="auth-brand-title">Preliminary Skin Image Analysis</h1>
            <p className="auth-brand-subtitle">
              Understand skin-image predictions through AI-assisted educational insights.
            </p>
          </div>

          <div className="auth-benefits-list">
            <div className="benefit-item">
              <div className="benefit-icon">
                <Sparkles size={18} />
              </div>
              <div className="benefit-content">
                <strong>AI-assisted image classification</strong>
                <p>
                  Seven dermatological categories analyzed using EfficientNet-B0
                  with calibrated confidence scores.
                </p>
              </div>
            </div>

            <div className="benefit-item">
              <div className="benefit-icon">
                <FileText size={18} />
              </div>
              <div className="benefit-content">
                <strong>Visual explanations and educational information</strong>
                <p>
                  Interpret prediction heatmaps (Grad-CAM) alongside referenced
                  clinical symptom information.
                </p>
              </div>
            </div>

            <div className="benefit-item">
              <div className="benefit-icon">
                <ShieldCheck size={18} />
              </div>
              <div className="benefit-content">
                <strong>Privacy-conscious analysis and safety guidance</strong>
                <p>
                  Anonymous local record retention, out-of-domain abstention,
                  and structured triage indications.
                </p>
              </div>
            </div>
          </div>

          <div className="auth-disclaimer-box">
            <Info size={16} />
            <p>
              <strong>Educational Notice:</strong> For educational purposes only.
              This application does not provide a medical diagnosis or treatment advice.
            </p>
          </div>
        </div>

        {/* ============================================================ */}
        {/* RIGHT COLUMN: AUTHENTICATION FORMS & GUEST ENTRY            */}
        {/* ============================================================ */}
        <div className="auth-form-column">
          {/* ---------------------------------------------------------- */}
          {/* LOGIN VIEW                                                 */}
          {/* ---------------------------------------------------------- */}
          {authMode === "login" && (
            <div className="auth-form-card">
              <div className="auth-form-header">
                <h2>Welcome back</h2>
                <p>Sign in to continue to your workspace.</p>
              </div>

              {loginError && (
                <div className="auth-error-banner" role="alert" aria-live="assertive">
                  <AlertCircle size={16} />
                  <span>{loginError}</span>
                </div>
              )}

              <form onSubmit={handleLoginSubmit} className="auth-fields-form">
                <div className="auth-input-group">
                  <label htmlFor="login-email">Email address</label>
                  <div className="auth-input-wrapper">
                    <Mail size={16} className="auth-field-icon" />
                    <input
                      id="login-email"
                      type="email"
                      autoComplete="email"
                      placeholder="name@example.com"
                      value={loginEmail}
                      onChange={(e) => {
                        setLoginEmail(e.target.value);
                        if (loginError) setLoginError("");
                      }}
                      required
                    />
                  </div>
                </div>

                <div className="auth-input-group">
                  <div className="auth-label-row">
                    <label htmlFor="login-password">Password</label>
                    <button
                      type="button"
                      className="auth-link-text"
                      onClick={() => {
                        setAuthMode("forgot");
                        setLoginError("");
                      }}
                    >
                      Forgot Password?
                    </button>
                  </div>
                  <div className="auth-input-wrapper">
                    <Lock size={16} className="auth-field-icon" />
                    <input
                      id="login-password"
                      type={showLoginPassword ? "text" : "password"}
                      autoComplete="current-password"
                      placeholder="Enter your password"
                      value={loginPassword}
                      onChange={(e) => {
                        setLoginPassword(e.target.value);
                        if (loginError) setLoginError("");
                      }}
                      required
                    />
                    <button
                      type="button"
                      className="auth-eye-btn"
                      onClick={() => setShowLoginPassword(!showLoginPassword)}
                      aria-label={showLoginPassword ? "Hide password" : "Show password"}
                    >
                      {showLoginPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  className="auth-primary-btn"
                  disabled={isSubmittingLogin}
                >
                  {isSubmittingLogin ? (
                    <span>Signing in...</span>
                  ) : (
                    <>
                      <span>Sign In</span>
                      <ArrowRight size={16} />
                    </>
                  )}
                </button>
              </form>

              <div className="auth-switch-mode">
                <span>Don't have an account? </span>
                <button
                  type="button"
                  className="auth-switch-link"
                  onClick={() => {
                    setAuthMode("register");
                    setLoginError("");
                  }}
                >
                  Create an Account
                </button>
              </div>

              {/* CLEARLY SEPARATED GUEST / DEMO ENTRY */}
              <div className="auth-divider">
                <span>OR CONTINUE WITHOUT ACCOUNT</span>
              </div>

              <div className="auth-guest-section">
                <button
                  type="button"
                  className="auth-guest-btn"
                  onClick={onOpenGuestModal}
                >
                  <UserCheck size={18} />
                  <span>Continue as Guest</span>
                </button>
                <p className="auth-guest-caption">
                  Access the clinical education workspace immediately without creating an account.
                </p>
              </div>
            </div>
          )}

          {/* ---------------------------------------------------------- */}
          {/* REGISTRATION VIEW                                          */}
          {/* ---------------------------------------------------------- */}
          {authMode === "register" && (
            <div className="auth-form-card">
              <div className="auth-form-header">
                <h2>Create an Account</h2>
                <p>Register for educational skin analysis access.</p>
              </div>

              {regError && (
                <div className="auth-error-banner" role="alert" aria-live="assertive">
                  <AlertCircle size={16} />
                  <span>{regError}</span>
                </div>
              )}

              <form onSubmit={handleRegisterSubmit} className="auth-fields-form">
                <div className="auth-input-group">
                  <label htmlFor="reg-name">Full name</label>
                  <div className="auth-input-wrapper">
                    <User size={16} className="auth-field-icon" />
                    <input
                      id="reg-name"
                      type="text"
                      autoComplete="name"
                      placeholder="Dr. Sarah Chen or Alex Taylor"
                      value={regName}
                      onChange={(e) => {
                        setRegName(e.target.value);
                        if (regError) setRegError("");
                      }}
                      required
                    />
                  </div>
                </div>

                <div className="auth-input-group">
                  <label htmlFor="reg-email">Email address</label>
                  <div className="auth-input-wrapper">
                    <Mail size={16} className="auth-field-icon" />
                    <input
                      id="reg-email"
                      type="email"
                      autoComplete="email"
                      placeholder="name@example.com"
                      value={regEmail}
                      onChange={(e) => {
                        setRegEmail(e.target.value);
                        if (regError) setRegError("");
                      }}
                      required
                    />
                  </div>
                </div>

                <div className="auth-input-group">
                  <label htmlFor="reg-password">Password</label>
                  <div className="auth-input-wrapper">
                    <Lock size={16} className="auth-field-icon" />
                    <input
                      id="reg-password"
                      type={showRegPassword ? "text" : "password"}
                      autoComplete="new-password"
                      placeholder="Create a strong password"
                      value={regPassword}
                      onChange={(e) => {
                        setRegPassword(e.target.value);
                        if (regError) setRegError("");
                      }}
                      required
                    />
                    <button
                      type="button"
                      className="auth-eye-btn"
                      onClick={() => setShowRegPassword(!showRegPassword)}
                      aria-label={showRegPassword ? "Hide password" : "Show password"}
                    >
                      {showRegPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>

                  {/* Password requirement indicator */}
                  <div className="auth-pw-hints">
                    <span className={hasMinLength ? "hint-pass" : "hint-pending"}>
                      <CheckCircle2 size={12} /> At least 8 characters
                    </span>
                    <span className={hasLetter ? "hint-pass" : "hint-pending"}>
                      <CheckCircle2 size={12} /> Contains letters
                    </span>
                    <span className={hasNumber ? "hint-pass" : "hint-pending"}>
                      <CheckCircle2 size={12} /> Contains numbers
                    </span>
                  </div>
                </div>

                <div className="auth-input-group">
                  <label htmlFor="reg-confirm">Confirm password</label>
                  <div className="auth-input-wrapper">
                    <Lock size={16} className="auth-field-icon" />
                    <input
                      id="reg-confirm"
                      type={showRegConfirm ? "text" : "password"}
                      autoComplete="new-password"
                      placeholder="Re-enter your password"
                      value={regConfirmPassword}
                      onChange={(e) => {
                        setRegConfirmPassword(e.target.value);
                        if (regError) setRegError("");
                      }}
                      required
                    />
                    <button
                      type="button"
                      className="auth-eye-btn"
                      onClick={() => setShowRegConfirm(!showRegConfirm)}
                      aria-label={showRegConfirm ? "Hide password" : "Show password"}
                    >
                      {showRegConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                  {regConfirmPassword.length > 0 && (
                    <span className={`auth-match-indicator ${passwordsMatch ? "match-pass" : "match-fail"}`}>
                      {passwordsMatch ? "Passwords match" : "Passwords do not match"}
                    </span>
                  )}
                </div>

                <label className="auth-checkbox-label" htmlFor="reg-terms">
                  <input
                    id="reg-terms"
                    type="checkbox"
                    checked={acceptedTerms}
                    onChange={(e) => {
                      setAcceptedTerms(e.target.checked);
                      if (regError) setRegError("");
                    }}
                  />
                  <span>
                    I accept the Terms of Use and Privacy Notice, and understand that this
                    platform is an educational tool, not a diagnostic medical device.
                  </span>
                </label>

                <button
                  type="submit"
                  className="auth-primary-btn"
                  disabled={isSubmittingReg}
                >
                  {isSubmittingReg ? (
                    <span>Creating account...</span>
                  ) : (
                    <>
                      <span>Create Account</span>
                      <ArrowRight size={16} />
                    </>
                  )}
                </button>
              </form>

              <div className="auth-switch-mode">
                <span>Already have an account? </span>
                <button
                  type="button"
                  className="auth-switch-link"
                  onClick={() => {
                    setAuthMode("login");
                    setRegError("");
                  }}
                >
                  Sign In
                </button>
              </div>
            </div>
          )}

          {/* ---------------------------------------------------------- */}
          {/* FORGOT PASSWORD VIEW                                       */}
          {/* ---------------------------------------------------------- */}
          {authMode === "forgot" && (
            <div className="auth-form-card">
              <div className="auth-form-header">
                <h2>Reset Password</h2>
                <p>Self-service recovery status</p>
              </div>

              <div className="auth-status-callout">
                <div className="status-callout-icon">
                  <AlertTriangle size={20} />
                </div>
                <div className="status-callout-text">
                  <strong>Automated Password Reset Unavailable</strong>
                  <p>
                    Automated self-service password recovery requires a configured,
                    authenticated SMTP email gateway.
                  </p>
                  <p className="callout-detail">
                    In this evaluation and local research deployment, automated email
                    dispatch is disabled to maintain patient data boundaries and prevent
                    unauthorized email transmission.
                  </p>
                </div>
              </div>

              <div className="auth-resolution-card">
                <h4>What you can do:</h4>
                <ul>
                  <li>Contact your local system administrator for a credential reset.</li>
                  <li>Or create a new educational account with an alternative email.</li>
                  <li>Or proceed using immediate guest access without saving credentials.</li>
                </ul>
              </div>

              <div className="auth-forgot-actions">
                <button
                  type="button"
                  className="auth-primary-btn"
                  onClick={() => setAuthMode("login")}
                >
                  Return to Sign In
                </button>

                <button
                  type="button"
                  className="auth-secondary-btn"
                  onClick={onOpenGuestModal}
                >
                  <UserCheck size={16} />
                  <span>Continue as Guest</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
