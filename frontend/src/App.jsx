import { useRef, useState, useEffect } from "react";
import {
  Upload,
  Camera,
  ShieldCheck,
  Sparkles,
  Image as ImageIcon,
  AlertCircle,
  History as HistoryIcon,
  FileText,
  FileSpreadsheet,
  BookOpen,
  Settings as SettingsIcon,
  Trash2,
  Home,
  User,
  UserCheck,
  ClipboardCheck,
} from "lucide-react";
import "./App.css";
import SymptomQuestionnaire from "./components/SymptomQuestionnaire";
import EmergencyAlert from "./components/EmergencyAlert";
import PredictionCard from "./components/PredictionCard";
import SafetyDecisionCard from "./components/SafetyDecisionCard";
import TopPredictionsCard from "./components/TopPredictionsCard";
import ImageQualityCard from "./components/ImageQualityCard";
import ReportedSymptomsCard from "./components/ReportedSymptomsCard";
import DiseaseInfoCard from "./components/DiseaseInfoCard";
import HistoryView from "./components/HistoryView";
import LearnView from "./components/LearnView";
import SettingsView from "./components/SettingsView";
import CameraCapture from "./components/CameraCapture";
import CaptureCoachingCard from "./components/CaptureCoachingCard";
import AbstentionCard from "./components/AbstentionCard";
import GradcamComparisonCard from "./components/GradcamComparisonCard";
import WelcomeView from "./components/WelcomeView";
import DemoLoginModal from "./components/DemoLoginModal";
import OnboardingModal from "./components/OnboardingModal";
import PreAnalysisReviewCard from "./components/PreAnalysisReviewCard";
import ClassicalSymptomReferenceCard from "./components/ClassicalSymptomReferenceCard";
import EducationalExplanationCard from "./components/EducationalExplanationCard";
import AuthView from "./components/AuthView";
import GuestDisclaimerModal from "./components/GuestDisclaimerModal";
import { INITIAL_SYMPTOMS } from "./constants/symptoms";


function App() {
  const fileInputRef = useRef(null);
  const activeAnalysisIdRef = useRef(0);
  const cameFromReviewRef = useRef(false);

  const [activeTab, setActiveTab] = useState("welcome"); // "welcome" | "analyze" | "history" | "learn" | "settings"
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null); // { id, name, email, isGuest, role }
  const [isAuthChecking, setIsAuthChecking] = useState(() => {
    try {
      return Boolean(sessionStorage.getItem("auth_token"));
    } catch {
      return false;
    }
  });
  const [isGuestModalOpen, setIsGuestModalOpen] = useState(false);

  // Restore authenticated session from sessionStorage on initial load
  useEffect(() => {
    const token = sessionStorage.getItem("auth_token");
    if (!token) return;

    fetch("/api/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.user) {
          setCurrentUser(data.user);
        } else {
          sessionStorage.removeItem("auth_token");
        }
      })
      .catch(() => {
        sessionStorage.removeItem("auth_token");
      })
      .finally(() => {
        setIsAuthChecking(false);
      });
  }, []);

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    setActiveTab("welcome");
    setIsGuestModalOpen(false);
  };

  const handleEnterGuest = (guestUser) => {
    setCurrentUser(guestUser);
    setActiveTab("welcome");
    setIsGuestModalOpen(false);
  };

  const handleSignOut = async () => {
    const token = sessionStorage.getItem("auth_token");
    if (token) {
      try {
        await fetch("/api/auth/logout", {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {
        // Continue clearing session even if logout API fails
      }
      sessionStorage.removeItem("auth_token");
    }
    setCurrentUser(null);
    setActiveTab("welcome");
    setIsGuestModalOpen(false);
    setIsReviewing(false);
    setIsCameraOpen(false);
    setError("");
  };
  const [reducedMotion, setReducedMotion] = useState(() => {
    try {
      const stored = localStorage.getItem("preferred_reduced_motion");
      if (stored !== null) return stored === "true";
      return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    } catch {
      return false;
    }
  });
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [imageSource, setImageSource] = useState("upload"); // "upload" | "camera"
  const [imageDimensions, setImageDimensions] = useState(null);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [symptoms, setSymptoms] = useState(INITIAL_SYMPTOMS);
  const [questionnaireOpen, setQuestionnaireOpen] = useState(false);
  const [isReviewing, setIsReviewing] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [isGeminiLoading, setIsGeminiLoading] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [isExportingCsv, setIsExportingCsv] = useState(false);

  useEffect(() => {
    if (!previewUrl) return;
    let isCancelled = false;
    const img = new Image();
    img.onload = () => {
      if (!isCancelled) {
        setImageDimensions({
          width: img.naturalWidth,
          height: img.naturalHeight,
        });
      }
    };
    img.onerror = () => {
      if (!isCancelled) {
        setImageDimensions(null);
      }
    };
    img.src = previewUrl;
    return () => {
      isCancelled = true;
    };
  }, [previewUrl]);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Please select a valid JPG, JPEG or PNG image.");
      return;
    }

    activeAnalysisIdRef.current += 1;
    setSelectedImage(file);
    setPreviewUrl(URL.createObjectURL(file));
    setImageSource("upload");
    // Preserve symptoms if already filled
    setIsCameraOpen(false);

    setResult(null);
    setError("");
    setIsAnalyzing(false);
    setIsGeminiLoading(false);

    if (cameFromReviewRef.current) {
      setIsReviewing(true);
      cameFromReviewRef.current = false;
    }
  };

  const handleCameraCapture = (file, preview) => {
    activeAnalysisIdRef.current += 1;
    setSelectedImage(file);
    setPreviewUrl(preview);
    setImageSource("camera");
    // Preserve symptoms if already filled
    setIsCameraOpen(false);

    setResult(null);
    setError("");
    setIsAnalyzing(false);
    setIsGeminiLoading(false);

    if (cameFromReviewRef.current) {
      setIsReviewing(true);
      cameFromReviewRef.current = false;
    }
  };

  const handleCameraCancel = () => {
    setIsCameraOpen(false);
    if (cameFromReviewRef.current) {
      setIsReviewing(true);
      cameFromReviewRef.current = false;
    }
  };

  const handleUploadClick = () => {
    setIsCameraOpen(false);
    fileInputRef.current?.click();
  };

  const handleProceedToReview = () => {
    if (!selectedImage) {
      setError("Please select or capture a valid skin image before proceeding to review.");
      return;
    }
    setError("");
    setIsReviewing(true);
  };

  const handleBackToEdit = () => {
    setIsReviewing(false);
  };

  const handleEditResponsesFromReview = () => {
    setIsReviewing(false);
    setQuestionnaireOpen(true);
  };

  const handleChangeImageFromReview = () => {
    if (isAnalyzing) return;
    cameFromReviewRef.current = true;
    fileInputRef.current?.click();
  };

  const handleRetakePhotoFromReview = () => {
    if (isAnalyzing) return;
    cameFromReviewRef.current = true;
    setIsReviewing(false);
    setIsCameraOpen(true);
  };

  const generateGeminiExplanation = async (
    analysisResult,
    targetAnalysisId = activeAnalysisIdRef.current
  ) => {
    const prediction =
      analysisResult?.prediction?.class_name ||
      analysisResult?.prediction;

    const confidence =
      analysisResult?.prediction?.confidence ??
      analysisResult?.confidence;

    if (!analysisResult || !prediction || confidence === undefined) {
      console.error("[AI FRONTEND] Missing inference context.");
      return;
    }
    if (isGeminiLoading) return;

    setIsGeminiLoading(true);

    setResult((previousResult) => {
      if (!previousResult) return null;
      return {
        ...previousResult,
        explanationLoading: true,
        explanation:
          "Generating educational explanation with Gemini...",
      };
    });

    try {
      const explanationController =
        new AbortController();

      const explanationTimeout =
        setTimeout(() => {
          explanationController.abort();
        }, 35000);

      const explanationResponse = await fetch(
        "/api/explain",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            prediction,
            confidence,
            analysis: analysisResult,
          }),
          signal: explanationController.signal,
        }
      );

      clearTimeout(explanationTimeout);

      const explanationText =
        await explanationResponse.text();

      // Discard stale response if newer analysis was started
      if (activeAnalysisIdRef.current !== targetAnalysisId) {
        return;
      }

      if (!explanationText.trim()) {
        throw new Error(
          "AI educational explanation is currently unavailable."
        );
      }

      let explanationData;

      try {
        explanationData =
          JSON.parse(explanationText);
      } catch {
        throw new Error(
          "AI educational explanation is currently unavailable."
        );
      }

      if (!explanationResponse.ok) {
        throw new Error(
          explanationData.error ||
          explanationData.details ||
          "AI educational explanation is currently unavailable."
        );
      }

      const returnedExplanation =
        explanationData.explanation ||
        explanationData.message ||
        "AI educational explanation is currently unavailable.";

      setIsGeminiLoading(false);

      setResult((previousResult) => {
        if (!previousResult || activeAnalysisIdRef.current !== targetAnalysisId) return previousResult;
        return {
          ...previousResult,
          explanation: returnedExplanation,
          structuredExplanation:
            explanationData && explanationData.schema_version === "1.0"
              ? explanationData
              : null,
          explanationLoading: false,
        };
      });

    } catch (geminiError) {
      if (activeAnalysisIdRef.current !== targetAnalysisId) {
        return;
      }

      console.error(
        "[AI FRONTEND] Gemini explanation error:",
        geminiError
      );

      setIsGeminiLoading(false);

      setResult((previousResult) => {
        if (!previousResult || activeAnalysisIdRef.current !== targetAnalysisId) return previousResult;
        return {
          ...previousResult,
          explanation:
            "Gemini explanation is temporarily unavailable. The CNN prediction and Grad-CAM analysis were completed successfully.",
          explanationLoading: false,
        };
      });
    }
  };

  const handleAnalyze = async () => {
    if (!selectedImage || isAnalyzing) return;

    const currentAnalysisId = ++activeAnalysisIdRef.current;

    setIsAnalyzing(true);
    setError("");
    setResult(null);

    try {
      // =========================================================
      // STEP 1 ? CNN + GRAD-CAM
      // =========================================================

      const formData = new FormData();
      formData.append("image", selectedImage);

      const activeSymptoms = {};
      if (symptoms.duration && typeof symptoms.duration === "string" && symptoms.duration.trim()) {
        activeSymptoms.duration = symptoms.duration.trim();
      }
      if (symptoms.location && typeof symptoms.location === "string" && symptoms.location.trim()) {
        activeSymptoms.location = symptoms.location.trim();
      }
      const boolKeys = [
        "spreading",
        "itching",
        "pain",
        "burning",
        "swelling",
        "bleeding",
        "discharge",
        "blisters",
        "fever",
        "sensitiveArea",
        "previousOccurrence",
        "newExposure",
      ];
      boolKeys.forEach((key) => {
        if (symptoms[key] === true || symptoms[key] === false) {
          activeSymptoms[key] = symptoms[key];
        }
      });

      if (Object.keys(activeSymptoms).length > 0) {
        formData.append("symptoms", JSON.stringify(activeSymptoms));
      }

      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      });

      const responseText = await response.text();

      // Check if user has changed image or restarted analysis while waiting
      if (activeAnalysisIdRef.current !== currentAnalysisId) {
        return;
      }

      console.log("AI bridge status:", response.status);
      console.log("AI bridge response:", responseText);

      if (!responseText.trim()) {
        throw new Error(
          `AI bridge returned an empty response (HTTP ${response.status}).`
        );
      }

      let data;

      try {
        data = JSON.parse(responseText);
      } catch {
        throw new Error(
          `AI bridge returned invalid JSON: ${responseText.slice(0, 500)}`
        );
      }

      if (!response.ok) {
        throw new Error(
          data.error ||
          data.details ||
          "AI analysis failed."
        );
      }

      const isAbstained = data.analysis?.status === "abstained" || data.status === "abstained";

      if (isAbstained) {
        setResult({
          ...data,
          explanationLoading: false,
          explanation: data.explanation || data.ood_assessment?.message || "Classification was abstained because the input is outside the supported domain.",
        });
        setIsAnalyzing(false);
        setIsGeminiLoading(false);
        setIsReviewing(false);
        console.log("[AI FRONTEND] Domain abstention handled safely.");
      } else {
        // Show CNN result immediately.
        setResult({
          ...data,
          explanationLoading: true,
          explanation:
            "Generating educational explanation with Gemini...",
        });

        // CNN is complete, so stop the main analysis spinner.
        setIsAnalyzing(false);
        setIsGeminiLoading(true);
        setIsReviewing(false);
        console.log(
          "[AI FRONTEND] CNN analysis completed."
        );

        // STEP 2 ? GEMINI EXPLANATION
        await generateGeminiExplanation(data, currentAnalysisId);
      }

    } catch (err) {
      if (activeAnalysisIdRef.current !== currentAnalysisId) {
        return;
      }

      console.error(
        "[AI FRONTEND] AI analysis error:",
        err
      );

      setError(
        err.message ||
        "Unable to analyze the image."
      );

      setIsAnalyzing(false);
    }
  };

  const handleRemoveImage = () => {
    activeAnalysisIdRef.current += 1;
    setSelectedImage(null);
    setPreviewUrl("");
    setImageDimensions(null);
    setIsCameraOpen(false);
    setIsReviewing(false);
    setResult(null);
    setError("");
    setIsAnalyzing(false);
    setIsGeminiLoading(false);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleNewImage = () => {
    activeAnalysisIdRef.current += 1;
    setSelectedImage(null);
    setPreviewUrl("");
    setImageDimensions(null);
    setIsCameraOpen(false);
    setIsReviewing(false);
    setSymptoms(INITIAL_SYMPTOMS);
    setResult(null);
    setError("");
    setIsAnalyzing(false);
    setIsGeminiLoading(false);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDownloadPdf = async () => {
    if (!result) return;
    try {
      setIsDownloadingPdf(true);
      const payload = {
        ...result,
        symptoms: result.symptoms || symptoms,
      };
      const res = await fetch("/api/export/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Failed to generate PDF (HTTP ${res.status}).`);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Skin_Analysis_Report_${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("[REPORT] PDF download error:", err);
      alert(err.message || "Failed to download PDF report.");
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handleExportCsv = async () => {
    if (!result) return;
    try {
      setIsExportingCsv(true);
      const payload = {
        ...result,
        symptoms: result.symptoms || symptoms,
      };
      const res = await fetch("/api/export/csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Failed to generate CSV (HTTP ${res.status}).`);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Skin_Analysis_Export_${Date.now()}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("[REPORT] CSV export error:", err);
      alert(err.message || "Failed to export CSV.");
    } finally {
      setIsExportingCsv(false);
    }
  };

  if (isAuthChecking) {
    return (
      <div className={`app auth-loading-screen ${reducedMotion ? "reduced-motion" : ""}`}>
        <div className="auth-loading-card">
          <div className="brand-icon pulse">
            <Sparkles size={28} />
          </div>
          <h2>AI Skin Analysis</h2>
          <p>Verifying secure session...</p>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className={`app auth-gate-mode ${reducedMotion ? "reduced-motion" : ""}`}>
        <header className="navbar navbar-gate">
          <div className="brand" aria-label="AI Skin Analysis Application">
            <div className="brand-icon">
              <Sparkles size={20} />
            </div>
            <div>
              <h1>AI Skin Analysis</h1>
              <span>Clinical Guidance & Education</span>
            </div>
          </div>

          <div className="status">
            <span className="status-dot"></span>
            System Ready
          </div>
        </header>

        <main className="gate-screen-body" aria-label="Authentication & Access Gate">
          <AuthView
            onLoginSuccess={handleLoginSuccess}
            onOpenGuestModal={() => setIsGuestModalOpen(true)}
          />
          <GuestDisclaimerModal
            isOpen={isGuestModalOpen}
            onClose={() => setIsGuestModalOpen(false)}
            onEnterGuest={handleEnterGuest}
          />
        </main>
      </div>
    );
  }

  return (
    <div className={`app ${reducedMotion ? "reduced-motion" : ""}`}>

      <header className="navbar">

        <div
          className="brand"
          onClick={() => setActiveTab("welcome")}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              setActiveTab("welcome");
            }
          }}
          style={{ cursor: "pointer" }}
          aria-label="Go to Welcome page"
        >
          <div className="brand-icon">
            <Sparkles size={20} />
          </div>

          <div>
            <h1>AI Skin Analysis</h1>
            <span>Preliminary Image Guidance</span>
          </div>
        </div>

        <nav className="nav-tabs" role="tablist" aria-label="Main Navigation">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "welcome"}
            className={`nav-tab-btn ${activeTab === "welcome" ? "active" : ""}`}
            onClick={() => setActiveTab("welcome")}
          >
            <Home size={16} />
            <span>Welcome</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "analyze"}
            className={`nav-tab-btn ${activeTab === "analyze" ? "active" : ""}`}
            onClick={() => setActiveTab("analyze")}
          >
            <Sparkles size={16} />
            <span>Analyze</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "history"}
            className={`nav-tab-btn ${activeTab === "history" ? "active" : ""}`}
            onClick={() => setActiveTab("history")}
          >
            <HistoryIcon size={16} />
            <span>History</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "learn"}
            className={`nav-tab-btn ${activeTab === "learn" ? "active" : ""}`}
            onClick={() => setActiveTab("learn")}
          >
            <BookOpen size={16} />
            <span>Learn</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "settings"}
            className={`nav-tab-btn ${activeTab === "settings" ? "active" : ""}`}
            onClick={() => setActiveTab("settings")}
          >
            <SettingsIcon size={16} />
            <span>Settings</span>
          </button>
        </nav>

        <div className="navbar-right-group">
          {currentUser && (
            <div
              className={`user-session-badge demo-user-badge ${currentUser.isGuest ? "guest-badge" : "registered-badge"}`}
              title={currentUser.isGuest ? `Guest Session: ${currentUser.name}` : `Signed in as ${currentUser.name} (${currentUser.email})`}
            >
              {currentUser.isGuest ? <UserCheck size={14} /> : <User size={14} />}
              <span className="session-user-name demo-user-name">{currentUser.name}</span>
              <button
                type="button"
                className="session-signout-btn demo-exit-btn"
                onClick={handleSignOut}
                title={currentUser.isGuest ? "Exit Guest Session" : "Sign Out of Account"}
                aria-label={currentUser.isGuest ? "Exit Guest Session" : "Sign Out of Account"}
              >
                {currentUser.isGuest ? "Exit" : "Sign Out"}
              </button>
            </div>
          )}

          <div className="status">
            <span className="status-dot"></span>
            AI System Ready
          </div>
        </div>

      </header>

      <main className="main-content">

        {activeTab === "welcome" ? (
          <WelcomeView
            onGetStarted={() => {
              const hasSeenOnboarding = localStorage.getItem("has_seen_skin_onboarding");
              if (!hasSeenOnboarding) {
                setIsOnboardingOpen(true);
              } else {
                setActiveTab("analyze");
              }
            }}
            onExplore={() => setActiveTab("learn")}
            onLearnMore={() => setActiveTab("learn")}
            onNavigateTab={(tab) => setActiveTab(tab)}
          />
        ) : activeTab === "history" ? (
          <HistoryView onBackToAnalyze={() => setActiveTab("analyze")} />
        ) : activeTab === "learn" ? (
          <LearnView />
        ) : activeTab === "settings" ? (
          <SettingsView
            onClearHistorySuccess={() => {}}
            onReplayOnboarding={() => setIsOnboardingOpen(true)}
            onNavigateTab={(tab) => setActiveTab(tab)}
            reducedMotion={reducedMotion}
            onToggleReducedMotion={() => {
              setReducedMotion((prev) => {
                const nextVal = !prev;
                try {
                  localStorage.setItem("preferred_reduced_motion", String(nextVal));
                } catch (e) {
                  console.warn("Could not persist preferred_reduced_motion:", e);
                }
                return nextVal;
              });
            }}
          />
        ) : (
          <>
            {!result && (
              <section className="hero">
                <div className="hero-badge">
                  <ShieldCheck size={15} />
                  <span>AI-Assisted Dermatology Guidance</span>
                </div>

                <h2>
                  Understand your skin image
                  <span> with AI assistance.</span>
                </h2>

                <p>
                  Upload or capture a skin image for preliminary classification, Grad-CAM visual attention, and clinical safety triage.
                </p>
              </section>
            )}

            {result ? (
              <section className="results-section" aria-live="polite">
                {/* 1. URGENT / EMERGENCY ALERT (Highest Visual Priority) */}
                <EmergencyAlert
                  decision={result.decision}
                  safety={result.safety}
                />

                {/* 2. RESULTS TOP HEADER */}
                <div className="results-header">
                  <div>
                    <div className="results-preliminary-tag">
                      <ShieldCheck size={14} />
                      <span>PRELIMINARY AI ANALYSIS</span>
                    </div>
                    <h3>Preliminary Classification & Safety Assessment</h3>
                    <p className="results-subheading-text">
                      This result is an AI-assisted preliminary research analysis and is not a medical diagnosis or prescription.
                    </p>
                  </div>

                  <div className="results-actions-group">
                    <button
                      className="results-export-csv-btn"
                      onClick={handleExportCsv}
                      disabled={isExportingCsv}
                      type="button"
                      title="Export results as CSV"
                    >
                      <FileSpreadsheet size={15} />
                      <span>{isExportingCsv ? "Exporting..." : "CSV"}</span>
                    </button>

                    <button
                      className="results-download-pdf-btn"
                      onClick={handleDownloadPdf}
                      disabled={isDownloadingPdf}
                      type="button"
                      title="Download publication-quality PDF summary report"
                    >
                      <FileText size={15} />
                      <span>{isDownloadingPdf ? "Generating..." : "Download PDF Report"}</span>
                    </button>

                    <button
                      className="secondary-button"
                      onClick={handleNewImage}
                      type="button"
                    >
                      Analyze another image
                    </button>
                  </div>
                </div>

                {/* 3. PRIMARY PREDICTION OR DOMAIN ABSTENTION */}
                {result.analysis?.status === "abstained" || result.status === "abstained" ? (
                  <AbstentionCard
                    oodAssessment={result.ood_assessment}
                    uncertainty={result.uncertainty}
                    decision={result.decision}
                  />
                ) : (
                  <PredictionCard
                    prediction={result.prediction}
                    uncertainty={result.uncertainty}
                    fallbackDisplayName={result.display_name}
                    fallbackConfidencePercent={result.confidence_percent}
                    fallbackConfidenceLevel={result.confidence_level}
                  />
                )}

                {/* 4. OVERALL SAFETY ASSESSMENT & DECISION */}
                <SafetyDecisionCard
                  decision={result.decision}
                  safety={result.safety}
                />

                {/* 5. TOP-3 MODEL PREDICTIONS (Omitted during domain abstention) */}
                {!(result.analysis?.status === "abstained" || result.status === "abstained") && (
                  <TopPredictionsCard
                    topPredictions={result.top_predictions}
                  />
                )}

                {/* 6. IMAGE QUALITY ASSESSMENT */}
                <ImageQualityCard
                  imageQuality={result.image_quality}
                />

                {/* 7. REPORTED SYMPTOMS CONTEXT */}
                <ReportedSymptomsCard
                  symptoms={result.symptoms || symptoms}
                />

                {/* 8. DISEASE EDUCATIONAL INFORMATION (Omitted during domain abstention) */}
                {!(result.analysis?.status === "abstained" || result.status === "abstained") && (
                  <DiseaseInfoCard
                    diseaseInfo={result.disease_information}
                    fallbackDisplayName={result.prediction?.display_name || result.display_name}
                  />
                )}

                {/* 8b. CLASSICAL SYMPTOM REFERENCE (Omitted during domain abstention) */}
                {!(result.analysis?.status === "abstained" || result.status === "abstained") && result.symptom_reference && (
                  <ClassicalSymptomReferenceCard
                    symptomReference={result.symptom_reference}
                    predictedCategory={result.prediction?.display_name || result.display_name}
                  />
                )}

                {/* 9. GRAD-CAM VISUAL EXPLANATION & COMPARISON */}
                {result.gradcam_generated && (result.gradcam_url || result.heatmap_url) && (
                  <GradcamComparisonCard
                    originalImageUrl={previewUrl}
                    gradcamUrl={result.gradcam_url}
                    heatmapUrl={result.heatmap_url}
                  />
                )}

                {/* 10. GEMINI EDUCATIONAL EXPLANATION */}
                <EducationalExplanationCard
                  result={result}
                  isLoading={isGeminiLoading}
                  onRetry={() => generateGeminiExplanation(result)}
                />

                {/* 11. COMPREHENSIVE MEDICAL & SAFETY DISCLAIMER */}
                <div className="final-safety">
                  <ShieldCheck size={20} />
                  <div>
                    <strong>
                      Important Safety Information & Medical Disclaimer
                    </strong>
                    <p>
                      {result.medical_disclaimer ||
                        "This application provides preliminary educational guidance only. It cannot replace examination by a qualified dermatologist or healthcare professional."}
                    </p>
                  </div>
                </div>

                {/* 12. BOTTOM RESULTS RE-ENTRY BAR */}
                <div className="results-bottom-actions">
                  <button
                    className="secondary-button"
                    onClick={handleNewImage}
                    type="button"
                  >
                    Analyze another image
                  </button>
                  <button
                    className="results-download-pdf-btn"
                    onClick={handleDownloadPdf}
                    disabled={isDownloadingPdf}
                    type="button"
                    title="Download publication-quality PDF summary report"
                  >
                    <FileText size={15} />
                    <span>{isDownloadingPdf ? "Generating..." : "Download PDF Report"}</span>
                  </button>
                  <button
                    className="results-export-csv-btn"
                    onClick={handleExportCsv}
                    disabled={isExportingCsv}
                    type="button"
                    title="Export results as CSV"
                  >
                    <FileSpreadsheet size={15} />
                    <span>{isExportingCsv ? "Exporting..." : "Export CSV"}</span>
                  </button>
                </div>

              </section>
            ) : isReviewing ? (
              <PreAnalysisReviewCard
                selectedImage={selectedImage}
                previewUrl={previewUrl}
                imageDimensions={imageDimensions}
                imageSource={imageSource}
                symptoms={symptoms}
                imageQuality={null}
                isAnalyzing={isAnalyzing}
                error={error}
                onBackToEdit={handleBackToEdit}
                onAnalyze={handleAnalyze}
                onChangeImage={handleChangeImageFromReview}
                onRetakePhoto={handleRetakePhotoFromReview}
                onEditResponses={handleEditResponsesFromReview}
              />
            ) : (
              <section className="analysis-card" aria-busy={isAnalyzing}>
                <div className="card-header">
                  <div>
                    <h3>Analyze Skin Image</h3>
                    <p>Upload a clear image of the affected skin area.</p>
                  </div>
                  <ImageIcon size={24} />
                </div>

                <CaptureCoachingCard />

                {isCameraOpen ? (
                  <CameraCapture
                    onCapture={handleCameraCapture}
                    onCancel={handleCameraCancel}
                    disabled={isAnalyzing}
                  />
                ) : !previewUrl ? (
                  <div className="capture-selection-container">
                    <div className="capture-options-grid">
                      <button
                        className="upload-area upload-tile"
                        onClick={handleUploadClick}
                        type="button"
                        aria-label="Upload a skin image from computer"
                        disabled={isAnalyzing}
                      >
                        <div className="upload-icon">
                          <Upload size={26} />
                        </div>
                        <strong>Upload Image File</strong>
                        <span>Browse your computer</span>
                        <small>JPG, JPEG, PNG (max 10 MB)</small>
                      </button>

                      <button
                        className="upload-area camera-tile"
                        onClick={() => setIsCameraOpen(true)}
                        type="button"
                        aria-label="Take a photo with device camera"
                        disabled={isAnalyzing}
                      >
                        <div className="upload-icon camera-icon-bg">
                          <Camera size={26} />
                        </div>
                        <strong>Use Camera</strong>
                        <span>Capture live skin photo</span>
                        <small>Requires browser camera access</small>
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="preview-container">
                    <img
                      src={previewUrl}
                      alt="Selected skin image preview"
                      className="image-preview"
                    />

                    <div className="preview-info">
                      <strong>{selectedImage?.name}</strong>

                      <span>
                        {(selectedImage?.size / 1024 / 1024).toFixed(2)} MB
                        {imageDimensions && ` • ${imageDimensions.width} × ${imageDimensions.height} px`}
                      </span>

                      <div className="preview-action-buttons">
                        <button
                          className="secondary-button"
                          onClick={handleUploadClick}
                          type="button"
                          disabled={isAnalyzing}
                        >
                          Upload different file
                        </button>

                        <button
                          className="secondary-button"
                          onClick={() => setIsCameraOpen(true)}
                          type="button"
                          disabled={isAnalyzing}
                        >
                          Take new photo
                        </button>

                        <button
                          className="secondary-button remove-img-btn"
                          onClick={handleRemoveImage}
                          type="button"
                          disabled={isAnalyzing}
                          title="Remove selected image"
                          aria-label="Remove selected image"
                        >
                          <Trash2 size={13} aria-hidden="true" />
                          <span>Remove Photo</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/jpg"
                  aria-label="Upload skin image file"
                  onChange={handleFileChange}
                  hidden
                />

                <SymptomQuestionnaire
                  symptoms={symptoms}
                  onChange={setSymptoms}
                  onClear={() => setSymptoms(INITIAL_SYMPTOMS)}
                  disabled={isAnalyzing}
                  isOpen={questionnaireOpen}
                  onToggleOpen={setQuestionnaireOpen}
                />

                <div className="analysis-note">
                  <ShieldCheck size={18} />
                  <div className="analysis-note-text">
                    <strong>Educational & Privacy Notice:</strong>
                    <span>
                      Images are analyzed locally for preliminary guidance and safety triage. Raw images are never stored on external servers.
                    </span>
                  </div>
                </div>

                {error && (
                  <div className="error-message" role="alert" aria-live="assertive">
                    <AlertCircle size={17} />
                    <span>{error}</span>
                  </div>
                )}

                <div className="analysis-step-action-bar">
                  <button
                    className="analyze-button review-proceed-btn"
                    disabled={!selectedImage || isAnalyzing}
                    onClick={handleProceedToReview}
                    type="button"
                    aria-label="Review image and questionnaire details before starting analysis"
                  >
                    <ClipboardCheck size={18} />
                    <span>Review Before Analysis</span>
                  </button>

                  {!selectedImage && (
                    <p className="review-prereq-note">
                      Select or capture an image above to review details before starting analysis.
                    </p>
                  )}
                </div>
              </section>
            )}


        {!result && (

          <section className="feature-grid">

            <div className="feature-card">

              <div className="feature-icon">
                <Sparkles size={20} />
              </div>

              <h4>
                AI Classification
              </h4>

              <p>
                A trained CNN analyzes the uploaded
                image and provides a preliminary
                skin-condition classification.
              </p>

            </div>


            <div className="feature-card">

              <div className="feature-icon">
                <ImageIcon size={20} />
              </div>

              <h4>
                Visual Explanation
              </h4>

              <p>
                Grad-CAM highlights image regions
                that influenced the CNN prediction.
              </p>

            </div>


            <div className="feature-card">

              <div className="feature-icon">
                <ShieldCheck size={20} />
              </div>

              <h4>
                Safety First
              </h4>

              <p>
                Results are presented as preliminary
                educational guidance and not as a
                medical diagnosis.
              </p>

            </div>

          </section>

        )}

        </>
        )}

      </main>


      <footer>
        AI-Assisted Symptom Image Analysis and
        Preliminary Guidance
        <span>&bull;</span>
        Research Prototype
      </footer>

      {/* Demo Evaluation Login Modal (when opened within active workspace) */}
      <DemoLoginModal
        isOpen={isDemoModalOpen}
        isInitialGate={false}
        onClose={() => setIsDemoModalOpen(false)}
        onEnterDemo={(userInfo) => {
          setCurrentUser(userInfo);
          setIsDemoModalOpen(false);
        }}
      />

      {/* First-time Onboarding Modal */}
      <OnboardingModal
        isOpen={isOnboardingOpen}
        onClose={() => {
          setIsOnboardingOpen(false);
          setActiveTab("analyze");
        }}
        onComplete={() => {
          try {
            localStorage.setItem("has_seen_skin_onboarding", "true");
          } catch (e) {
            console.warn("Could not save onboarding status to localStorage:", e);
          }
          setIsOnboardingOpen(false);
          setActiveTab("analyze");
        }}
      />

      {/* MOBILE STICKY BOTTOM NAVIGATION BAR */}
      <nav className="mobile-bottom-nav" role="navigation" aria-label="Mobile Navigation">
        <button
          type="button"
          className={`mobile-nav-btn ${activeTab === "welcome" ? "active" : ""}`}
          onClick={() => setActiveTab("welcome")}
          aria-label="Welcome screen"
          aria-selected={activeTab === "welcome"}
        >
          <Home size={19} aria-hidden="true" />
          <span>Welcome</span>
        </button>

        <button
          type="button"
          className={`mobile-nav-btn ${activeTab === "analyze" ? "active" : ""}`}
          onClick={() => setActiveTab("analyze")}
          aria-label="Analyze screen"
          aria-selected={activeTab === "analyze"}
        >
          <Sparkles size={19} aria-hidden="true" />
          <span>Analyze</span>
        </button>

        <button
          type="button"
          className={`mobile-nav-btn ${activeTab === "history" ? "active" : ""}`}
          onClick={() => setActiveTab("history")}
          aria-label="History timeline"
          aria-selected={activeTab === "history"}
        >
          <HistoryIcon size={19} aria-hidden="true" />
          <span>History</span>
        </button>

        <button
          type="button"
          className={`mobile-nav-btn ${activeTab === "learn" ? "active" : ""}`}
          onClick={() => setActiveTab("learn")}
          aria-label="Learn educational library"
          aria-selected={activeTab === "learn"}
        >
          <BookOpen size={19} aria-hidden="true" />
          <span>Learn</span>
        </button>

        <button
          type="button"
          className={`mobile-nav-btn ${activeTab === "settings" ? "active" : ""}`}
          onClick={() => setActiveTab("settings")}
          aria-label="Settings and privacy"
          aria-selected={activeTab === "settings"}
        >
          <SettingsIcon size={19} aria-hidden="true" />
          <span>Settings</span>
        </button>
      </nav>
    </div>
  );
}

export default App;





