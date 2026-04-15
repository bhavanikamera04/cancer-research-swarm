"""
CancerResearchSwarm - Shared Configuration
All agents read from this file.
"""

import os

# ── Groq API ─────────────────────────────────────────────────────────────────
# Get free API key at: https://console.groq.com
# Set as environment variable: export GROQ_API_KEY="your_key_here"
# Or paste directly below (not recommended for production)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.1-8b-instant"   # Primary (fast + stable)
GROQ_FAST    = "llama-3.1-8b-instant"   # Keep same (or remove fallback logic)

# ── PubMed API ────────────────────────────────────────────────────────────────
# Free, no key needed. Real peer-reviewed medical papers.
PUBMED_SEARCH_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL   = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PUBMED_MAX_RESULTS = 5
PUBMED_EMAIL       = "aquaswarm@research.com"   # Required by NCBI fair use policy

# ── Agent Settings ─────────────────────────────────────────────────────────
TEMPERATURE     = 0.2    # Low = more factual, consistent
MAX_TOKENS      = 1500
REQUEST_TIMEOUT = 30     # seconds

# ── Cancer Types Supported ────────────────────────────────────────────────────
CANCER_TYPES = [
    "Lung Cancer",
    "Breast Cancer",
    "Colorectal Cancer",
    "Prostate Cancer",
    "Leukemia",
    "Lymphoma",
    "Brain Tumor",
    "Skin Cancer (Melanoma)",
    "Pancreatic Cancer",
    "Ovarian Cancer",
    "Cervical Cancer",
    "Stomach Cancer",
    "Liver Cancer",
    "Kidney Cancer",
    "Thyroid Cancer",
    "Bladder Cancer",
]

# ── Risk Factors ──────────────────────────────────────────────────────────────
RISK_FACTORS = [
    "Smoking",
    "Family history of cancer",
    "Obesity",
    "Alcohol use",
    "Radiation exposure",
    "Chemical exposure",
    "Chronic inflammation",
    "Viral infections (HPV, HBV, HCV)",
    "Age > 50",
    "Sedentary lifestyle",
    "Poor diet",
    "Immunosuppression",
]

# ── Disclaimer ────────────────────────────────────────────────────────────────
MEDICAL_DISCLAIMER = """
⚠️ IMPORTANT MEDICAL DISCLAIMER:
This system is a research assistance tool designed to support — not replace —
qualified medical professionals. All recommendations must be reviewed and
validated by a licensed oncologist before any clinical decision is made.
This tool does not constitute medical advice.
"""