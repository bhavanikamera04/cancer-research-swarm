"""
CancerResearchSwarm - Agent 3: Treatment Advisor
Synthesizes literature research + patient analysis into
evidence-based treatment recommendations for doctor review.

⚠️ OUTPUT IS FOR DOCTOR REVIEW ONLY — NOT DIRECT MEDICAL ADVICE
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
    MEDICAL_DISCLAIMER
)

from agents.literature_scout import LiteratureReport
from agents.patient_analyst  import PatientAnalysis


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class TreatmentOption:
    name:             str
    category:         str    # "Surgery", "Chemotherapy", "Radiation", "Immunotherapy", etc.
    evidence_strength: str   # "Strong", "Moderate", "Emerging"
    description:      str
    relevant_for:     str    # Why this fits this specific patient
    clinical_trials:  list[str] = field(default_factory=list)


@dataclass
class TreatmentReport:
    cancer_type:           str
    patient_risk_level:    str
    patient_risk_score:    int
    evidence_level:        str
    treatment_options:     list[TreatmentOption]
    first_line_priority:   str
    monitoring_plan:       list[str]
    lifestyle_recommendations: list[str]
    urgent_actions:        list[str]
    full_synthesis:        str
    confidence_note:       str
    disclaimer:            str
    error:                 Optional[str] = None


# ── Treatment Knowledge Base ──────────────────────────────────────────────────
# Evidence-based first-line approaches by cancer type
# Source: NCCN Guidelines 2024, ESMO Guidelines 2024

STANDARD_APPROACHES = {
    "Lung Cancer": {
        "first_line": "NSCLC: Platinum-based chemotherapy ± immunotherapy (pembrolizumab if PD-L1 ≥50%). SCLC: Etoposide + cisplatin/carboplatin.",
        "targeted":   "EGFR mutation: osimertinib. ALK/ROS1: crizotinib/alectinib. KRAS G12C: sotorasib.",
        "immunotherapy": "Pembrolizumab, nivolumab, atezolizumab based on PD-L1 expression.",
    },
    "Breast Cancer": {
        "first_line": "HER2+: trastuzumab-based regimens. HR+/HER2-: CDK4/6 inhibitors + endocrine therapy. TNBC: chemotherapy ± immunotherapy.",
        "targeted":   "BRCA1/2 mutation: olaparib/talazoparib. HER2+: trastuzumab + pertuzumab.",
        "immunotherapy": "Pembrolizumab for TNBC with PD-L1+.",
    },
    "Colorectal Cancer": {
        "first_line": "FOLFOX or FOLFIRI ± bevacizumab or cetuximab (RAS wild-type). MSI-H: immunotherapy first-line.",
        "targeted":   "KRAS/NRAS wild-type: cetuximab or panitumumab. BRAF V600E: encorafenib + cetuximab.",
        "immunotherapy": "Pembrolizumab or nivolumab for MSI-H/dMMR tumors.",
    },
    "Leukemia": {
        "first_line": "AML: cytarabine + anthracycline ('7+3' induction). ALL: multi-agent chemotherapy protocols (HyperCVAD). CML: imatinib/dasatinib.",
        "targeted":   "BCR-ABL (CML/Ph+ ALL): TKIs. FLT3 mutation (AML): midostaurin. IDH1/2: enasidenib/ivosidenib.",
        "immunotherapy": "Blinatumomab for B-cell ALL. CAR-T for relapsed/refractory ALL.",
    },
    "Lymphoma": {
        "first_line": "DLBCL: R-CHOP (rituximab + CHOP). Hodgkin: ABVD or BEACOPP. Follicular: BR or R-CHOP.",
        "targeted":   "CD20+: rituximab/obinutuzumab. BCL-2: venetoclax. BTK inhibitors for MCL/CLL.",
        "immunotherapy": "Pembrolizumab for relapsed Hodgkin. CAR-T for relapsed DLBCL.",
    },
    "default": {
        "first_line": "Standard-of-care chemotherapy based on cancer type, stage, and molecular profile.",
        "targeted":   "Molecular profiling recommended to identify actionable mutations.",
        "immunotherapy": "PD-L1 testing recommended to assess immunotherapy eligibility.",
    }
}


# ── Groq Synthesis ────────────────────────────────────────────────────────────

def synthesize_with_groq(
    literature:      LiteratureReport,
    patient:         PatientAnalysis,
    standard_info:   dict
) -> dict:
    """
    Uses Groq LLaMA 3 to synthesize literature + patient data
    into personalized treatment recommendations.
    """
    if not GROQ_API_KEY:
        return {
            "treatment_options":           [],
            "first_line_priority":         "Groq API key not configured.",
            "monitoring_plan":             [],
            "lifestyle_recommendations":   [],
            "urgent_actions":              [],
            "full_synthesis":              "API key required.",
            "confidence_note":             "",
        }

    # Build literature summary for prompt
    paper_titles = "\n".join(
        f"  - {p.title} ({p.year})" for p in literature.papers[:5]
    ) if literature.papers else "  - No papers retrieved"

    key_findings = "\n".join(
        f"  - {f}" for f in literature.key_findings[:4]
    ) if literature.key_findings else "  - Not available"

    prompt = f"""You are a senior oncologist providing a treatment consultation summary for a colleague.

PATIENT SUMMARY:
- Cancer type: {patient.patient_profile.cancer_type}
- Age/Gender: {patient.patient_profile.age} / {patient.patient_profile.gender}
- Symptoms: {patient.patient_profile.symptoms}
- Risk level: {patient.risk_level} ({patient.risk_score}/100)
- Key patterns: {'; '.join(patient.identified_patterns[:3])}
- Red flags: {'; '.join(patient.red_flags) if patient.red_flags else 'None'}
- Medical history: {patient.patient_profile.medical_history or 'Not provided'}
- Risk factors: {', '.join(patient.patient_profile.risk_factors) or 'None'}

RESEARCH FINDINGS (from {literature.papers_found} PubMed papers):
Papers reviewed:
{paper_titles}

Key findings:
{key_findings}

Evidence level: {literature.evidence_level}

STANDARD OF CARE REFERENCE:
First line: {standard_info.get('first_line', 'Per NCCN guidelines')}
Targeted options: {standard_info.get('targeted', 'Molecular profiling recommended')}
Immunotherapy: {standard_info.get('immunotherapy', 'PD-L1 testing recommended')}

Provide treatment recommendations in this EXACT format for doctor review:

FULL_SYNTHESIS:
[3-4 sentences synthesizing the research evidence with this specific patient's profile]

TREATMENT_OPTIONS:
OPTION_1:
NAME: [treatment name]
CATEGORY: [Surgery/Chemotherapy/Radiation/Immunotherapy/Targeted/Supportive]
EVIDENCE: [Strong/Moderate/Emerging]
DESCRIPTION: [1-2 sentence description]
RELEVANT_BECAUSE: [why this fits this specific patient]

OPTION_2:
NAME: [treatment name]
CATEGORY: [category]
EVIDENCE: [level]
DESCRIPTION: [description]
RELEVANT_BECAUSE: [reason]

OPTION_3:
NAME: [treatment name]
CATEGORY: [category]
EVIDENCE: [level]
DESCRIPTION: [description]
RELEVANT_BECAUSE: [reason]

FIRST_LINE_PRIORITY:
[One sentence: what should be the immediate clinical priority for this patient]

MONITORING_PLAN:
- [Monitoring step 1]
- [Monitoring step 2]
- [Monitoring step 3]

LIFESTYLE_RECOMMENDATIONS:
- [Lifestyle recommendation 1]
- [Lifestyle recommendation 2]

URGENT_ACTIONS:
- [Urgent action if any — tests, referrals, immediate interventions]
- [Urgent action 2 if applicable]

CONFIDENCE_NOTE:
[One sentence about limitations of this AI-generated recommendation]

All recommendations must be for doctor review only. Be specific to this patient."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }

    payload = {
        "model":       GROQ_MODEL,
        "messages":    [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens":  2000,
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
        return parse_treatment_response(text)

    except Exception as e:
        return {
            "treatment_options":         [],
            "first_line_priority":       f"Analysis unavailable: {str(e)[:100]}",
            "monitoring_plan":           [],
            "lifestyle_recommendations": [],
            "urgent_actions":            [],
            "full_synthesis":            "",
            "confidence_note":           "",
        }


def parse_treatment_response(text: str) -> dict:
    """Parses the structured treatment response from Groq."""
    result = {
        "full_synthesis":              "",
        "treatment_options":           [],
        "first_line_priority":         "",
        "monitoring_plan":             [],
        "lifestyle_recommendations":   [],
        "urgent_actions":              [],
        "confidence_note":             "",
    }

    lines = text.strip().split("\n")
    current_section = None
    current_option  = {}

    def save_option(opt):
        if opt.get("name"):
            result["treatment_options"].append(TreatmentOption(
                name              = opt.get("name", ""),
                category          = opt.get("category", ""),
                evidence_strength = opt.get("evidence", "Moderate"),
                description       = opt.get("description", ""),
                relevant_for      = opt.get("relevant_because", ""),
            ))

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("FULL_SYNTHESIS:"):
            current_section = "synthesis"
            content = stripped.replace("FULL_SYNTHESIS:", "").strip()
            if content:
                result["full_synthesis"] = content
        elif stripped.startswith("TREATMENT_OPTIONS:"):
            current_section = "options"
        elif stripped.startswith("OPTION_") and stripped.endswith(":"):
            save_option(current_option)
            current_option = {}
        elif stripped.startswith("NAME:"):
            current_option["name"] = stripped.replace("NAME:", "").strip()
        elif stripped.startswith("CATEGORY:"):
            current_option["category"] = stripped.replace("CATEGORY:", "").strip()
        elif stripped.startswith("EVIDENCE:"):
            current_option["evidence"] = stripped.replace("EVIDENCE:", "").strip()
        elif stripped.startswith("DESCRIPTION:"):
            current_option["description"] = stripped.replace("DESCRIPTION:", "").strip()
        elif stripped.startswith("RELEVANT_BECAUSE:"):
            current_option["relevant_because"] = stripped.replace("RELEVANT_BECAUSE:", "").strip()
        elif stripped.startswith("FIRST_LINE_PRIORITY:"):
            save_option(current_option)
            current_option = {}
            current_section = "first_line"
            content = stripped.replace("FIRST_LINE_PRIORITY:", "").strip()
            if content:
                result["first_line_priority"] = content
        elif stripped.startswith("MONITORING_PLAN:"):
            current_section = "monitoring"
        elif stripped.startswith("LIFESTYLE_RECOMMENDATIONS:"):
            current_section = "lifestyle"
        elif stripped.startswith("URGENT_ACTIONS:"):
            current_section = "urgent"
        elif stripped.startswith("CONFIDENCE_NOTE:"):
            current_section = "confidence"
            content = stripped.replace("CONFIDENCE_NOTE:", "").strip()
            if content:
                result["confidence_note"] = content
        elif current_section == "synthesis":
            result["full_synthesis"] += " " + stripped
        elif current_section == "first_line" and not result["first_line_priority"]:
            result["first_line_priority"] = stripped
        elif current_section == "monitoring" and stripped.startswith("-"):
            m = stripped.lstrip("- ").strip()
            if m:
                result["monitoring_plan"].append(m)
        elif current_section == "lifestyle" and stripped.startswith("-"):
            l = stripped.lstrip("- ").strip()
            if l:
                result["lifestyle_recommendations"].append(l)
        elif current_section == "urgent" and stripped.startswith("-"):
            u = stripped.lstrip("- ").strip()
            if u:
                result["urgent_actions"].append(u)
        elif current_section == "confidence":
            if result["confidence_note"]:
                result["confidence_note"] += " " + stripped
            else:
                result["confidence_note"] = stripped

    save_option(current_option)
    return result


# ── Main Agent Function ───────────────────────────────────────────────────────

def run_treatment_advisor(
    literature: LiteratureReport,
    patient:    PatientAnalysis
) -> TreatmentReport:
    """
    Main function for Agent 3.
    Synthesizes all information into treatment recommendations.

    Args:
        literature: Output from Agent 1 (Literature Scout)
        patient:    Output from Agent 2 (Patient Analyst)

    Returns:
        TreatmentReport with evidence-based recommendations for doctor review
    """
    try:
        cancer_type   = patient.patient_profile.cancer_type
        standard_info = STANDARD_APPROACHES.get(cancer_type, STANDARD_APPROACHES["default"])

        synthesis = synthesize_with_groq(literature, patient, standard_info)

        # Urgent actions: always include red flags from patient analyst
        urgent_actions = synthesis.get("urgent_actions", [])
        for flag in patient.red_flags:
            if flag not in urgent_actions:
                urgent_actions.insert(0, flag)

        return TreatmentReport(
            cancer_type                = cancer_type,
            patient_risk_level         = patient.risk_level,
            patient_risk_score         = patient.risk_score,
            evidence_level             = literature.evidence_level,
            treatment_options          = synthesis["treatment_options"],
            first_line_priority        = synthesis["first_line_priority"],
            monitoring_plan            = synthesis["monitoring_plan"],
            lifestyle_recommendations  = synthesis["lifestyle_recommendations"],
            urgent_actions             = urgent_actions,
            full_synthesis             = synthesis["full_synthesis"].strip(),
            confidence_note            = synthesis["confidence_note"],
            disclaimer                 = MEDICAL_DISCLAIMER,
        )

    except Exception as e:
        return TreatmentReport(
            cancer_type               = patient.patient_profile.cancer_type,
            patient_risk_level        = patient.risk_level,
            patient_risk_score        = patient.risk_score,
            evidence_level            = "Unknown",
            treatment_options         = [],
            first_line_priority       = "",
            monitoring_plan           = [],
            lifestyle_recommendations = [],
            urgent_actions            = [],
            full_synthesis            = "",
            confidence_note           = "",
            disclaimer                = MEDICAL_DISCLAIMER,
            error                     = str(e),
        )