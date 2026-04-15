"""
CancerResearchSwarm - Agent 1: Literature Scout
Searches PubMed for real peer-reviewed cancer research papers.
Summarizes findings using Groq LLaMA 3.

Source: NCBI PubMed E-utilities API (free, no key required)
"""

import requests
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL, GROQ_FAST,
    PUBMED_SEARCH_URL, PUBMED_FETCH_URL, PUBMED_SUMMARY_URL,
    PUBMED_MAX_RESULTS, PUBMED_EMAIL,
    TEMPERATURE, MAX_TOKENS, REQUEST_TIMEOUT
)


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class ResearchPaper:
    pubmed_id:   str
    title:       str
    authors:     str
    journal:     str
    year:        str
    abstract:    str
    url:         str


@dataclass
class LiteratureReport:
    query:            str
    papers_found:     int
    papers:           list[ResearchPaper]
    ai_summary:       str
    key_findings:     list[str]
    research_gaps:    list[str]
    evidence_level:   str    # "Strong", "Moderate", "Limited"
    error:            Optional[str] = None


# ── PubMed Search ─────────────────────────────────────────────────────────────

def search_pubmed_ids(query: str, max_results: int = PUBMED_MAX_RESULTS) -> list[str]:
    """
    Searches PubMed and returns list of paper IDs.
    Uses NCBI E-utilities esearch endpoint.
    """
    params = {
        "db":      "pubmed",
        "term":    query + "[Title/Abstract]",
        "retmode": "json",
        "retmax":  max_results,
        "sort":    "relevance",
        "tool":    "CancerResearchSwarm",
        "email":   PUBMED_EMAIL,
    }
    try:
        response = requests.get(PUBMED_SEARCH_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        raise ConnectionError(f"PubMed search failed: {e}")


def fetch_paper_abstracts(pubmed_ids: list[str]) -> list[ResearchPaper]:
    """
    Fetches full paper details including abstracts from PubMed.
    Uses efetch endpoint with XML parsing.
    """
    if not pubmed_ids:
        return []

    params = {
        "db":      "pubmed",
        "id":      ",".join(pubmed_ids),
        "retmode": "xml",
        "rettype": "abstract",
        "tool":    "CancerResearchSwarm",
        "email":   PUBMED_EMAIL,
    }

    try:
        response = requests.get(PUBMED_FETCH_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return parse_pubmed_xml(response.text, pubmed_ids)
    except Exception as e:
        raise ConnectionError(f"PubMed fetch failed: {e}")


def parse_pubmed_xml(xml_text: str, pubmed_ids: list[str]) -> list[ResearchPaper]:
    """
    Parses PubMed XML response into ResearchPaper objects.
    """
    papers = []
    try:
        root = ET.fromstring(xml_text)
        articles = root.findall(".//PubmedArticle")

        for i, article in enumerate(articles):
            # Title
            title_el = article.find(".//ArticleTitle")
            title = title_el.text if title_el is not None else "Title not available"
            title = title.strip() if title else "Title not available"

            # Authors
            authors = []
            for author in article.findall(".//Author")[:3]:
                last  = author.find("LastName")
                first = author.find("ForeName")
                if last is not None:
                    name = last.text
                    if first is not None:
                        name += f" {first.text[0]}."
                    authors.append(name)
            authors_str = ", ".join(authors) if authors else "Authors not listed"
            if len(article.findall(".//Author")) > 3:
                authors_str += " et al."

            # Journal
            journal_el = article.find(".//Journal/Title")
            journal = journal_el.text if journal_el is not None else "Journal unknown"

            # Year
            year_el = article.find(".//PubDate/Year")
            year = year_el.text if year_el is not None else "Year unknown"

            # Abstract
            abstract_parts = article.findall(".//AbstractText")
            if abstract_parts:
                abstract = " ".join(
                    (el.get("Label", "") + ": " + (el.text or "")).strip()
                    for el in abstract_parts
                    if el.text
                )
            else:
                abstract = "Abstract not available."

            # PubMed ID
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else (pubmed_ids[i] if i < len(pubmed_ids) else "unknown")

            papers.append(ResearchPaper(
                pubmed_id = pmid,
                title     = title,
                authors   = authors_str,
                journal   = journal,
                year      = year,
                abstract  = abstract[:1500],   # Cap length
                url       = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            ))

    except ET.ParseError as e:
        raise ValueError(f"XML parsing failed: {e}")

    return papers


# ── Groq AI Summary ───────────────────────────────────────────────────────────

def summarize_with_groq(
    papers: list[ResearchPaper],
    cancer_type: str,
    symptoms: str
) -> dict:
    """
    Uses Groq LLaMA 3 to summarize research findings.
    Returns structured analysis: summary, key findings, gaps, evidence level.
    """
    if not GROQ_API_KEY:
        return {
            "summary":        "Groq API key not set. Please add GROQ_API_KEY to environment.",
            "key_findings":   [],
            "research_gaps":  [],
            "evidence_level": "Unknown",
        }

    # Prepare paper content for the prompt
    paper_content = ""
    for i, p in enumerate(papers, 1):
        paper_content += f"""
Paper {i}: {p.title}
Authors: {p.authors}
Journal: {p.journal} ({p.year})
Abstract: {p.abstract[:800]}
---"""

    prompt = f"""You are a medical research analyst specializing in oncology.
A doctor needs research insights for a patient with the following:
- Cancer type: {cancer_type}
- Symptoms: {symptoms}

Here are {len(papers)} recent PubMed research papers:
{paper_content}

Provide a structured analysis in this EXACT format:

SUMMARY:
[2-3 sentence overview of current research state for this cancer type and symptoms]

KEY_FINDINGS:
- [Finding 1 from the research]
- [Finding 2 from the research]
- [Finding 3 from the research]
- [Finding 4 from the research]

RESEARCH_GAPS:
- [Gap 1 - what is still unknown or understudied]
- [Gap 2]

EVIDENCE_LEVEL:
[One word only: Strong / Moderate / Limited]

Be precise, cite specific findings from the papers. Stay factual."""

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
        return parse_groq_response(text)

    except requests.exceptions.HTTPError as e:
        if "429" in str(e):
            return {
                "summary":        "Rate limit hit. Please wait 30 seconds and try again.",
                "key_findings":   [],
                "research_gaps":  [],
                "evidence_level": "Unknown",
            }
        raise


def parse_groq_response(text: str) -> dict:
    """Parses structured Groq response into components."""
    result = {
        "summary":        "",
        "key_findings":   [],
        "research_gaps":  [],
        "evidence_level": "Moderate",
    }

    lines = text.strip().split("\n")
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("SUMMARY:"):
            current_section = "summary"
            content = line.replace("SUMMARY:", "").strip()
            if content:
                result["summary"] = content
        elif line.startswith("KEY_FINDINGS:"):
            current_section = "key_findings"
        elif line.startswith("RESEARCH_GAPS:"):
            current_section = "research_gaps"
        elif line.startswith("EVIDENCE_LEVEL:"):
            level = line.replace("EVIDENCE_LEVEL:", "").strip()
            if level in ["Strong", "Moderate", "Limited"]:
                result["evidence_level"] = level
        elif current_section == "summary" and not result["summary"]:
            result["summary"] = line
        elif current_section == "summary" and result["summary"]:
            result["summary"] += " " + line
        elif current_section == "key_findings" and line.startswith("-"):
            finding = line.lstrip("- ").strip()
            if finding:
                result["key_findings"].append(finding)
        elif current_section == "research_gaps" and line.startswith("-"):
            gap = line.lstrip("- ").strip()
            if gap:
                result["research_gaps"].append(gap)

    return result


# ── Main Agent Function ───────────────────────────────────────────────────────

def run_literature_scout(
    cancer_type: str,
    symptoms:    str,
    extra_terms: str = ""
) -> LiteratureReport:
    """
    Main function for Agent 1.
    Searches PubMed and returns AI-summarized literature report.

    Args:
        cancer_type:  e.g. "Lung Cancer"
        symptoms:     e.g. "persistent cough, weight loss, chest pain"
        extra_terms:  optional additional search terms

    Returns:
        LiteratureReport with real papers and AI analysis
    """
    # Build search query
    query_parts = [cancer_type, "treatment", "clinical trial"]
    if symptoms:
        # Add first two symptom keywords
        symptom_words = [s.strip() for s in symptoms.split(",")][:2]
        query_parts.extend(symptom_words)
    if extra_terms:
        query_parts.append(extra_terms)

    query = " ".join(query_parts)

    try:
        # Step 1: Search PubMed
        pubmed_ids = search_pubmed_ids(query)

        if not pubmed_ids:
            # Fallback: broader search
            pubmed_ids = search_pubmed_ids(cancer_type + " treatment 2023 2024")

        if not pubmed_ids:
            return LiteratureReport(
                query         = query,
                papers_found  = 0,
                papers        = [],
                ai_summary    = "No papers found for this query.",
                key_findings  = [],
                research_gaps = [],
                evidence_level= "Limited",
                error         = "No PubMed results found."
            )

        # Step 2: Fetch abstracts
        papers = fetch_paper_abstracts(pubmed_ids)

        # Step 3: AI summarization
        analysis = summarize_with_groq(papers, cancer_type, symptoms)

        return LiteratureReport(
            query          = query,
            papers_found   = len(papers),
            papers         = papers,
            ai_summary     = analysis["summary"],
            key_findings   = analysis["key_findings"],
            research_gaps  = analysis["research_gaps"],
            evidence_level = analysis["evidence_level"],
        )

    except ConnectionError as e:
        return LiteratureReport(
            query          = query,
            papers_found   = 0,
            papers         = [],
            ai_summary     = "",
            key_findings   = [],
            research_gaps  = [],
            evidence_level = "Unknown",
            error          = str(e)
        )