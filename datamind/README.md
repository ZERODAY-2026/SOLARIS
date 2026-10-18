# ❄️ DataMind: Talk to Your Data

> **ZeroDay OSS Hacktoberfest 2026 · Problem Statement 1 (IIIT Dharwad)**  
> *An open-source, evidence-grounded natural language data intelligence engine orchestrated by Google Gemma 4 and connected live to Snowflake Cloud Data Warehouse.*

---

## 🌟 Overview

**DataMind** empowers decision-makers, educators, and researchers to explore complex relational databases using natural, everyday conversational language. Instead of relying on static precomputed charts or hallucinatory LLM summaries, DataMind dynamically:

1. **Synthesizes Optimal Snowflake SQL** in real time from natural language inquiries.
2. **Executes Read-Only Queries Live** on Snowflake compute warehouses with sub-second latency tracking.
3. **Generates Grounded Explanations** where every single number is cited with verifiable claim-to-row badges (e.g. `[Row 1, Col: AVG_FINAL_GRADE]`).
4. **Enforces Multi-Layer Security** via AST token inspection that permanently blocks `DROP`, `DELETE`, `UPDATE`, or SQL injection attempts.
5. **Maintains Multi-Turn Conversational Memory** allowing natural contextual follow-ups (e.g. *"what about female students in math"*).
6. **Renders Dynamic Visualizations** (comparative bar charts and time-series line trends) built strictly from verified warehouse data.

---

## 📋 Prerequisites

Before installing DataMind, ensure your environment meets the following requirements:

* **Python**: Version `3.10` or higher (tested on Python 3.10, 3.11, 3.12, 3.14).
* **Snowflake Account**: Any standard Snowflake trial or enterprise account with permissions on a warehouse (`COMPUTE_WH`), database, and schema.
* **OpenRouter API Key**: An active OpenRouter key with access to Google Gemma models (`google/gemma-4-26b-a4b-it` or compatible Gemma variants).
* **Git**: Installed on your system for repository management.

---

## 🚀 Step-by-Step Installation Guide

### Step 1: Clone the Repository
```bash
git clone https://github.com/ZERODAY-2026/SOLARIS.git
cd SOLARIS
```

### Step 2: Set Up a Python Virtual Environment
We strongly recommend using a clean virtual environment to prevent dependency conflicts:

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (Command Prompt or PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Required Dependencies
All core dependencies are pinned in `requirements.txt`:
```bash
pip install -r requirements.txt
```

#### What `requirements.txt` Installs:
* `snowflake-connector-python>=3.10.0`: Official high-performance Python client for Snowflake.
* `python-dotenv>=1.0.0`: Secure environment variable management.
* `pyyaml>=6.0.0`: Schema and multi-dataset configuration parser.
* `requests>=2.31.0`: HTTPS communication with Google Gemma on OpenRouter.
* `streamlit>=1.35.0`: Interactive, modern dark SaaS analytical user interface.
* `pandas>=2.0.0`: Tabular data manipulation and type coercion for visualization.

---

## 🔐 Environment Configuration (.env Setup)

DataMind keeps all sensitive credentials out of version control via `.gitignore`. You must configure your own credentials in a `.env` file.

1. Create your local `.env` file from the provided template:
   ```bash
   cp .env.example .env
   ```
   *(On Windows Command Prompt, run: `copy .env.example .env`)*

2. Open `.env` in your text editor and fill in your details:
   ```ini
   # ==============================================================================
   # Snowflake Cloud Data Warehouse Credentials
   # ==============================================================================
   SNOWFLAKE_ACCOUNT=your_snowflake_account_id        # e.g. "xy12345" or "xy12345.ap-south-1.aws"
   SNOWFLAKE_HOST=your_account.snowflakecomputing.com  # e.g. "xy12345.ap-south-1.aws.snowflakecomputing.com"
   SNOWFLAKE_USER=your_snowflake_username            # e.g. "ADMIN_USER"
   SNOWFLAKE_PASSWORD=your_snowflake_password        # Your secure password
   SNOWFLAKE_WAREHOUSE=COMPUTE_WH                   # Target Snowflake warehouse
   SNOWFLAKE_DATABASE=DATAMIND_DB                   # Database name
   SNOWFLAKE_SCHEMA=PUBLIC                          # Schema name
   SNOWFLAKE_ROLE=ACCOUNTADMIN                      # Snowflake role

   # ==============================================================================
   # Google Gemma 4 Inference Configuration (OpenRouter API)
   # ==============================================================================
   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxx    # Your OpenRouter API key
   GEMMA_MODEL=google/gemma-4-26b-a4b-it            # Google Gemma 4 model slug
   ```

> [!IMPORTANT]
> Never commit your real `.env` file to any public Git repository. It is ignored by default in `.gitignore`.

---

## 💾 Ingesting the Benchmark Dataset into Snowflake

DataMind includes an automated pipeline that downloads the official **UCI Machine Learning Student Performance Benchmark**, normalizes all 33 features across Mathematics and Portuguese courses, and ingests all **1,044 records** into your Snowflake table `STUDENT_PERFORMANCE`:

```bash
python data/ingest_uci_students.py
```

**Expected output:**
```
[1/4] Downloading official UCI Student Performance benchmark archive...
[2/4] Extracting student-mat.csv and student-por.csv...
Combined dataset: 1044 rows, 35 columns.
[3/4] Connecting to Snowflake and creating table STUDENT_PERFORMANCE...
[4/4] Ingesting 1044 student records into Snowflake...
Successfully committed all 1044 records into Snowflake table STUDENT_PERFORMANCE!
Verification: 1044 total records across 2 subjects committed.
```

*(Optional: To also load the secondary macroeconomic dataset `GLOBAL_INDICATORS` with 164 countries, run: `python data/load_data.py`)*

---

## 🖥️ Launching the Application

Start the Streamlit dashboard:
```bash
streamlit run app.py
```

Open your browser at **`http://localhost:8501`** to interact with the system.

---

## 🧪 Running Automated Tests

Run the test suite to verify grounded claims, mathematical derivations, and multi-turn context retention:

```bash
# Test multi-turn conversational follow-up and student query derivations
python tests/test_student_queries.py

# Test intent triage (valid vs ambiguous vs malicious)
python tests/test_triage.py

# Test claim-to-row grounding and AST security guardrails
python -m unittest tests/test_grounding.py
```

---

## 🛠️ Comprehensive Troubleshooting Guide

### 1. Snowflake Connection Errors (`250001: Could not connect to Snowflake`)
* **Symptom**: `OperationalError: 250001: Could not connect to Snowflake backend` or `Incorrect username or password`.
* **Solutions**:
  1. Verify `SNOWFLAKE_ACCOUNT` and `SNOWFLAKE_HOST`: The host should be formatted as `<account_id>.<region>.aws.snowflakecomputing.com`.
  2. Double-check that your Snowflake warehouse (`COMPUTE_WH`) is active and not suspended or dropped.
  3. Ensure your Snowflake network policy allows traffic from your client IP address.

### 2. "I can only see 100 rows in Snowflake Snowsight UI"
* **Explanation**: This is Snowflake's default UI preview behavior. In Snowsight, clicking "Data Preview" on a table runs an automatic `LIMIT 100` to prevent crashing browser memory on massive enterprise datasets.
* **Verification**: In a Snowflake worksheet, run:
  ```sql
  SELECT COUNT(*) FROM DATAMIND_DB.PUBLIC.STUDENT_PERFORMANCE;
  ```
  This will confirm all **1,044 records** are permanently stored.

### 3. OpenRouter API Failures (`401 Unauthorized` or `429 Rate Limit Exceeded`)
* **Symptom**: `OpenRouter API Error 401` or `No response from Gemma model`.
* **Solutions**:
  1. Check that `OPENROUTER_API_KEY` is correctly set in your `.env` file without leading or trailing spaces.
  2. Confirm your OpenRouter account has positive credit balance.
  3. If rate-limited (`429`), wait a few moments before submitting your next prompt or configure a fallback Gemma model tier in `.env`.

### 4. Visual Charts Not Rendering in Streamlit
* **Symptom**: The SQL executes and tables display, but no bar or line chart appears.
* **Explanation**: Snowflake returns aggregated columns as Python `Decimal` objects. DataMind automatically runs `pd.to_numeric` on result columns to coerce them into native floats.
* **Solution**: Ensure you are running the latest version of `app.py`. Clear the Streamlit cache by pressing **"C"** in the web interface and selecting **"Clear Cache"**, then reload.

### 5. `Port 8501 is already in use`
* **Symptom**: Streamlit displays a port collision error.
* **Solution**: Start Streamlit on a different port:
  ```bash
  streamlit run app.py --server.port 8502
  ```

---

## 🏛️ Project Directory Structure

```
SOLARIS/
├── .env.example                  # Environment template for new users
├── .gitignore                    # Strictly protects credentials from git
├── LICENSE                       # Open-source Apache 2.0 license
├── README.md                     # Comprehensive setup, usage & troubleshooting
├── requirements.txt              # Pinned Python package dependencies
├── app.py                        # Streamlit Intelligence Desk with charts & evidence
├── config.yaml                   # Multi-dataset mapping (Student Performance & Global Dev)
├── TEAM_HANDOVER_GUIDE.md        # Technical architecture, pros/cons & live demo script
├── core/
│   ├── agent.py                  # Main orchestrator: multi-turn memory, schema discovery, cost
│   ├── gemma_client.py           # Google Gemma 4 client via OpenRouter API
│   ├── prompts.py                # System prompts with mathematical derivation guardrails
│   └── snowflake_client.py       # AST read-only guardrails & live Snowflake executor
├── data/
│   ├── ingest_uci_students.py    # Automated downloader & loader for 1,044 UCI students
│   └── load_data.py              # Secondary loader for 164-country global development data
└── tests/
    ├── test_grounding.py         # Grounding and claim-to-row verification unit tests
    ├── test_student_queries.py   # Multi-turn context and mathematical derivation tests
    ├── test_triage.py            # Intent and ambiguity classification tests
    └── test_typos.py             # Slang and typo-resilience tests
```

---

## 🛡️ Hackathon Mandatory Core Features (M1–M8 Compliance)

* **M1 (Everyday Language)**: Normalizes conversational English, slang, and misspellings without requiring rigid keywords.
* **M2 (Live Retrieval)**: Queries actual live records in Snowflake compute warehouse at question time with zero mocking.
* **M3 (Strict Grounding)**: Enforces claim-to-row badge citations (`[Row X, Col: Y]`) with zero hallucinated values.
* **M4 & M5 (Inspectable Evidence)**: 3-tab verification container showing executed SQL, raw records, execution latency, and 1-click CSV export.
* **M6 (Safety & Ambiguity Triage)**: AST guardrail blocks destructive SQL (`DROP`, `DELETE`), while ambiguity triage guides underspecified queries.
* **M7 (Meaningful Integration)**: Deep synergy between Google Gemma 4 (cognitive reasoning) and Snowflake (analytical data warehouse).
* **M8 & Criterion 7 (Reusability & Adaptability)**: Dynamic multi-dataset switching driven purely by `config.yaml`.

---

## 📜 License
This project is licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.
