import React, { useRef, useState, useEffect, useCallback } from "react";
import { Camera, RefreshCw, X, CameraOff, Check } from "lucide-react";

/**
 * CameraCapture handles live browser camera stream, frame capture,
 * permission handling, error fallback, retake, and resource cleanup (FR-02).
 */
export default function CameraCapture({ onCapture, onCancel, disabled = false }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const previewUrlRef = useRef("");

  const [cameraState, setCameraState] = useState("initializing"); // "initializing" | "ready" | "denied" | "unsupported" | "error" | "captured"
  const [errorMessage, setErrorMessage] = useState("");
  const [capturedBlob, setCapturedBlob] = useState(null);
  const [capturedPreviewUrl, setCapturedPreviewUrl] = useState("");

  const stopActiveStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch (e) {
          console.warn("[CAMERA] Error stopping track:", e);
        }
      });
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  const initializeCamera = useCallback(async () => {
    stopActiveStream();
    setErrorMessage("");
    setCameraState("initializing");

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraState("unsupported");
      setErrorMessage("Your browser does not support camera capture. Please use the file upload option instead.");
      return;
    }

    try {
      const constraints = {
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current
            .play()
            .then(() => setCameraState("ready"))
            .catch((err) => {
              console.error("[CAMERA] Play error:", err);
              setCameraState("error");
              setErrorMessage("Unable to start video preview. Please try again or upload a photo.");
            });
        };
      } else {
        setCameraState("ready");
      }
    } catch (err) {
      console.warn("[CAMERA] getUserMedia error:", err);
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setCameraState("denied");
        setErrorMessage("Camera access was denied. Please allow camera permissions in your browser settings or use file upload.");
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        setCameraState("error");
        setErrorMessage("No camera hardware detected on this device. Please upload an image file instead.");
      } else if (err.name === "NotReadableError" || err.name === "TrackStartError") {
        setCameraState("error");
        setErrorMessage("The camera is currently in use by another application. Please close other camera apps, retry, or upload an image file instead.");
      } else {
        setCameraState("error");
        setErrorMessage(err.message || "Failed to initialize camera. Please use file upload.");
      }
    }
  }, [stopActiveStream]);

  // Keep previewUrlRef in sync
  useEffect(() => {
    previewUrlRef.current = capturedPreviewUrl;
  }, [capturedPreviewUrl]);

  useEffect(() => {
    let isCancelled = false;
    const start = async () => {
      if (!isCancelled) {
        await initializeCamera();
      }
    };
    start();
    return () => {
      isCancelled = true;
      stopActiveStream();
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current);
      }
    };
  }, [initializeCamera, stopActiveStream]);

  const handleCaptureFrame = () => {
    if (!videoRef.current || cameraState !== "ready") return;

    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    const width = video.videoWidth || 640;
    const height = video.videoHeight || 480;

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      setErrorMessage("Failed to acquire 2D rendering context for frame capture.");
      return;
    }

    ctx.drawImage(video, 0, 0, width, height);

    canvas.toBlob(
      (blob) => {
        if (!blob || blob.size === 0) {
          setErrorMessage("Failed to capture a valid frame from the camera.");
          return;
        }

        // Stop live preview tracks once captured to release hardware
        stopActiveStream();

        const file = new File([blob], `camera_capture_${Date.now()}.jpg`, {
          type: "image/jpeg",
          lastModified: Date.now(),
        });

        const preview = URL.createObjectURL(blob);
        setCapturedBlob(file);
        setCapturedPreviewUrl(preview);
        setCameraState("captured");
      },
      "image/jpeg",
      0.92
    );
  };

  const handleRetake = () => {
    if (capturedPreviewUrl) {
      URL.revokeObjectURL(capturedPreviewUrl);
      setCapturedPreviewUrl("");
    }
    setCapturedBlob(null);
    initializeCamera();
  };

  const handleConfirmUse = () => {
    if (capturedBlob && onCapture) {
      onCapture(capturedBlob, capturedPreviewUrl);
    }
  };

  const handleExit = () => {
    stopActiveStream();
    if (capturedPreviewUrl) {
      URL.revokeObjectURL(capturedPreviewUrl);
    }
    if (onCancel) {
      onCancel();
    }
  };

  return (
    <div className="camera-capture-container" role="region" aria-label="Camera capture mode">
      <div className="camera-header">
        <div className="camera-title">
          <Camera size={18} aria-hidden="true" />
          <span>Take a Photo with Camera</span>
        </div>
        <button
          type="button"
          className="camera-close-btn"
          onClick={handleExit}
          disabled={disabled}
          aria-label="Cancel camera and return to file upload"
        >
          <X size={18} />
        </button>
      </div>

      <div className="camera-viewfinder-box">
        {cameraState === "initializing" && (
          <div className="camera-status-msg" aria-live="polite">
            <RefreshCw size={24} className="spin" aria-hidden="true" />
            <p>Requesting camera access...</p>
          </div>
        )}

        {(cameraState === "denied" || cameraState === "unsupported" || cameraState === "error") && (
          <div className="camera-error-banner" role="alert" aria-live="assertive">
            <CameraOff size={28} className="camera-err-icon" aria-hidden="true" />
            <strong>Unable to access camera</strong>
            <p>{errorMessage}</p>
            <div className="camera-fallback-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={handleExit}
              >
                Return to File Upload
              </button>
              {cameraState !== "unsupported" && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={initializeCamera}
                >
                  Retry Camera
                </button>
              )}
            </div>
          </div>
        )}

        <video
          ref={videoRef}
          playsInline
          muted
          className={`camera-video-stream ${cameraState === "ready" ? "visible" : "hidden"}`}
          aria-label="Live camera viewfinder"
        />

        {cameraState === "captured" && (
          <div className="camera-captured-preview">
            <img
              src={capturedPreviewUrl}
              alt="Captured skin lesion"
              className="captured-image-tag"
            />
          </div>
        )}

        {cameraState === "ready" && (
          <div className="viewfinder-overlay" aria-hidden="true">
            <div className="viewfinder-reticle"></div>
            <span className="viewfinder-hint">Position skin lesion centrally in frame</span>
          </div>
        )}
      </div>

      <div className="camera-controls">
        {cameraState === "ready" && (
          <div className="camera-actions-row">
            <button
              type="button"
              className="cancel-action-btn"
              onClick={handleExit}
              disabled={disabled}
            >
              Cancel
            </button>
            <button
              type="button"
              className="shutter-button"
              onClick={handleCaptureFrame}
              disabled={disabled}
              aria-label="Capture photo"
            >
              <div className="shutter-inner"></div>
            </button>
            <div className="camera-spacer"></div>
          </div>
        )}

        {cameraState === "captured" && (
          <div className="camera-captured-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={handleRetake}
              disabled={disabled}
              aria-label="Retake photo and restart camera viewfinder"
            >
              <RefreshCw size={15} aria-hidden="true" />
              <span>Retake</span>
            </button>
            <button
              type="button"
              className="primary-button-confirm"
              onClick={handleConfirmUse}
              disabled={disabled}
              aria-label="Confirm and use this captured photo for analysis"
            >
              <Check size={16} aria-hidden="true" />
              <span>Use This Photo</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
