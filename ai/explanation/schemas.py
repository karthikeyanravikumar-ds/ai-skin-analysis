from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EducationalPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=120)
    explanation: str = Field(min_length=1, max_length=600)


class NextStep(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    code: Literal[
        "CONSULT_DERMATOLOGIST",
        "GENTLE_SKINCARE",
        "MONITOR_CHANGES",
        "SEEK_URGENT_CARE",
        "FOLLOW_EXISTING_MEDICAL_ADVICE",
    ]
    explanation: str = Field(min_length=1, max_length=400)


class ExplanationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: Literal["1.0"] = "1.0"

    summary: str = Field(min_length=1, max_length=500)
    model_output_meaning: str = Field(min_length=1, max_length=700)
    reported_symptoms_context: str = Field(min_length=1, max_length=700)
    visual_attention_explanation: str = Field(min_length=1, max_length=700)
    uncertainty_explanation: str = Field(min_length=1, max_length=700)

    educational_points: list[EducationalPoint] = Field(min_length=1, max_length=5)
    next_steps: list[NextStep] = Field(min_length=1, max_length=5)

    limitations: list[str] = Field(min_length=1, max_length=6)
    content_ids: list[str] = Field(max_length=10)
    guardrail_flags: list[str] = Field(max_length=10)
