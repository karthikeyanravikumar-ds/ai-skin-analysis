"""
Educational Analysis Report Generator Module.

Generates self-contained PDF summary reports and sanitized CSV exports from
existing analysis responses or stored history records.

Guarantees:
1. Pure report generation: NEVER re-executes CNN inference or PyTorch models.
2. Complete inclusion of triage safety decisions, top predictions, uncertainty,
   image quality metrics, user-reported symptoms, and educational guidance.
3. Strict non-diagnostic disclaimer and limitation notices.
4. Formula injection protection for CSV exports.
5. No internal server secrets, raw image bytes, or private API keys in output.
"""

import csv
import io
import math
import os
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, FancyBboxPatch

from ai.safety.guidelines import SAFETY_DISCLAIMER
from ai.safety.disease_info import get_disease_information
try:
    from ai.reference.symptom_reference import get_symptom_reference
except Exception:
    get_symptom_reference = lambda *args, **kwargs: None


def _sanitize_csv_value(value: Any) -> str:
    """
    Sanitize text against spreadsheet formula injection (=, +, -, @, \\t, \\r).
    """
    if value is None:
        return ""
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{text}"
    return text


def _extract_confidence(data: Dict[str, Any]) -> tuple[float, float, str]:
    """Extract (confidence_value_0_to_1, confidence_percent_0_to_100, confidence_level_str)."""
    conf_obj = data.get("confidence")
    pred_obj = data.get("prediction") if isinstance(data.get("prediction"), dict) else {}

    val = None
    pct = None
    lvl = None

    if isinstance(conf_obj, dict):
        val = conf_obj.get("value")
        pct = conf_obj.get("percent")
        lvl = conf_obj.get("level")
    elif isinstance(conf_obj, (int, float)):
        val = float(conf_obj)

    if val is None and isinstance(pred_obj, dict):
        val = pred_obj.get("confidence")
    if pct is None and isinstance(pred_obj, dict):
        pct = pred_obj.get("confidence_percent")
    if lvl is None and isinstance(pred_obj, dict):
        lvl = pred_obj.get("confidence_level")

    if pct is None and data.get("confidence_percent") is not None:
        pct = data.get("confidence_percent")
    if lvl is None and data.get("confidence_level") is not None:
        lvl = data.get("confidence_level")

    # Safe float conversions
    if pct is not None:
        try:
            pct = float(pct)
            if val is None:
                val = pct / 100.0 if pct > 1.0 else pct
        except (ValueError, TypeError):
            pct = 0.0

    if val is not None:
        try:
            val = float(val)
            if pct is None:
                pct = val * 100.0 if val <= 1.0 else val
        except (ValueError, TypeError):
            val = 0.0
            pct = 0.0

    if val is None:
        val = 0.0
    if pct is None:
        pct = 0.0
    if not lvl:
        lvl = "high" if pct >= 80 else ("moderate" if pct >= 50 else "low")

    return float(val), float(pct), str(lvl).strip().lower()


def _extract_prediction(data: Dict[str, Any]) -> tuple[str, str]:
    """Extract (class_name, display_name)."""
    pred_obj = data.get("prediction")
    if isinstance(pred_obj, dict):
        p_class = pred_obj.get("class_name") or pred_obj.get("prediction") or data.get("prediction") or "unknown"
        d_name = pred_obj.get("display_name") or data.get("display_name") or str(p_class).replace("_", " ").title()
        return str(p_class), str(d_name)
    if isinstance(pred_obj, str) and pred_obj.strip():
        p_class = pred_obj.strip()
        d_name = str(data.get("display_name") or p_class.replace("_", " ").title()).strip()
        return p_class, d_name
    p_class = str(data.get("prediction", "unknown")).strip()
    d_name = str(data.get("display_name", p_class.replace("_", " ").title())).strip()
    return p_class, d_name


def generate_analysis_csv(records: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
    """
    Generate sanitized, formula-injection-safe CSV string from one or more analysis records.
    Does NOT include private API keys or internal server paths.
    """
    if isinstance(records, dict):
        record_list = [records]
    elif isinstance(records, (list, tuple)):
        record_list = list(records)
    else:
        raise ValueError("records must be a dictionary or list of dictionaries")

    output = io.StringIO()
    fieldnames = [
        "record_id",
        "timestamp",
        "model_version",
        "prediction_class",
        "display_name",
        "confidence_percent",
        "confidence_level",
        "image_quality_status",
        "safety_level",
        "decision_level",
        "requires_professional_evaluation",
        "is_emergency",
        "is_preliminary",
        "reported_symptoms",
        "classical_reference_features",
        "classical_distinctive_clue",
        "classical_interpretation_limit",
        "medical_disclaimer",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()

    for item in record_list:
        if not isinstance(item, dict):
            continue

        rec_id = item.get("record_id") or item.get("id") or item.get("analysis_id", "N/A")
        ts = item.get("timestamp") or item.get("created_at", "")
        model_ver = item.get("model_version") or "EfficientNet-B0 v2.0"

        pred_class, disp_name = _extract_prediction(item)
        conf_val, conf_pct, conf_lvl = _extract_confidence(item)

        iq_info = item.get("image_quality", {})
        iq_status = iq_info.get("status") if isinstance(iq_info, dict) else item.get("image_quality_status", "unknown")

        safety_info = item.get("safety", {})
        saf_level = safety_info.get("level") if isinstance(safety_info, dict) else item.get("safety_level", "routine")

        dec_info = item.get("decision", {})
        if isinstance(dec_info, dict):
            dec_level = dec_info.get("level") or dec_info.get("safety_level", "routine")
            req_eval = dec_info.get("requires_professional_evaluation", False)
            is_emerg = dec_info.get("is_emergency", False)
        else:
            dec_level = item.get("decision_level", "routine")
            req_eval = item.get("requires_professional_evaluation", False)
            is_emerg = item.get("is_emergency", False)

        is_prelim = item.get("is_preliminary", item.get("preliminary", True))

        # Format symptoms summary
        symptoms_data = item.get("symptoms") or item.get("reported_symptoms")
        if isinstance(symptoms_data, dict):
            active_symptoms = [k.replace("_", " ").title() for k, v in symptoms_data.items() if v is True or v == "true" or v == 1]
            symptoms_str = "; ".join(active_symptoms) if active_symptoms else "None reported"
        elif isinstance(symptoms_data, list):
            symptoms_str = "; ".join(str(s) for s in symptoms_data)
        elif isinstance(symptoms_data, str) and symptoms_data.strip():
            symptoms_str = symptoms_data.strip()
        else:
            symptoms_str = "None reported"

        # Classical symptom reference (Task INT-CSV-01)
        sym_ref = item.get("symptom_reference")
        if not sym_ref and pred_class:
            try:
                sym_ref = get_symptom_reference(pred_class)
            except Exception:
                sym_ref = None

        ref_features = sym_ref.get("typical_lesion_features", "") if isinstance(sym_ref, dict) else ""
        ref_clue = sym_ref.get("distinctive_clue", "") if isinstance(sym_ref, dict) else ""
        ref_limit = sym_ref.get("interpretation_limit", "") if isinstance(sym_ref, dict) else ""

        row = {
            "record_id": _sanitize_csv_value(rec_id),
            "timestamp": _sanitize_csv_value(ts),
            "model_version": _sanitize_csv_value(model_ver),
            "prediction_class": _sanitize_csv_value(pred_class),
            "display_name": _sanitize_csv_value(disp_name),
            "confidence_percent": _sanitize_csv_value(f"{conf_pct:.2f}"),
            "confidence_level": _sanitize_csv_value(conf_lvl),
            "image_quality_status": _sanitize_csv_value(iq_status),
            "safety_level": _sanitize_csv_value(saf_level),
            "decision_level": _sanitize_csv_value(dec_level),
            "requires_professional_evaluation": _sanitize_csv_value(req_eval),
            "is_emergency": _sanitize_csv_value(is_emerg),
            "is_preliminary": _sanitize_csv_value(is_prelim),
            "reported_symptoms": _sanitize_csv_value(symptoms_str),
            "classical_reference_features": _sanitize_csv_value(ref_features),
            "classical_distinctive_clue": _sanitize_csv_value(ref_clue),
            "classical_interpretation_limit": _sanitize_csv_value(ref_limit),
            "medical_disclaimer": _sanitize_csv_value(SAFETY_DISCLAIMER),
        }
        writer.writerow(row)

    return output.getvalue()



def generate_analysis_pdf(
    data: Dict[str, Any],
    output_path: Optional[Union[str, Path]] = None,
    gradcam_image_path: Optional[Union[str, Path]] = None
) -> bytes:
    """
    Generate a formatted, publication-quality PDF summary report from an existing analysis dictionary.
    Does NOT rerun CNN inference or any model weights.
    """
    if not isinstance(data, dict):
        raise ValueError("data must be a dictionary")

    # Extract core fields safely
    record_id = str(data.get("record_id") or data.get("id") or data.get("analysis_id", "ANON-ANALYSIS")).strip()
    analysis_ts = str(data.get("timestamp") or data.get("created_at", datetime.now(timezone.utc).isoformat())).strip()
    report_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    model_version = str(data.get("model_version", "EfficientNet-B0 v2.0")).strip()

    # Prediction & Confidence
    pred_class, disp_name = _extract_prediction(data)
    conf_val, conf_pct, conf_lvl = _extract_confidence(data)

    # Top predictions

    top_preds = data.get("top_predictions", [])
    if not isinstance(top_preds, (list, tuple)):
        top_preds = []

    # Image quality
    iq_obj = data.get("image_quality", {})
    iq_status = str(iq_obj.get("status") if isinstance(iq_obj, dict) else data.get("image_quality_status", "good")).strip()

    # Safety & Decision
    safety_obj = data.get("safety", {})
    saf_lvl = str(safety_obj.get("level") if isinstance(safety_obj, dict) else data.get("safety_level", "routine")).strip().lower()

    dec_obj = data.get("decision", {})
    if isinstance(dec_obj, dict):
        dec_lvl = str(dec_obj.get("level") or dec_obj.get("safety_level", "routine")).strip().lower()
        req_eval = bool(dec_obj.get("requires_professional_evaluation", False))
        is_emerg = bool(dec_obj.get("is_emergency", False))
        dec_guidance = dec_obj.get("recommendation", "")
    else:
        dec_lvl = str(data.get("decision_level", "routine")).strip().lower()
        req_eval = bool(data.get("requires_professional_evaluation", False))
        is_emerg = bool(data.get("is_emergency", False))
        dec_guidance = ""

    # Symptoms
    symptoms_obj = data.get("symptoms") or data.get("reported_symptoms", {})
    reported_symptoms_list: List[str] = []
    if isinstance(symptoms_obj, dict):
        for k, v in symptoms_obj.items():
            if v is True or v == "true" or v == 1 or v == "yes":
                reported_symptoms_list.append(k.replace("_", " ").title())
            elif (k in ("duration", "location")) and isinstance(v, str) and v.strip():
                reported_symptoms_list.append(f"{k.title()}: {v.strip()}")
    elif isinstance(symptoms_obj, list):
        reported_symptoms_list = [str(s).replace("_", " ").title() for s in symptoms_obj if s]
    elif isinstance(symptoms_obj, str) and symptoms_obj.strip():
        reported_symptoms_list = [s.strip() for s in symptoms_obj.split(";") if s.strip()]

    # Disease info
    try:
        disease_info = get_disease_information(pred_class) or {}
    except Exception:
        disease_info = {}

    # Educational explanation if provided
    explanation_text = str(data.get("explanation") or "").strip()

    # Classical symptom reference (Task INT-CSV-01)
    symptom_ref = data.get("symptom_reference")
    if not symptom_ref and pred_class:
        try:
            symptom_ref = get_symptom_reference(pred_class)
        except Exception:
            symptom_ref = None

    # Build PDF with Matplotlib
    pdf_buffer = io.BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        # Page 1: Comprehensive Summary Report
        fig = plt.figure(figsize=(8.5, 11), dpi=150)
        fig.patch.set_facecolor("#ffffff")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()

        # Top Header Banner
        ax.add_patch(Rectangle((0, 0.91), 1, 0.09, facecolor="#0f172a", edgecolor="none"))
        ax.text(0.05, 0.955, "AI SKIN ANALYSIS", color="#38bdf8", fontsize=15, fontweight="bold", va="center")
        ax.text(0.05, 0.93, "Preliminary Educational & Research Summary Report", color="#e2e8f0", fontsize=10.5, va="center")
        ax.text(0.95, 0.942, f"MODEL: {model_version}", color="#94a3b8", fontsize=9, fontweight="bold", ha="right", va="center")

        # Metadata Row
        y = 0.885
        ax.text(0.05, y, f"Report Date: {report_ts}", color="#475569", fontsize=8.5)
        ax.text(0.50, y, f"Analysis Date: {analysis_ts}", color="#475569", fontsize=8.5)
        ax.text(0.95, y, f"ID: {record_id[:18]}...", color="#475569", fontsize=8.5, ha="right")

        # Divider
        y -= 0.015
        ax.plot([0.05, 0.95], [y, y], color="#cbd5e1", lw=0.8)

        # 1. Primary Classification Box
        y -= 0.035
        card_bg = "#f8fafc"
        ax.add_patch(FancyBboxPatch((0.05, y - 0.08), 0.90, 0.095, boxstyle="round,pad=0.01,rounding_size=0.015",
                                    facecolor=card_bg, edgecolor="#cbd5e1", lw=1))
        ax.text(0.07, y, "PRELIMINARY AI ESTIMATE", color="#64748b", fontsize=8, fontweight="bold")
        ax.text(0.07, y - 0.035, disp_name, color="#0f172a", fontsize=16, fontweight="bold")
        ax.text(0.07, y - 0.065, f"Estimated Class: {pred_class} | Confidence: {conf_pct:.2f}% ({conf_lvl.title()})",
                color="#334155", fontsize=9.5)

        # Confidence Badge
        badge_color = "#16a34a" if conf_lvl == "high" else ("#d97706" if conf_lvl == "moderate" else "#dc2626")
        ax.add_patch(FancyBboxPatch((0.74, y - 0.055), 0.19, 0.05, boxstyle="round,pad=0.008,rounding_size=0.01",
                                    facecolor=badge_color, edgecolor="none"))
        ax.text(0.835, y - 0.03, f"{conf_pct:.1f}% Confidence", color="#ffffff", fontsize=9.5, fontweight="bold", ha="center", va="center")

        # 2. Safety Assessment & Triage
        y -= 0.125
        triage_bg = "#fef2f2" if is_emerg or dec_lvl == "urgent" else ("#fffbeb" if dec_lvl == "attention" else "#f0fdf4")
        triage_border = "#fca5a5" if is_emerg or dec_lvl == "urgent" else ("#fde68a" if dec_lvl == "attention" else "#bbf7d0")
        triage_title = "URGENT CLINICAL EVALUATION RECOMMENDED" if is_emerg or dec_lvl == "urgent" else (
            "ATTENTION ADVISED — MONITOR SYMPTOMS" if dec_lvl == "attention" else "ROUTINE PRELIMINARY GUIDANCE"
        )
        triage_color = "#991b1b" if is_emerg or dec_lvl == "urgent" else ("#92400e" if dec_lvl == "attention" else "#166534")

        ax.add_patch(FancyBboxPatch((0.05, y - 0.075), 0.90, 0.085, boxstyle="round,pad=0.01,rounding_size=0.015",
                                    facecolor=triage_bg, edgecolor=triage_border, lw=1))
        ax.text(0.07, y, f"SAFETY TRIAGE DECISION: {triage_title}", color=triage_color, fontsize=10, fontweight="bold")
        eval_txt = "Professional Medical Evaluation: RECOMMENDED" if req_eval else "Professional Evaluation: Routine Educational Review"
        ax.text(0.07, y - 0.025, eval_txt, color=triage_color, fontsize=9, fontweight="bold")
        if dec_guidance:
            guidance_wrapped = textwrap.shorten(dec_guidance, width=105, placeholder="...")
            ax.text(0.07, y - 0.055, guidance_wrapped, color="#334155", fontsize=8.5)
        else:
            ax.text(0.07, y - 0.055, "This assessment is non-diagnostic. Consult a licensed dermatologist for any concerning skin lesion.",
                    color="#334155", fontsize=8.5)

        # 3. Two-Column Data Section (Top-3 Predictions & User Symptoms)
        y -= 0.115
        col_w = 0.435

        # Left Column: Top-3 Candidate Predictions
        ax.add_patch(FancyBboxPatch((0.05, y - 0.14), col_w, 0.145, boxstyle="round,pad=0.01,rounding_size=0.015",
                                    facecolor="#ffffff", edgecolor="#e2e8f0", lw=1))
        ax.text(0.07, y - 0.005, "TOP CANDIDATE PREDICTIONS", color="#475569", fontsize=8.5, fontweight="bold")
        py = y - 0.035
        if top_preds:
            for rank, tp in enumerate(top_preds[:3], 1):
                c_name = str(tp.get("class_name", "")).replace("_", " ").title()
                p_val = float(tp.get("probability", 0.0))
                p_pct = float(tp.get("probability_percent", p_val * 100.0))
                ax.text(0.07, py, f"#{rank} {c_name}", color="#0f172a", fontsize=9, fontweight="bold")
                ax.text(0.05 + col_w - 0.02, py, f"{p_pct:.2f}%", color="#2563eb", fontsize=9, fontweight="bold", ha="right")
                # Bar
                ax.add_patch(Rectangle((0.07, py - 0.015), (col_w - 0.04) * min(1.0, max(0.0, p_val)), 0.005,
                                       facecolor="#3b82f6", edgecolor="none"))
                py -= 0.035
        else:
            ax.text(0.07, py, f"#1 {disp_name}: {conf_pct:.2f}%", color="#0f172a", fontsize=9)

        # Right Column: User-Reported Symptoms & Quality
        rx = 0.05 + col_w + 0.03
        ax.add_patch(FancyBboxPatch((rx, y - 0.14), col_w, 0.145, boxstyle="round,pad=0.01,rounding_size=0.015",
                                    facecolor="#ffffff", edgecolor="#e2e8f0", lw=1))
        ax.text(rx + 0.02, y - 0.005, "REPORTED SYMPTOMS (USER ATTRIBUTED)", color="#475569", fontsize=8.5, fontweight="bold")
        sy = y - 0.035
        if reported_symptoms_list:
            for sym in reported_symptoms_list[:3]:
                ax.text(rx + 0.02, sy, f"* {sym}", color="#0f172a", fontsize=8.5)
                sy -= 0.022
            if len(reported_symptoms_list) > 3:
                ax.text(rx + 0.02, sy, f"* +{len(reported_symptoms_list) - 3} more symptoms", color="#64748b", fontsize=8)
        else:
            ax.text(rx + 0.02, sy, "No acute symptom red flags reported by user.", color="#64748b", fontsize=8.5, style="italic")

        # Image Quality Info
        ax.text(rx + 0.02, y - 0.115, f"Image Quality Status: {iq_status.upper()}", color="#0f172a", fontsize=8.5, fontweight="bold")

        # 4. Educational Overview & Classical Symptom Reference
        y -= 0.175
        ax.add_patch(FancyBboxPatch((0.05, y - 0.13), 0.90, 0.135, boxstyle="round,pad=0.01,rounding_size=0.015",
                                    facecolor="#f8fafc", edgecolor="#e2e8f0", lw=1))
        ax.text(0.07, y - 0.005, "EDUCATIONAL DISEASE INFORMATION & CLASSICAL REFERENCE", color="#475569", fontsize=8.5, fontweight="bold")

        ey = y - 0.026
        if symptom_ref and isinstance(symptom_ref, dict):
            ref_name = symptom_ref.get("disease_name", disp_name)
            ref_feat = symptom_ref.get("typical_lesion_features", "")
            ref_clue = symptom_ref.get("distinctive_clue", "")
            ref_safety = symptom_ref.get("safety_note", "")
            ref_limit = symptom_ref.get("interpretation_limit", "")

            ax.text(0.07, ey, f"Classical Reference ({ref_name}): {textwrap.shorten(ref_feat, width=88)}", color="#0f172a", fontsize=8.0, fontweight="bold")
            ey -= 0.018
            if ref_clue:
                ax.text(0.07, ey, f"Distinctive Clue: {textwrap.shorten(ref_clue, width=95)}", color="#1e293b", fontsize=7.8)
                ey -= 0.018
            if ref_safety:
                ax.text(0.07, ey, f"Safety Note: {textwrap.shorten(ref_safety, width=95)}", color="#991b1b", fontsize=7.8)
                ey -= 0.018
            if ref_limit:
                ax.text(0.07, ey, f"Interpretation Limit: {textwrap.shorten(ref_limit, width=95)}", color="#64748b", fontsize=7.8, style="italic")
                ey -= 0.018
        else:
            desc = disease_info.get("description", "Preliminary educational summary.")
            desc_wrapped = textwrap.wrap(desc, width=108)
            for line in desc_wrapped[:3]:
                ax.text(0.07, ey, line, color="#1e293b", fontsize=8.2)
                ey -= 0.018

            when_see = disease_info.get("when_to_see_doctor", "")
            if when_see:
                ax.text(0.07, ey - 0.005, f"When to see a doctor: {textwrap.shorten(when_see, width=100)}",
                        color="#0f172a", fontsize=8.2, fontweight="bold")

        # 5. Non-Diagnostic Medical Disclaimer (Crucial Safety Box)
        y -= 0.165
        ax.add_patch(FancyBboxPatch((0.05, y - 0.08), 0.90, 0.085, boxstyle="round,pad=0.01,rounding_size=0.015",
                                    facecolor="#fff7ed", edgecolor="#fed7aa", lw=1))
        ax.text(0.07, y - 0.005, "MANDATORY MEDICAL DISCLAIMER & LIMITATIONS", color="#9a3412", fontsize=8.5, fontweight="bold")
        disclaimer_lines = textwrap.wrap(SAFETY_DISCLAIMER, width=110)
        dy = y - 0.026
        for line in disclaimer_lines[:3]:
            ax.text(0.07, dy, line, color="#7c2d12", fontsize=7.8)
            dy -= 0.016

        # 6. Footer Privacy & Export Notice
        ax.text(0.05, 0.035, "Privacy & Data Retention Notice: Uploaded photos and personal identifiers are not permanently stored on servers.",
                color="#64748b", fontsize=7.5)
        ax.text(0.05, 0.02, "Progression Notice: Past records represent isolated tests; record differences do not establish disease progression or cure.",
                color="#64748b", fontsize=7.5)
        ax.text(0.95, 0.025, "Page 1 of 1", color="#94a3b8", fontsize=8, ha="right")

        pdf.savefig(fig)
        plt.close(fig)

    pdf_bytes = pdf_buffer.getvalue()

    if output_path:
        target_path = Path(output_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
