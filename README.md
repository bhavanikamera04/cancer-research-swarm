# 🧠 CancerResearchSwarm

A **3-agent parallel AI system** for cancer research assistance.
Built using **DevSwarm**, where each agent is developed independently and merged into a unified system.

---

## ⚡ What It Does

A doctor enters patient information.
Three AI agents work **in parallel** to generate insights:

| Agent                | Branch                    | Task                                                   |
| -------------------- | ------------------------- | ------------------------------------------------------ |
| 📚 Literature Scout  | `agent-literature-scout`  | Searches PubMed and summarizes research using AI       |
| 🏥 Patient Analyst   | `agent-patient-analyst`   | Calculates risk score and identifies clinical patterns |
| 💊 Treatment Advisor | `agent-treatment-advisor` | Combines outputs into evidence-based recommendations   |

---

## ⚡ Parallel Execution

* Agent 1 and Agent 2 run **simultaneously**
* Agent 3 runs after both complete
* Reduces execution time significantly

```
Sequential: A → B → C  (slow)
Parallel:   A + B → C  (fast ⚡)
```

---

## 🏗️ System Architecture

```
Doctor Input
     ↓
 ┌──────────────┬──────────────┐
 │ Literature   │ Patient      │
 │ Scout        │ Analyst      │
 └──────┬───────┴──────┬───────┘
        ↓              ↓
     (Parallel Execution)
              ↓
     Treatment Advisor
              ↓
         Final Output
```

---

## 🧪 DevSwarm Workflow

This project demonstrates **true parallel development**:

* Each agent built in its own branch:

  * `agent-literature-scout`
  * `agent-patient-analyst`
  * `agent-treatment-advisor`
* All branches merged into `main`

👉 This proves **independent agent development + integration**

---

## 🛠️ Tech Stack

| Component     | Tool                              |
| ------------- | --------------------------------- |
| LLM           | Groq API (`llama-3.1-8b-instant`) |
| Research Data | PubMed E-utilities                |
| Dashboard     | Streamlit                         |
| Backend       | Python                            |
| Parallelism   | Threading                         |

---

## 🚀 Setup

### 1. Get Groq API Key

Go to: https://console.groq.com
Sign up → Create API key

---

### 2. Set API Key (Windows PowerShell)

```
$env:GROQ_API_KEY="your_key_here"
```

---

### 3. Install Dependencies

```
pip install -r requirements.txt
pip install groq
```

---

### 4. Run the App

```
streamlit run main.py
```

---

## 🎯 Demo Flow

1. Enter patient details
2. Literature Scout fetches research
3. Patient Analyst calculates risk
4. Both run in **parallel**
5. Treatment Advisor generates recommendations

---

## 📸 Demo UI

*Add your screenshot here*

```
![App Screenshot](screenshot.png)
```

---

## ⚠️ Disclaimer

This system is a **research assistance tool** for medical professionals only.

* Not a substitute for clinical judgment
* All outputs must be reviewed by a licensed oncologist
* Not intended for direct medical use

---

## 👨‍💻 Author

**Bhavani Kamera**
AI & Data Science Student

---

## ⭐ If you like this project

Give it a ⭐ on GitHub!
