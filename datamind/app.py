import streamlit as st
import pandas as pd
import sys
import os

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datamind.core.agent import DataMindAgent

st.set_page_config(
    page_title="DataMind · Enterprise Data Intelligence",
    page_icon="❄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Production-Grade Modern SaaS Theme Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Gradient Header Accent */
    .hero-banner {
        background: linear-gradient(135deg, rgba(20, 26, 40, 0.95) 0%, rgba(13, 17, 23, 0.98) 100%);
        border: 1px solid rgba(41, 181, 232, 0.25);
        border-radius: 16px;
        padding: 24px 30px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }
    
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FFFFFF 0%, #29B5E8 50%, #4285F4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    
    .hero-subtitle {
        color: #94A3B8;
        font-size: 0.98rem;
        font-weight: 400;
        line-height: 1.5;
    }

    /* Status Badges */
    .badge-container {
        display: flex;
        gap: 10px;
        margin-top: 14px;
        flex-wrap: wrap;
    }
    
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(41, 181, 232, 0.1);
        border: 1px solid rgba(41, 181, 232, 0.3);
        color: #38BDF8;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .status-badge.gemma {
        background: rgba(66, 133, 244, 0.1);
        border-color: rgba(66, 133, 244, 0.3);
        color: #8AB4F8;
    }

    .status-badge.guardrail {
        background: rgba(16, 185, 129, 0.1);
        border-color: rgba(16, 185, 129, 0.3);
        color: #34D399;
    }

    /* Metric & KPI Cards */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 14px;
        margin: 18px 0;
    }

    .kpi-card {
        background: #141B26;
        border: 1px solid #232E3F;
        border-radius: 12px;
        padding: 16px 20px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .kpi-card:hover {
        border-color: #29B5E8;
        transform: translateY(-2px);
    }

    .kpi-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .kpi-value {
        font-size: 1.4rem;
        font-weight: 800;
        color: #F8FAFC;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Chat message enhancements */
    .stChatMessage {
        border-radius: 14px !important;
        margin-bottom: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Streamlit tabs modern look */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #232E3F;
        padding-bottom: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        font-size: 0.88rem;
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(41, 181, 232, 0.15) !important;
        color: #38BDF8 !important;
    }

    /* Code Block Monospace Styling */
    pre, code {
        font-family: 'JetBrains Mono', monospace !important;
    }
</style>
""", unsafe_allow_html=True)

# Session State Setup with Isolated Per-Dataset Agent Instances and Memory
if "agents" not in st.session_state:
    st.session_state.agents = {}

# Sidebar Configuration
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/ff/Snowflake_Logo.svg", width=140)
    st.markdown("### **DataMind Control Center**")
    st.caption("ZeroDay OSS Hacktoberfest 2026 · Problem Statement 1")

    st.markdown("---")
    st.markdown("##### ◎ Active Data Warehouse Domain")
    
    # Read config to get datasets
    temp_agent = DataMindAgent()
    dataset_keys = list(temp_agent.config["datasets"].keys())
    dataset_names = [temp_agent.config["datasets"][k]["name"] for k in dataset_keys]
    
    selected_idx = st.selectbox(
        "Select Active Knowledge Domain:",
        range(len(dataset_keys)),
        format_func=lambda x: dataset_names[x]
    )
    selected_key = dataset_keys[selected_idx]

    if "agents" not in st.session_state:
        st.session_state.agents = {}

    if selected_key not in st.session_state.agents:
        agent_inst = DataMindAgent()
        agent_inst.set_active_dataset(selected_key)
        st.session_state.agents[selected_key] = agent_inst

    agent = st.session_state.agents[selected_key]

    if "domain_histories" not in st.session_state:
        st.session_state.domain_histories = {}

    if selected_key not in st.session_state.domain_histories:
        st.session_state.domain_histories[selected_key] = []

    # Active chat history for current selected dataset
    chat_history = st.session_state.domain_histories[selected_key]

    # Domain Info Card
    with st.container():
        st.markdown(f"""
        **Target Table**: `{agent.dataset_info['table_name']}`  
        **Catalog**: `DATAMIND_DB.PUBLIC`  
        **Description**: {agent.dataset_info['description']}
        """)

    # Multi-Turn Conversational Memory Monitor
    st.markdown("---")
    st.markdown("##### 🧠 Conversational Context Monitor")
    turn_count = len(agent.conversation_history)
    if turn_count == 0:
        st.caption("Fresh context: awaiting first inquiry.")
    else:
        st.markdown(f"**{turn_count} turns** in active memory:")
        for idx, t in enumerate(agent.conversation_history[-3:], 1):
            q_short = t['question'][:36] + ("..." if len(t['question']) > 36 else "")
            st.markdown(f"• Turn {idx}: *\"{q_short}\"*")

    st.markdown("---")
    col_reset, col_clear = st.columns(2)
    with col_reset:
        if st.button("↺ Clear Chat", use_container_width=True):
            agent.reset_conversation()
            st.session_state.domain_histories[selected_key] = []
            st.rerun()
    with col_clear:
        if st.button("↻ Reload App", use_container_width=True):
            st.rerun()

    st.markdown("---")
    st.markdown("##### ⛊ Enterprise Safeguards Active")
    st.markdown("""
    - ⚿ **Read-Only AST Guard**: Blocks `DROP`, `DELETE`, `ALTER`
    - ⚲ **Claim-to-Row Badging**: Strict citation indexing
    - ⚡ **Warehouse Monitoring**: Real-time compute tracking
    - ◈ **Model**: Google Gemma 4 (26B MoE)
    """)

    # ── Automated Document / Dataset Ingestor (PDF / CSV / Excel) ──
    st.markdown("---")
    with st.expander("📤 Upload Custom Dataset (CSV / PDF / Excel)"):
        st.caption("Upload a CSV, Excel, or tabular PDF. Gemma 4 automatically infers schema, generates DDL, creates the Snowflake table, and adds it as an active domain.")
        uploaded_file = st.file_uploader(
            "Choose file",
            type=["csv", "xlsx", "xls", "pdf"],
            key="dataset_file_uploader",
            label_visibility="collapsed"
        )
        custom_name = st.text_input("Dataset Display Name (optional):", placeholder="e.g. Q3 Sales Performance")
        if uploaded_file is not None:
            if st.button("⚡ Ingest into Snowflake via Gemma 4", use_container_width=True):
                with st.spinner("Parsing file, inferring schema via Gemma 4, and deploying to Snowflake..."):
                    try:
                        from datamind.core.auto_ingest import DatasetAutoIngestor
                        ingestor = DatasetAutoIngestor()
                        df_up, tbl_up = ingestor.parse_uploaded_file_to_df(uploaded_file)
                        disp_name = custom_name.strip() if custom_name else f"Uploaded {uploaded_file.name}"
                        schema_meta = ingestor.infer_snowflake_schema_and_ddl(df_up, tbl_up, disp_name)
                        new_domain_key = ingestor.deploy_to_snowflake_and_register(df_up, schema_meta)
                        if "domain_histories" in st.session_state:
                            st.session_state.domain_histories[new_domain_key] = []
                        if "agents" in st.session_state:
                            new_agent = DataMindAgent()
                            new_agent.set_active_dataset(new_domain_key)
                            st.session_state.agents[new_domain_key] = new_agent
                        st.success(f"✓ Created table `{tbl_up}` on Snowflake with {len(df_up)} records!")
                        st.info(f"Registered domain **{disp_name}**. Refreshing workspace...")
                        import time
                        time.sleep(1.2)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Ingestion failed: {exc}")

# Hero Section
if selected_key == "student_performance":
    record_badge = "◉ 1,044 Verified Student Records (Math & Portuguese)"
elif selected_key == "global_development":
    record_badge = "◉ 164 Sovereign Economies Loaded"
else:
    record_badge = f"◉ Custom Domain: {agent.dataset_info.get('table_name', 'TABLE')}"

st.markdown(f"""
<div class="hero-banner">
    <div class="hero-title">❄ DataMind Analytics Engine</div>
    <div class="hero-subtitle">
        Natural language data intelligence connected directly to <b>Snowflake Cloud Data Warehouse</b> and orchestrated by <b>Google Gemma 4</b>.
        Every single figure is computed live with inspectable SQL, raw row data, and verifiable claim badges.
    </div>
    <div class="badge-container">
        <span class="status-badge">❄ Snowflake COMPUTE_WH Active</span>
        <span class="status-badge gemma">◈ Google Gemma 4 Reasoning</span>
        <span class="status-badge guardrail">⛊ Anti-Injection AST Guard</span>
        <span class="status-badge">{record_badge}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Quick Discovery Prompt Pills
st.markdown("##### ✦ Suggested Executive Inquiries:")
col1, col2, col3, col4 = st.columns(4)

sample_query = None
if selected_key == "global_development":
    if col1.button("■ Top 5 Economies by GDP (2023)", use_container_width=True):
        sample_query = "What are the top 5 countries by GDP per capita in 2023?"
    if col2.button("▲ India GDP & Emissions Trend", use_container_width=True):
        sample_query = "Show India's GDP per capita and CO2 emissions from 2018 to 2023"
    if col3.button("◉ Compare Argentina & Spain", use_container_width=True):
        sample_query = "Compare the GDP per capita and CO2 emissions of Argentina and Spain in 2022"
    if col4.button("⚲ Explore Available Countries", use_container_width=True):
        sample_query = "Which countries are available in the dataset?"
elif selected_key == "student_performance":
    if col1.button("◆ Pass Rate: Math vs Portuguese", use_container_width=True):
        sample_query = "Compare the pass rate (G3 >= 10) and average final grade between Math and Portuguese students"
    if col2.button("⏱ Study Time Impact on Final Grade", use_container_width=True):
        sample_query = "What is the average final grade (G3) and student count across weekly study time levels?"
    if col3.button("≡ Alcohol Consumption vs Grades", use_container_width=True):
        sample_query = "Compare average final grades (G3) for students with low weekend alcohol (Walc <= 2) versus high weekend alcohol (Walc >= 4)"
    if col4.button("▲ Parental Education Effect", use_container_width=True):
        sample_query = "How does mother education level (Medu) affect students average final grade (G3) and pass rate?"
else:
    tbl_name = agent.dataset_info.get('table_name', 'TABLE')
    if col1.button("■ Sample First 5 Records", use_container_width=True):
        sample_query = f"Show the first 5 records from {tbl_name}"
    if col2.button("▲ Total Record Count", use_container_width=True):
        sample_query = f"What is the total number of records in {tbl_name}?"
    if col3.button("◉ Summary Aggregates", use_container_width=True):
        sample_query = "Show summary statistics or key aggregates across the main numeric columns"
    if col4.button("⚲ Available Schema & Columns", use_container_width=True):
        sample_query = "What columns and data features are available in this table?"

def render_auto_chart(df: pd.DataFrame):
    """
    Intelligently detects time-series and comparative metrics
    to render production-grade interactive visualizations.
    """
    if df is None or df.empty or len(df.columns) < 2:
        return

    df = df.copy()
    # Coerce Snowflake Decimals or numeric strings to float/int
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass

    cols = df.columns.tolist()
    cols_upper = [c.upper() for c in cols]
    
    # 1. Multi-Year Time Series Line Trend
    if any("YEAR" in c for c in cols_upper):
        year_col = [c for c in cols if "YEAR" in c.upper()][0]
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != year_col]
        
        if numeric_cols:
            st.markdown("##### ▲ **Verified Time-Series Visualization**")
            if any("COUNTRY" in c for c in cols_upper):
                country_col = [c for c in cols if "COUNTRY" in c.upper()][0]
                try:
                    pivoted = df.pivot(index=year_col, columns=country_col, values=numeric_cols[0])
                    st.line_chart(pivoted, use_container_width=True)
                except Exception:
                    st.line_chart(df.set_index(year_col)[numeric_cols], use_container_width=True)
            else:
                st.line_chart(df.set_index(year_col)[numeric_cols], use_container_width=True)

    # 2. Categorical Comparison Bar Chart
    else:
        cat_match_keywords = ["SUBJECT", "SCHOOL", "SEX", "STUDYTIME", "WALC", "DALC", "MEDU", "FEDU", "ADDRESS", "COUNTRY", "DEPT", "DEPARTMENT"]
        has_cat = any(any(kw in c for kw in cat_match_keywords) for c in cols_upper)
        if len(cols) >= 2 and (has_cat or df[cols[0]].dtype == "object"):
            cat_col = cols[0]
            num_candidates = df.select_dtypes(include=["number"]).columns.tolist()
            num_candidates = [c for c in num_candidates if c != cat_col]
            if num_candidates:
                val_col = num_candidates[0]
                st.markdown(f"##### ■ **Comparative Analytics: {val_col} by {cat_col}**")
                chart_df = df[[cat_col, val_col]].dropna().set_index(cat_col)
                st.bar_chart(chart_df, use_container_width=True)

# Render Historical Messages for Current Domain
for chat in chat_history:
    with st.chat_message(chat["role"]):
        if chat.get("context_pill"):
            st.markdown(chat["context_pill"], unsafe_allow_html=True)
        if chat.get("guardrail_box") == "warning":
            st.warning(chat["content"])
        elif chat.get("guardrail_box") == "error":
            st.error(chat["content"])
        elif chat.get("guardrail_box") == "info":
            st.info(chat["content"])
        else:
            st.markdown(chat["content"])
        if "df" in chat and chat["df"] is not None and not chat["df"].empty:
            render_auto_chart(chat["df"])
        if "sql" in chat and chat["sql"]:
            with st.expander("⚲ View Inspected SQL & Data Evidence"):
                st.code(chat["sql"], language="sql")
                if "df" in chat and chat["df"] is not None:
                    st.dataframe(chat["df"], use_container_width=True)

# Interactive Chat Input
user_query = st.chat_input("Ask any question or follow up on previous analysis...")
query_to_run = user_query or sample_query

if query_to_run:
    # Append User Message to domain history
    chat_history.append({"role": "user", "content": query_to_run})
    with st.chat_message("user"):
        st.write(query_to_run)

    with st.chat_message("assistant"):
        with st.spinner("⚡ Gemma 4 synthesizing query & executing on Snowflake warehouse..."):
            result = agent.answer_question(query_to_run)

        status = result.get("status")

        if status == "success":
            context_pill = None
            if result.get("is_follow_up") and result.get("prior_inquiry"):
                context_pill = f"""
                <div style="background: rgba(66, 133, 244, 0.12); border: 1px solid rgba(66, 133, 244, 0.35); border-radius: 8px; padding: 6px 14px; margin-bottom: 12px; font-size: 0.85rem; color: #8AB4F8; display: inline-flex; align-items: center; gap: 8px;">
                    <span>🧠</span> <span><b>Multi-Turn Context Resolved</b>: Follow-up contextualized from previous inquiry: <i>"{result['prior_inquiry']}"</i></span>
                </div>
                """
                st.markdown(context_pill, unsafe_allow_html=True)

            st.markdown(result["direct_answer"])

            # Dataframe for rows
            df = None
            if result["rows"] and result["columns"]:
                df = pd.DataFrame(result["rows"], columns=result["columns"])
                # Auto-render chart
                render_auto_chart(df)

            # Executive Evidence Container (M4 & M5)
            st.markdown("---")
            st.markdown("#### ⚲ **Inspectable Evidence & Verification Suite**")
            
            tab_sql, tab_rows, tab_metrics = st.tabs([
                "✎ Executed Snowflake SQL",
                "≡ Live Result Records & Export",
                "⚡ Warehouse Compute & Cost Analytics"
            ])

            with tab_sql:
                st.code(result["sql"], language="sql")
                st.caption("✓ Validated read-only query executed directly on Snowflake compute warehouse at question time.")

            with tab_rows:
                if df is not None and not df.empty:
                    st.dataframe(df, use_container_width=True)
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="↓ Download Grounded Data (CSV)",
                        data=csv_data,
                        file_name=f"datamind_snowflake_result.csv",
                        mime="text/csv",
                        use_container_width=False
                    )
                else:
                    st.warning("No rows returned from the warehouse for the given criteria.")

            with tab_metrics:
                # KPI Grid
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Query Latency</div>
                        <div class="kpi-value">{result['execution_time_ms']} ms</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m2:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Rows Evaluated</div>
                        <div class="kpi-value">{result['row_count']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m3:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Est. Snowflake Credits</div>
                        <div class="kpi-value">{result.get('cost_estimate_credits', 0.0)} cr</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m4:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Reasoning Engine</div>
                        <div class="kpi-value" style="font-size: 1.1rem; color: #8AB4F8;">Gemma 4 (26B)</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.caption(f"Connected to Snowflake Warehouse `COMPUTE_WH` on `DATAMIND_DB.PUBLIC`. Claim citations verified against active query index.")

            # Record in domain history
            chat_history.append({
                "role": "assistant",
                "content": result["direct_answer"],
                "sql": result["sql"],
                "df": df,
                "context_pill": context_pill
            })

        elif status == "ambiguous":
            st.warning(f"**⚠ Ambiguity Detected (M6 Guardrail):**\n\n{result['direct_answer']}")
            chat_history.append({"role": "assistant", "content": result["direct_answer"], "guardrail_box": "warning"})
        elif status == "empty_result":
            st.warning(f"**∅ Empty Result / Zero Matching Records (M6 Guardrail):**\n\n{result['direct_answer']}")
            if result.get("sql"):
                with st.expander("⚲ View Inspected SQL Query"):
                    st.code(result["sql"], language="sql")
            chat_history.append({"role": "assistant", "content": result["direct_answer"], "sql": result.get("sql"), "guardrail_box": "warning"})
        elif status == "refused":
            st.error(f"**⛔ Security Guardrail Refusal (M6 Safeguard):**\n\n{result['direct_answer']}")
            chat_history.append({"role": "assistant", "content": result["direct_answer"], "guardrail_box": "error"})
        elif status in ["out_of_scope", "greeting", "pleasantry"]:
            st.info(f"**ℹ Out of Bounds / Unsupported Request (M6 Guardrail):**\n\n{result['direct_answer']}")
            chat_history.append({"role": "assistant", "content": result["direct_answer"], "guardrail_box": "info"})
        else:
            st.error(f"**✕ Execution Error:**\n\n{result['direct_answer']}")
            chat_history.append({"role": "assistant", "content": result["direct_answer"], "guardrail_box": "error"})
