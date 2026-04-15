"""
CancerResearchSwarm - Agent 2: Patient Analyst
Analyzes patient data and identifies cancer risk patterns.
Uses Groq LLaMA 3 for intelligent pattern recognition.
"""

import requests
from dataclasses import dataclass, field
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL,
    TEMPERATURE, MAX_TOKENS, REQUEST_TIMEOUT,
    RISK_FACTORS
)


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class PatientProfile:
    age:            int
    gender:         str
    cancer_type:    str
    symptoms:       str
    duration_weeks: int
    risk_factors:   list[str]
    medical_history: str
    current_meds:   str
    family_history: str


@dataclass
class PatientAnalysis:
    patient_profile:      PatientProfile
    risk_level:           str       # "High", "Moderate", "Low"
    risk_score:           int       # 0–100
    identified_patterns:  list[str]
    red_flags:            list[str]
    protective_factors:   list[str]
    urgency:              str       # "Immediate", "Soon", "Routine"
    clinical_summary:     str
    questions_for_doctor: list[str]
    error:                Optional[str] = None


# ── Risk Scoring ──────────────────────────────────────────────────────────────

# Age risk weights by cancer type
AGE_RISK_THRESHOLDS = {
    "Lung Cancer":        {"high": 60, "moderate": 45},
    "Breast Cancer":      {"high": 50, "moderate": 35},
    "Colorectal Cancer":  {"high": 55, "moderate": 40},
    "Prostate Cancer":    {"high": 65, "moderate": 50},
    "Leukemia":           {"high": 65, "moderate": 2},   # bimodal - children + elderly
    "default":            {"high": 60, "moderate": 40},
}

# Symptom severity weights
HIGH_SEVERITY_SYMPTOMS = [
    "blood", "bleeding", "hemorrhage",
    "weight loss", "unexplained weight",
    "persistent pain", "severe pain",
    "difficulty breathing", "shortness of breath",
    "lump", "mass", "swelling",
    "fatigue", "night sweats",
    "fever", "bone pain",
]

RED_FLAG_SYMPTOMS = [
    "coughing blood", "blood in stool", "blood in urine",
    "sudden vision loss", "seizure", "paralysis",
    "severe headache", "confusion", "loss of consciousness",
]


def calculate_base_risk_score(profile: PatientProfile) -> tuple[int, list[str]]:
    """
    Calculates a numerical risk score (0-100) based on patient data.
    Returns (score, list of contributing factors).
    """
    score = 0
    factors = []

    # Age risk
    thresholds = AGE_RISK_THRESHOLDS.get(profile.cancer_type, AGE_RISK_THRESHOLDS["default"])
    if profile.age >= thresholds["high"]:
        score += 25
        factors.append(f"Age {profile.age} — high-risk bracket for {profile.cancer_type}")
    elif profile.age >= thresholds["moderate"]:
        score += 15
        factors.append(f"Age {profile.age} — moderate-risk bracket")

    # Risk factors count
    num_risk_factors = len(profile.risk_factors)
    if num_risk_factors >= 4:
        score += 30
        factors.append(f"{num_risk_factors} major risk factors present")
    elif num_risk_factors >= 2:
        score += 18
        factors.append(f"{num_risk_factors} risk factors present")
    elif num_risk_factors == 1:
        score += 8
        factors.append(f"1 risk factor: {profile.risk_factors[0]}")

    # Symptom severity
    symptoms_lower = profile.symptoms.lower()
    high_sev_count = sum(1 for s in HIGH_SEVERITY_SYMPTOMS if s in symptoms_lower)
    if high_sev_count >= 3:
        score += 25
        factors.append(f"{high_sev_count} high-severity symptoms")
    elif high_sev_count >= 1:
        score += 12
        factors.append(f"{high_sev_count} notable symptom(s)")

    # Duration
    if profile.duration_weeks > 8:
        score += 15
        factors.append(f"Symptoms persisting {profile.duration_weeks} weeks")
    elif profile.duration_weeks > 4:
        score += 8
        factors.append(f"Symptoms for {profile.duration_weeks} weeks")

    # Family history
    if profile.family_history and len(profile.family_history) > 5:
        score += 10
        factors.append("Family history of cancer reported")

    # Smoking (strongest individual risk factor for many cancers)
    if "smoking" in [r.lower() for r in profile.risk_factors]:
        score += 15
        factors.append("Active/former smoker — major carcinogen exposure")

    return min(score, 100), factors


def identify_red_flags(profile: PatientProfile) -> list[str]:
    """Identifies symptoms that require immediate medical attention."""
    symptoms_lower = profile.symptoms.lower()
    flags = []
    for flag in RED_FLAG_SYMPTOMS:
        if flag in symptoms_lower:
            flags.append(f"RED FLAG: '{flag}' — requires immediate oncologist review")
    return flags


def determine_urgency(risk_score: int, red_flags: list[str], duration_weeks: int) -> str:
    if red_flags or risk_score >= 75:
        return "Immediate"
    elif risk_score >= 50 or duration_weeks > 8:
        return "Soon"
    else:
        return "Routine"


def determine_risk_level(score: int) -> str:
    if score >= 70:
        return "High"
    elif score >= 40:
        return "Moderate"
    else:
        return "Low"


# ── Groq Analysis ─────────────────────────────────────────────────────────────

def analyze_with_groq(profile: PatientProfile, base_score: int, patterns: list[str]) -> dict:
    """
    Uses Groq LLaMA 3 to provide deep clinical pattern analysis.
    """
    if not GROQ_API_KEY:
        return {
            "clinical_summary":     "Groq API key not configured.",
            "identified_patterns":  patterns,
            "protective_factors":   [],
            "questions_for_doctor": [],
        }

    prompt = f"""You are an oncology clinical analyst assisting a doctor.

Patient Data:
- Age: {profile.age} | Gender: {profile.gender}
- Suspected cancer type: {profile.cancer_type}
- Presenting symptoms: {profile.symptoms}
- Symptom duration: {profile.duration_weeks} weeks
- Risk factors: {', '.join(profile.risk_factors) if profile.risk_factors else 'None reported'}
- Medical history: {profile.medical_history or 'Not provided'}
- Current medications: {profile.current_meds or 'None'}
- Family history: {profile.family_history or 'Not provided'}
- Preliminary risk score: {base_score}/100

Provide a structured clinical analysis in this EXACT format:

CLINICAL_SUMMARY:
[3-4 sentence clinical narrative of this patient's presentation and key concerns]

PATTERNS:
- [Clinical pattern 1 observed in this patient]
- [Clinical pattern 2]
- [Clinical pattern 3]

PROTECTIVE_FACTORS:
- [Factor that reduces risk or improves prognosis, if any]
- [Factor 2, if any]

QUESTIONS_FOR_DOCTOR:
- [Specific question to ask this patient in clinic]
- [Question 2]
- [Question 3]
- [Question 4]

Be specific to THIS patient's data. Do not give generic cancer information."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }

    payload = {
        "model":       GROQ_MODEL,
        "messages":    [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens":  MAX_TOKENS,
    }

    try:
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        return parse_patient_response(text, patterns)

    except Exception as e:
        return {
            "clinical_summary":     f"AI analysis unavailable: {str(e)[:100]}",
            "identified_patterns":  patterns,
            "protective_factors":   [],
            "questions_for_doctor": [],
        }


def parse_patient_response(text: str, fallback_patterns: list[str]) -> dict:
    """Parses structured Groq response for patient analysis."""
    result = {
        "clinical_summary":     "",
        "identified_patterns":  [],
        "protective_factors":   [],
        "questions_for_doctor": [],
    }

    lines = text.strip().split("\n")
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("CLINICAL_SUMMARY:"):
            current_section = "clinical_summary"
            content = line.replace("CLINICAL_SUMMARY:", "").strip()
            if content:
                result["clinical_summary"] = content
        elif line.startswith("PATTERNS:"):
            current_section = "patterns"
        elif line.startswith("PROTECTIVE_FACTORS:"):
            current_section = "protective"
        elif line.startswith("QUESTIONS_FOR_DOCTOR:"):
            current_section = "questions"
        elif current_section == "clinical_summary":
            if result["clinical_summary"]:
                result["clinical_summary"] += " " + line
            else:
                result["clinical_summary"] = line
        elif current_section == "patterns" and line.startswith("-"):
            p = line.lstrip("- ").strip()
            if p:
                result["identified_patterns"].append(p)
        elif current_section == "protective" and line.startswith("-"):
            p = line.lstrip("- ").strip()
            if p and p.lower() not in ["none", "none reported", "n/a"]:
                result["protective_factors"].append(p)
        elif current_section == "questions" and line.startswith("-"):
            q = line.lstrip("- ").strip()
            if q:
                result["questions_for_doctor"].append(q)

    if not result["identified_patterns"]:
        result["identified_patterns"] = fallback_patterns

    return result


# ── Main Agent Function ───────────────────────────────────────────────────────

def run_patient_analyst(profile: PatientProfile) -> PatientAnalysis:
    """
    Main function for Agent 2.
    Analyzes patient data and returns comprehensive risk assessment.

    Args:
        profile: PatientProfile dataclass with all patient information

    Returns:
        PatientAnalysis with risk score, patterns, red flags, and clinical summary
    """
    try:
        # Step 1: Calculate base risk score
        risk_score, base_patterns = calculate_base_risk_score(profile)

        # Step 2: Identify red flags
        red_flags = identify_red_flags(profile)

        # Step 3: Deep AI analysis
        analysis = analyze_with_groq(profile, risk_score, base_patterns)

        # Step 4: Determine risk level and urgency
        risk_level = determine_risk_level(risk_score)
        urgency    = determine_urgency(risk_score, red_flags, profile.duration_weeks)

        return PatientAnalysis(
            patient_profile      = profile,
            risk_level           = risk_level,
            risk_score           = risk_score,
            identified_patterns  = analysis["identified_patterns"],
            red_flags            = red_flags,
            protective_factors   = analysis["protective_factors"],
            urgency              = urgency,
            clinical_summary     = analysis["clinical_summary"],
            questions_for_doctor = analysis["questions_for_doctor"],
        )

    except Exception as e:
        return PatientAnalysis(
            patient_profile      = profile,
            risk_level           = "Unknown",
            risk_score           = 0,
            identified_patterns  = [],
            red_flags            = [],
            protective_factors   = [],
            urgency              = "Unknown",
            clinical_summary     = "",
            questions_for_doctor = [],
            error                = str(e),
        )