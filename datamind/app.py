import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from datamind.core.agent import DataMindAgent

st.set_page_config(page_title="DataMind · Intelligence Desk", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

# Visual direction: editorial research desk rather than a conventional chatbot.
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#e9eee9; --muted:#8d9a92; --panel:#151c19; --line:#2a3730; --lime:#c7f36b; --mint:#8fe0bd; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background: radial-gradient(ellipse at 80% 0%, #1a2a22 0%, #101613 42%, #0c100e 100%); color:var(--ink); }
[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:1.7rem; padding-bottom:3rem; max-width:1500px; }
[data-testid="stSidebar"] { background:#111714; border-right:1px solid var(--line); }
[data-testid="stSidebar"] .block-container { padding-top:1.5rem; }
.eyebrow { color:var(--lime); text-transform:uppercase; letter-spacing:.19em; font:500 10px 'DM Mono',monospace; }
.hero-title { font:800 clamp(2.2rem,4vw,4.1rem)/1.04 'Manrope',sans-serif; letter-spacing:-.065em; margin:.5rem 0 .7rem; color:#f0f4ef; }
.hero-title span { color:var(--lime); }
.hero-sub { color:#a1aea5; max-width:740px; font-size:15px; line-height:1.65; }
.rule { height:1px; background:linear-gradient(90deg,var(--lime),#344239 42%,transparent); margin:1.4rem 0 1.5rem; }
.kicker { font:500 10px 'DM Mono',monospace; color:#8d9a92; text-transform:uppercase; letter-spacing:.13em; }
.stat-card { background:linear-gradient(145deg,#1a241e,#141a17); border:1px solid #2a3930; border-radius:13px; padding:15px 17px; min-height:88px; }
.stat-label { font:500 10px 'DM Mono',monospace; color:#93a197; text-transform:uppercase; letter-spacing:.1em; }
.stat-value { font:700 24px 'Manrope',sans-serif; color:#eff5ee; margin-top:6px; }
.stat-note { font-size:11px; color:#8d9a92; margin-top:2px; }
.section-title { font:700 17px 'Manrope',sans-serif; letter-spacing:-.025em; color:#edf3ed; }
.prompt-card { background:#151d18; border:1px solid #2c3a31; padding:13px 15px; border-radius:12px; min-height:82px; }
.prompt-tag { color:var(--lime); font:500 10px 'DM Mono',monospace; letter-spacing:.08em; }
.prompt-copy { color:#dce5dd; font-size:13px; margin-top:6px; line-height:1.4; }
.answer-panel { background:linear-gradient(135deg,#17231b,#151b18); border:1px solid #354b3a; border-left:3px solid var(--lime); border-radius:12px; padding:20px 22px; }
.answer-label { color:var(--lime); font:500 10px 'DM Mono',monospace; text-transform:uppercase; letter-spacing:.14em; margin-bottom:8px; }
div[data-testid="stChatMessage"] { background:#141b17; border:1px solid #27342c; border-radius:13px; padding:14px; }
.stButton > button { border-radius:9px; border:1px solid #35453a; background:#19221c; color:#e5eee6; font-weight:600; transition:all .15s ease; }
.stButton > button:hover { border-color:var(--lime); color:var(--lime); background:#202c23; }
.stButton > button[kind="primary"] { background:var(--lime); color:#172015; border-color:var(--lime); }
.stButton > button[kind="primary"]:hover { background:#d7ff8a; color:#172015; }
.stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div { background:#121915 !important; border-color:#344238 !important; color:#eaf0e9 !important; border-radius:9px !important; }
.stTabs [data-baseweb="tab-list"] { gap:6px; border-bottom:1px solid #2b3930; }
.stTabs [data-baseweb="tab"] { background:#151c18; border-radius:8px 8px 0 0; color:#a8b5ab; padding:10px 15px; }
.stTabs [aria-selected="true"] { color:var(--lime) !important; border-bottom-color:var(--lime) !important; }
[data-testid="stDataFrame"] { border:1px solid #2a3930; border-radius:10px; overflow:hidden; }
.stAlert { border-radius:10px; }
div[data-testid="stExpander"] { background:#141b17; border:1px solid #2b3930; border-radius:10px; }
footer {visibility:hidden;}
.small-note { color:#849188; font-size:11px; }
code, .stCode { font-family:'DM Mono',monospace !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_agent():
    return DataMindAgent()

agent = get_agent()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "query_text" not in st.session_state:
    st.session_state.query_text = ""
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# Sidebar: controls that affect actual query behavior.
with st.sidebar:
    st.markdown('<div class="eyebrow">◈ DATAMIND / WORKSPACE</div>', unsafe_allow_html=True)
    st.markdown("## Intelligence desk")
    st.caption("Live data · evidence-first answers")
    st.divider()
    dataset_keys = list(agent.config["datasets"].keys())
    dataset_names = [agent.config["datasets"][k]["name"] for k in dataset_keys]
    current_idx = dataset_keys.index(agent.active_dataset_key) if agent.active_dataset_key in dataset_keys else 0
    selected_idx = st.selectbox("KNOWLEDGE DOMAIN", range(len(dataset_keys)), index=current_idx, format_func=lambda x: dataset_names[x])
    selected_key = dataset_keys[selected_idx]
    if agent.active_dataset_key != selected_key:
        agent.set_active_dataset(selected_key)
        agent.reset_conversation()
        st.session_state.chat_history = []
        st.session_state.last_result = None
        st.rerun()

    st.markdown("**Active source**")
    st.code(agent.dataset_info["table_name"], language=None)
    st.caption(agent.dataset_info.get("description", "Configured Snowflake dataset"))
    st.divider()
    st.markdown("**SESSION TOOLS**")
    if st.button("＋ New analysis", use_container_width=True):
        agent.reset_conversation()
        st.session_state.chat_history = []
        st.session_state.last_result = None
        st.session_state.query_text = ""
        st.rerun()
    if st.session_state.chat_history:
        options = list(range(len(st.session_state.chat_history)))
        picked = st.selectbox("Recent questions", options, format_func=lambda i: st.session_state.chat_history[i].get("question", f"Analysis {i+1}")[:54])
        if st.button("↺ Reuse selected question", use_container_width=True):
            st.session_state.query_text = st.session_state.chat_history[picked].get("question", "")
            st.rerun()
    st.divider()
    st.markdown("**TRUST & TRACEABILITY**")
    st.markdown("<div class='small-note'>◉ Read-only SQL guardrails<br>◉ Row-grounded explanations<br>◉ Live Snowflake execution<br>◉ Inspectable query evidence</div>", unsafe_allow_html=True)
    st.markdown("<br><div class='small-note'>DATA PLATFORM · SNOWFLAKE<br>REASONING LAYER · GEMMA VIA OPENROUTER</div>", unsafe_allow_html=True)

# Hero
st.markdown('<div class="eyebrow">FIELD NOTES  /  ANALYTICS SYSTEM 01</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Ask better questions.<br><span>Get answers with receipts.</span></div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">A research workspace for exploring live warehouse data in plain language. Every answer comes with the query, returned rows, and execution details so you can check the work—not just trust the summary.</div>', unsafe_allow_html=True)
st.markdown('<div class="rule"></div>', unsafe_allow_html=True)

# Compact live workspace indicators.
last = st.session_state.last_result or {}
latency = f"{last.get('execution_time_ms', '—')} ms" if last else "—"
rows_count = str(last.get("row_count", "—")) if last else "—"
cost = f"{last.get('cost_estimate_credits', 0.0):.4f} cr" if last else "—"
c1, c2, c3, c4 = st.columns(4)
for col, label, value, note in [
    (c1, "ACTIVE DOMAIN", agent.dataset_info["name"], "Selected knowledge source"),
    (c2, "LAST LATENCY", latency, "Warehouse execution"),
    (c3, "ROWS RETURNED", rows_count, "Most recent successful query"),
    (c4, "EST. CREDITS", cost, "Latest query estimate"),
]:
    with col:
        st.markdown(f'<div class="stat-card"><div class="stat-label">{label}</div><div class="stat-value" style="font-size:{"17px" if label == "ACTIVE DOMAIN" else "24px"}">{value}</div><div class="stat-note">{note}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Start with a direction</div><div class="small-note">Choose a research lead, or write your own question below.</div>', unsafe_allow_html=True)
if selected_key == "global_development":
    samples = [
        ("01 / RANK", "Top 5 countries by GDP per capita in 2023", "What are the top 5 countries by GDP per capita in 2023?"),
        ("02 / TREND", "India GDP and life expectancy, 2018–2023", "Show India's GDP per capita and life expectancy from 2018 to 2023"),
        ("03 / DISCOVER", "Which countries are in this dataset?", "Which countries are available in the dataset?"),
        ("04 / COMPARE", "China vs India CO₂ emissions in 2023", "Compare CO2 emissions per capita between China and India in 2023"),
    ]
else:
    samples = [
        ("01 / RANK", "Department with highest average exam score", "Which department has the highest average exam score?"),
        ("02 / FILTER", "Students with A/A+ and weekly study hours", "List all students with an A or A+ grade and their weekly study hours"),
        ("03 / SCHEMA", "Explore available metrics and columns", "What metrics and columns are in this table?"),
        ("04 / SIGNAL", "Students with attendance below 70%", "Which students have attendance below 70 percent?"),
    ]
cols = st.columns(4)
for i, (tag, title, query) in enumerate(samples):
    with cols[i]:
        st.markdown(f'<div class="prompt-card"><div class="prompt-tag">{tag}</div><div class="prompt-copy">{title}</div></div>', unsafe_allow_html=True)
        if st.button("Explore ↗", key=f"sample_{i}", use_container_width=True):
            st.session_state.query_text = query
            st.session_state.run_query_now = True

st.markdown("<br>", unsafe_allow_html=True)
with st.form("query_form", clear_on_submit=False):
    st.markdown('<div class="section-title">Your question</div>', unsafe_allow_html=True)
    query_value = st.text_area("Ask in natural language", value=st.session_state.query_text, height=95, placeholder="e.g. Which regions improved the most, and what evidence supports that?", label_visibility="collapsed")
    left, right = st.columns([4, 1])
    with left:
        st.caption("Tip: specify a metric, time range, or comparison to make the result more precise.")
    with right:
        submitted = st.form_submit_button("Run analysis  ↗", type="primary", use_container_width=True)

run_sample = st.session_state.pop("run_query_now", False)
query_to_run = query_value.strip() if submitted else (st.session_state.query_text.strip() if run_sample else "")
if query_to_run:
    st.session_state.query_text = query_to_run
    with st.spinner("Translating question · validating SQL · querying Snowflake…"):
        result = agent.answer_question(query_to_run)
    st.session_state.last_result = result if result.get("status") == "success" else st.session_state.last_result
    status = result.get("status")
    st.markdown("<div class='rule'></div>", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">LATEST RUN  /  EVIDENCE RECORD</div>', unsafe_allow_html=True)
    if status == "success":
        st.markdown('<div class="answer-panel"><div class="answer-label">◉ VERIFIED RESPONSE</div>', unsafe_allow_html=True)
        st.markdown(result.get("direct_answer", "No answer returned."))
        st.markdown('</div>', unsafe_allow_html=True)
        df = pd.DataFrame(result.get("rows", []), columns=result.get("columns", [])) if result.get("columns") else pd.DataFrame()
        if not df.empty:
            st.markdown("<br><div class='section-title'>Read the shape of the data</div>", unsafe_allow_html=True)
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            categorical_cols = [c for c in df.columns if c not in numeric_cols]
            chart_col1, chart_col2 = st.columns([1, 1])
            with chart_col1:
                chart_type = st.selectbox("VIEW", ["Auto view", "Table only", "Bar comparison", "Line trend"], key=f"chart_type_{len(st.session_state.chat_history)}")
            with chart_col2:
                if numeric_cols and categorical_cols:
                    x_col = st.selectbox("CATEGORY / X AXIS", categorical_cols, key=f"x_{len(st.session_state.chat_history)}")
                    y_col = st.selectbox("MEASURE / Y AXIS", numeric_cols, key=f"y_{len(st.session_state.chat_history)}")
                else:
                    x_col = y_col = None
            should_chart = chart_type in ["Bar comparison", "Line trend"] or (chart_type == "Auto view" and len(df.columns) == 2 and x_col and y_col)
            if should_chart and x_col and y_col:
                plot_df = df[[x_col, y_col]].dropna().set_index(x_col)
                if chart_type == "Line trend" or (chart_type == "Auto view" and any("YEAR" in str(x).upper() for x in [x_col])):
                    st.line_chart(plot_df)
                else:
                    st.bar_chart(plot_df)
            with st.expander("Open result table", expanded=True):
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.download_button("↓ Download results as CSV", data=df.to_csv(index=False).encode("utf-8"), file_name=f"datamind_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv")
        else:
            st.info("The warehouse returned no rows for this query.")
        st.markdown("<br><div class='section-title'>Evidence locker</div><div class='small-note'>Inspect exactly what ran and what came back from the warehouse.</div>", unsafe_allow_html=True)
        tab_sql, tab_rows, tab_perf = st.tabs(["01 · Executed SQL", "02 · Returned rows", "03 · Runtime & cost"])
        with tab_sql:
            sql = result.get("sql", "")
            st.code(sql, language="sql")
            st.download_button("↓ Save SQL", data=sql, file_name="datamind_query.sql", mime="text/sql")
            st.caption("Validated read-only query executed against the configured Snowflake warehouse.")
        with tab_rows:
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.caption("No result rows to display.")
        with tab_perf:
            p1, p2, p3 = st.columns(3)
            p1.metric("Execution latency", f"{result.get('execution_time_ms', '—')} ms")
            p2.metric("Rows returned", result.get("row_count", len(df)))
            p3.metric("Estimated credits", f"{result.get('cost_estimate_credits', 0.0)} cr")
            st.caption("Credit usage is an estimate supplied by the application; actual billing may differ.")
        st.session_state.chat_history.append({"role": "assistant", "question": query_to_run, "content": result.get("direct_answer", ""), "sql": result.get("sql", ""), "df": df, "result": result})
    else:
        messages = {
            "ambiguous": ("Clarification needed", "The question may have more than one interpretation. Refine the metric, group, or time range and try again."),
            "refused": ("Safety guardrail activated", "This request was blocked by the query safety layer."),
            "out_of_scope": ("Outside this data domain", "Try asking about information available in the selected dataset."),
        }
        heading, hint = messages.get(status, ("The analysis could not complete", "Check the configuration and service connectivity, then try again."))
        st.warning(f"**{heading}**\n\n{result.get('direct_answer', hint)}\n\n_{hint}_")
        st.session_state.chat_history.append({"role": "assistant", "question": query_to_run, "content": result.get("direct_answer", hint)})

# Session timeline stays useful after the latest answer.
if st.session_state.chat_history:
    st.markdown("<div class='rule'></div><div class='section-title'>Session trail</div><div class='small-note'>Questions asked in this workspace. Reuse any prompt from the left rail.</div>", unsafe_allow_html=True)
    for idx, item in enumerate(reversed(st.session_state.chat_history[-8:])):
        with st.expander(f"{len(st.session_state.chat_history) - idx:02d}  ·  {item.get('question', 'Analysis')}"):
            st.markdown(item.get("content", ""))
            if item.get("sql"):
                st.code(item["sql"], language="sql")

st.markdown("<br><div class='small-note'>DATAMIND / Built for inspectable, evidence-grounded exploration · Responses depend on live source availability.</div>", unsafe_allow_html=True)
