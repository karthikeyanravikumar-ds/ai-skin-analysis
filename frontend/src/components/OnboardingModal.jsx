import { useState, useEffect } from "react";
import {
  X,
  Camera,
  ClipboardList,
  Activity,
  ShieldAlert,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
} from "lucide-react";

const ONBOARDING_STEPS = [
  {
    step: 1,
    title: "Prepare a Clear Image",
    icon: Camera,
    headline: "High visual fidelity enables accurate AI feature extraction",
    description:
      "For reliable preliminary screening, position your camera 10–15 cm from the affected skin area under bright, natural, non-glaring lighting. Avoid severe shadows, motion blur, and extreme close-ups.",
    tips: [
      "Ensure the lesion or skin rash is centered and in sharp focus.",
      "Avoid flash glare and heavy filtering.",
      "The model supports photograph inputs (JPG, JPEG, PNG).",
    ],
  },
  {
    step: 2,
    title: "Provide Contextual Symptoms",
    icon: ClipboardList,
    headline: "Clinical context refines safety triage boundaries",
    description:
      "An optional structured symptom questionnaire lets you report itching, pain, rapid progression, systemic symptoms, or bleeding. User-reported symptoms guide deterministic safety gates.",
    tips: [
      "Select 'Yes', 'No', or 'Unsure' for each symptom.",
      "Symptoms are evaluated alongside neural network visual features.",
      "Emergency indicators prompt immediate clinical medical attention.",
    ],
  },
  {
    step: 3,
    title: "Understand the Result",
    icon: Activity,
    headline: "Interpret model confidence and visual attention critically",
    description:
      "Results present the top predicted conditions out of 7 supported classes, alongside softmax confidence, image-quality verification, and interactive Grad-CAM heatmap visualizations.",
    tips: [
      "Grad-CAM highlights image regions influencing the CNN prediction.",
      "High model confidence does not guarantee clinical diagnosis.",
      "Inputs outside the 7 classes trigger safe out-of-distribution abstention.",
    ],
  },
  {
    step: 4,
    title: "Use Information Responsibly",
    icon: ShieldAlert,
    headline: "AI screening is educational, not diagnostic",
    description:
      "This application is an educational and research platform. Its predictions are not clinical diagnoses and must never replace an evaluation or biopsy performed by a qualified dermatologist or physician.",
    tips: [
      "Always consult a licensed healthcare professional for medical concerns.",
      "High-risk flags require prompt in-person clinical care.",
      "Anonymous analysis records can be exported or cleared anytime in Settings.",
    ],
  },
];

export default function OnboardingModal({ isOpen, onClose, onComplete }) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const handleCloseModal = () => {
    setCurrentStepIndex(0);
    onClose();
  };

  const handleCompleteModal = () => {
    setCurrentStepIndex(0);
    onComplete();
  };

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        setCurrentStepIndex(0);
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const currentStep = ONBOARDING_STEPS[currentStepIndex];
  const isLastStep = currentStepIndex === ONBOARDING_STEPS.length - 1;
  const IconComponent = currentStep.icon;

  const handleNext = () => {
    if (isLastStep) {
      handleCompleteModal();
    } else {
      setCurrentStepIndex((prev) => Math.min(prev + 1, ONBOARDING_STEPS.length - 1));
    }
  };

  const handlePrev = () => {
    setCurrentStepIndex((prev) => Math.max(prev - 1, 0));
  };

  return (
    <div
      className="history-modal-backdrop"
      onClick={handleCloseModal}
      role="dialog"
      aria-modal="true"
      aria-labelledby="onboarding-step-title"
    >
      <div
        className="history-modal-content onboarding-modal-box"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header">
          <div>
            <div className="modal-preliminary-tag">
              <span>STEP {currentStep.step} OF {ONBOARDING_STEPS.length}</span>
            </div>
            <h3 id="onboarding-step-title" className="modal-title">
              {currentStep.title}
            </h3>
          </div>

          <button
            type="button"
            className="modal-close-btn"
            onClick={handleCloseModal}
            aria-label="Skip onboarding"
            title="Skip onboarding tutorial"
          >
            <X size={20} />
          </button>
        </div>

        {/* Progress Tracker Bar */}
        <div className="onboarding-progress-track" aria-hidden="true">
          {ONBOARDING_STEPS.map((s, idx) => (
            <div
              key={s.step}
              className={`onboarding-progress-bar ${
                idx <= currentStepIndex ? "active" : ""
              }`}
            />
          ))}
        </div>

        {/* Content Body */}
        <div className="modal-body onboarding-modal-body">
          <div className="onboarding-icon-header">
            <div className="onboarding-icon-bubble">
              <IconComponent size={26} />
            </div>
            <h4 className="onboarding-headline">{currentStep.headline}</h4>
          </div>

          <p className="onboarding-description">{currentStep.description}</p>

          <div className="onboarding-tips-card">
            <strong className="onboarding-tips-heading">Key Recommendations:</strong>
            <ul className="onboarding-tips-list">
              {currentStep.tips.map((tip, idx) => (
                <li key={idx}>
                  <CheckCircle2 size={14} className="tip-check-icon" />
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="modal-footer onboarding-footer">
          <button
            type="button"
            className="secondary-button"
            onClick={handleCloseModal}
          >
            Skip Onboarding
          </button>

          <div className="onboarding-nav-btns">
            {currentStepIndex > 0 && (
              <button
                type="button"
                className="secondary-button"
                onClick={handlePrev}
                aria-label="Previous onboarding step"
              >
                <ArrowLeft size={15} />
                <span>Previous</span>
              </button>
            )}

            <button
              type="button"
              className="welcome-btn-primary"
              onClick={handleNext}
              aria-label={isLastStep ? "Complete onboarding and begin analysis" : "Next onboarding step"}
            >
              <span>{isLastStep ? "Start Analysis" : "Continue"}</span>
              <ArrowRight size={15} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
