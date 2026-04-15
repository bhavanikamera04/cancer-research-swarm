CancerResearchSwarm
A 3-agent parallel AI system for cancer research assistance.
Built with DevSwarm — each agent developed on an independent git branch.
What It Does
A doctor enters patient information. Three AI agents work in parallel:
AgentBranchTaskLiterature Scoutagent-literature-scoutSearches real PubMed papers, AI-summarizes findingsPatient Analystagent-patient-analystCalculates risk score, identifies clinical patternsTreatment Advisoragent-treatment-advisorSynthesizes both into evidence-based recommendations
Agents 1 and 2 run simultaneously using Python threading.
Agent 3 synthesizes their outputs. True parallel execution.
Setup
1. Get Groq API Key (Free)
Go to https://console.groq.com → Sign up → Create API key
2. Set API Key
bashexport GROQ_API_KEY="your_key_here"
3. Install Dependencies
bashpip install -r requirements.txt
4. Run
bashstreamlit run main.py
DevSwarm Git Workflow
bash# Create parallel branches
git checkout -b agent-literature-scout
# build literature_scout.py
git add agents/literature_scout.py
git commit -m "Agent 1: Literature Scout complete"

git checkout main
git checkout -b agent-patient-analyst
# build patient_analyst.py
git add agents/patient_analyst.py
git commit -m "Agent 2: Patient Analyst complete"

git checkout main
git checkout -b agent-treatment-advisor
# build treatment_advisor.py
git add agents/treatment_advisor.py
git commit -m "Agent 3: Treatment Advisor complete"

# Merge all branches
git checkout main
git merge agent-literature-scout
git merge agent-patient-analyst
git merge agent-treatment-advisor
Tech Stack
ComponentToolCostLLMGroq API — LLaMA 3 70BFreeResearch dataPubMed E-utilitiesFreeDashboardStreamlitFreeAgent coordinationPython threading—
Disclaimer
This system is a research assistance tool for qualified medical professionals only.
All output must be reviewed by a licensed oncologist before any clinical decision.
This tool does not constitute medical advice.