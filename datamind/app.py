import streamlit as st
import pandas as pd
import sys
import os

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datamind.core.agent import DataMindAgent

st.set_page_config(
    page_title="DataMind - Talk to Your Data",
    page_icon="❄️",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .metric-card {
        background-color: #1e2530;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #29B5E8;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_agent():
    return DataMindAgent()

agent = get_agent()

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar: Controls & Dataset Selection
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/ff/Snowflake_Logo.svg", width=160)
    st.title("DataMind Settings")
    
    st.subheader("Active Knowledge Domain")
    dataset_keys = list(agent.config["datasets"].keys())
    dataset_names = [agent.config["datasets"][k]["name"] for k in dataset_keys]
    
    selected_idx = st.selectbox(
        "Choose Dataset:",
        range(len(dataset_keys)),
        format_func=lambda x: dataset_names[x]
    )
    selected_key = dataset_keys[selected_idx]
    
    # If dataset changed, reset conversation
    if agent.active_dataset_key != selected_key:
        agent.set_active_dataset(selected_key)
        st.session_state.chat_history = []
        st.rerun()

    st.info(f"**Target Table:** `{agent.dataset_info['table_name']}`\n\n{agent.dataset_info['description']}")
    
    if st.button("🔄 Reset Conversation History"):
        agent.reset_conversation()
        st.session_state.chat_history = []
        st.success("Conversation cleared!")
        st.rerun()

    st.divider()
    st.markdown("### System Architecture")
    st.markdown("""
    - **Data Platform**: Snowflake (Trial Cloud Warehouse)
    - **AI Model**: Google Gemma 4 (26B/31B MoE)
    - **Safety Layer**: AST Read-Only & Anti-Injection Guardrails
    - **Grounding**: Strict Claim-to-Row Verification
    - **Memory**: Multi-Turn Follow-Up Support
    """)

# Main Screen
st.title("❄️ DataMind: Talk to Your Data")
st.caption("ZeroDay OSS Hacktoberfest 2026 · Problem Statement 1 (IIIT Dharwad)")

st.markdown("""
Ask questions in everyday natural language. Every answer is **computed from live Snowflake data** at question time, with complete inspectable evidence, automatic data visualizations, and cost tracking.
""")

# Quick Question Pills
st.markdown("##### 💡 Try Sample Inquiries:")
col1, col2, col3, col4 = st.columns(4)

sample_query = None
if selected_key == "global_development":
    if col1.button("📊 Top 5 Countries by GDP (2023)"):
        sample_query = "What are the top 5 countries by GDP per capita in 2023?"
    if col2.button("📈 India GDP & Life Expectancy Trend"):
        sample_query = "Show India's GDP per capita and life expectancy from 2018 to 2023"
    if col3.button("🌍 Which Countries Are Available?"):
        sample_query = "Which countries are available in the dataset?"
    if col4.button("🌱 CO2 Comparison (China vs India)"):
        sample_query = "Compare CO2 emissions per capita between China and India in 2023"
else:
    if col1.button("🎓 Highest Average Exam Score"):
        sample_query = "Which department has the highest average exam score?"
    if col2.button("⏱️ Study Hours vs Grade"):
        sample_query = "List all students with an A or A+ grade and their weekly study hours"
    if col3.button("📋 Show Table Schema"):
        sample_query = "What metrics and columns are in this table?"
    if col4.button("📉 Low Attendance Students"):
        sample_query = "Which students have attendance below 70 percent?"

# Helper function to auto-render interactive charts
def render_auto_chart(df: pd.DataFrame):
    """
    Automatically detects whether result rows contain a time series
    or categorical comparison and renders an interactive chart.
    """
    cols = df.columns.tolist()
    cols_upper = [c.upper() for c in cols]
    
    # 1. Time series trend (e.g. contains 'YEAR' and numeric metrics)
    if any("YEAR" in c for c in cols_upper):
        year_col = [c for c in cols if "YEAR" in c.upper()][0]
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != year_col]
        
        if numeric_cols:
            st.markdown("##### 📈 Interactive Verified Trend Chart")
            # If multiple countries exist, pivot or chart directly
            if any("COUNTRY" in c for c in cols_upper):
                country_col = [c for c in cols if "COUNTRY" in c.upper()][0]
                try:
                    pivoted = df.pivot(index=year_col, columns=country_col, values=numeric_cols[0])
                    st.line_chart(pivoted)
                except Exception:
                    st.line_chart(df.set_index(year_col)[numeric_cols])
            else:
                st.line_chart(df.set_index(year_col)[numeric_cols])

    # 2. Categorical comparison (e.g. Country or Department vs Metric)
    elif len(cols) == 2 and (any("COUNTRY" in c or "DEPT" in c or "DEPARTMENT" in c for c in cols_upper)):
        cat_col = cols[0]
        val_col = cols[1]
        if pd.api.types.is_numeric_dtype(df[val_col]):
            st.markdown("##### 📊 Interactive Comparison Chart")
            st.bar_chart(df.set_index(cat_col)[val_col])

# Render prior chat messages
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])
        if "sql" in chat and chat["sql"]:
            with st.expander("🔍 View Executed SQL & Rows"):
                st.code(chat["sql"], language="sql")
                if "df" in chat and chat["df"] is not None:
                    st.dataframe(chat["df"], use_container_width=True)

# Chat Input Form
user_query = st.chat_input("Ask a question or follow up on the previous answer...")
query_to_run = user_query or sample_query

if query_to_run:
    with st.chat_message("user"):
        st.write(query_to_run)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing question with Gemma & querying Snowflake..."):
            result = agent.answer_question(query_to_run)

        status = result.get("status")

        if status == "success":
            st.markdown(result["direct_answer"])

            # Dataframe for rows
            df = None
            if result["rows"] and result["columns"]:
                df = pd.DataFrame(result["rows"], columns=result["columns"])
                # Auto-render chart if applicable (Optional Feature from PDF)
                render_auto_chart(df)

            # Inspectable Evidence Tabs (Mandatory M4 & M5)
            st.divider()
            st.subheader("🔍 Inspectable Evidence & Traceability")
            tab_sql, tab_rows, tab_metrics = st.tabs([
                "📝 Executed Snowflake SQL",
                "📋 Live Result Rows",
                "⚡ Warehouse Performance & Cost"
            ])

            with tab_sql:
                st.code(result["sql"], language="sql")
                st.caption("Validated read-only query executed directly on Snowflake warehouse at question time.")

            with tab_rows:
                if df is not None and not df.empty:
                    st.dataframe(df, use_container_width=True)
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Export Verified Rows (CSV)",
                        data=csv_data,
                        file_name=f"datamind_query_results.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No rows returned from the warehouse for the given criteria.")

            with tab_metrics:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Execution Latency", f"{result['execution_time_ms']} ms")
                m2.metric("Rows Examined", result["row_count"])
                m3.metric("Est. Credits Consumed", f"{result.get('cost_estimate_credits', 0.0)} cr")
                m4.metric("AI Reasoner", "Gemma 4 (26B MoE)")
                
                st.caption(f"Connected to Snowflake Warehouse `COMPUTE_WH` on `DATAMIND_DB.PUBLIC`. Claim citations verified against active query index.")

            # Store in session state
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result["direct_answer"],
                "sql": result["sql"],
                "df": df
            })

        elif status == "ambiguous":
            st.warning(f"**Ambiguity Detected (M6 Guardrail):**\n\n{result['direct_answer']}")
            st.session_state.chat_history.append({"role": "assistant", "content": result["direct_answer"]})
        elif status == "refused":
            st.error(f"**Security Guardrail Refusal (M6):**\n\n{result['direct_answer']}")
            st.session_state.chat_history.append({"role": "assistant", "content": result["direct_answer"]})
        elif status == "out_of_scope":
            st.info(f"**Scope Boundary (M6):**\n\n{result['direct_answer']}")
            st.session_state.chat_history.append({"role": "assistant", "content": result["direct_answer"]})
        else:
            st.error(f"**Execution Error:**\n\n{result['direct_answer']}")
            st.session_state.chat_history.append({"role": "assistant", "content": result["direct_answer"]})
