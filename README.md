# ❄️ DataMind: Talk to Your Data
> **ZeroDay OSS Hacktoberfest 2026 · Problem Statement 1 (IIIT Dharwad)**  
> *An open-source, evidence-grounded data agent powered by Google Gemma 4 and Snowflake Cloud Data Warehouse.*

---

## 🌟 Overview
DataMind allows non-technical decision-makers to ask complex business and research questions in plain natural language. Rather than hallucinating or summarizing static summaries, DataMind:
1. Synthesizes optimal, dialect-accurate Snowflake SQL at query time.
2. Executes read-only queries with millisecond tracking on a live Snowflake warehouse.
3. Produces a plain-language explanation citing exact data rows, filters, and assumptions.
4. Exposes an **Inspectable Evidence Container** showing the live SQL, result rows, and warehouse execution latency.

---

## 🚀 Quick Start (< 3 minutes)

### 1. Install Dependencies
```bash
pip install snowflake-connector-python python-dotenv pyyaml requests streamlit pandas
```

### 2. Configure Credentials
Edit `datamind/.env`:
```ini
SNOWFLAKE_ACCOUNT=ol15456
SNOWFLAKE_HOST=ol15456.ap-south-1.aws.snowflakecomputing.com
SNOWFLAKE_USER=KIRITO2026
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=DATAMIND_DB
SNOWFLAKE_SCHEMA=PUBLIC

OPENROUTER_API_KEY=your_key
GEMMA_MODEL=google/gemma-4-26b-a4b-it
```

### 3. Load Sample Datasets into Snowflake
```bash
python datamind/data/load_data.py
```

### 4. Launch the Streamlit Dashboard
```bash
streamlit run datamind/app.py
```

---

## 🧪 Automated Testing & Verification
Run the comprehensive test suite verifying grounding, SQL safety guardrails, ambiguity triage, and multi-dataset adaptability:
```bash
python -m unittest datamind/tests/test_grounding.py
```

---

## 🛡️ Hackathon Mandatory Core Features (M1–M8 Compliance)
- **M1 (Natural Language)**: Ask questions in everyday conversational phrasing.
- **M2 (Live Retrieval)**: Computes answers directly from live Snowflake queries at question time.
- **M3 (Grounding)**: Zero hallucinated figures; claims map directly to returned data rows.
- **M4 & M5 (Evidence & Explainability)**: Full visibility into executed SQL, returned records, and assumptions.
- **M6 (Edge Case & Safety Handling)**: Guardrails against SQL injection (`DROP`, `DELETE`), polite refusal of malicious prompts, and helpful clarification on ambiguous queries.
- **M7 (Meaningful Snowflake + Gemma Integration)**: Snowflake acts as the core analytical compute engine; Gemma 4 acts as the reasoning and explainability orchestrator.
- **M8 & Criterion 7 (Reusability & Adaptability)**: Switch between datasets (e.g. *Global Development* vs. *Student Academics*) purely via `config.yaml` without touching application code.
