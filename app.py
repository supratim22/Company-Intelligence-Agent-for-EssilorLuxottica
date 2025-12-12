# app.py

import sys
import pathlib

import streamlit as st
import pandas as pd

# -----------------------------
# Setup imports from src package
# -----------------------------
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))  # so "src" can be imported

DATA_DIR = PROJECT_ROOT / "data"

from src.kpis import get_kpis_df
from src.llm_agent import answer_question
from src.retrieval import load_tfidf_artifacts  # for Chunk Explorer / Document Viewer


# -----------------------------
# Cached loaders
# -----------------------------
@st.cache_data
def load_kpis(category_arg):
    return get_kpis_df(category_arg)


@st.cache_data
def load_all_chunks():
    # Use the same document store the retriever uses
    df, _, _ = load_tfidf_artifacts()
    return df


# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="EssilorLuxottica – ESG & Financial Analyst",
    layout="wide",
)

st.title("EssilorLuxottica Company Intelligence Agent")

st.markdown(
    """
This app uses a small set of EssilorLuxottica documents (FactSet financials, ESG report,
and annual report excerpts), a TF–IDF retriever, and an LLM to:

- Show key ESG and financial KPIs.
- Answer questions based only on the provided documents.
- Display which text chunks were used for each answer.
"""
)


# -----------------------------
# Sidebar – Company & KPI overview
# -----------------------------
st.sidebar.header("Setup")

# For now, only one company – but this shows how it would scale
company = st.sidebar.selectbox("Company", ["EssilorLuxottica"], index=0)

st.sidebar.header("KPI Overview")

kpi_category = st.sidebar.selectbox(
    "KPI Category",
    options=["all", "financial", "esg", "other"],
    index=2,  # default to "esg" since that's strongest
)

category_arg = None if kpi_category == "all" else kpi_category
kpi_df = load_kpis(category_arg)

st.sidebar.dataframe(
    kpi_df[["name", "value", "unit", "year", "category", "confidence"]],
    use_container_width=True,
)


# -----------------------------
# Tabs
# -----------------------------
tab_snapshot, tab_fin, tab_esg, tab_custom, tab_chunks, tab_doc = st.tabs(
    [
        "Snapshot",
        "Financial Q&A",
        "ESG Q&A",
        "Custom Q&A",
        "Chunk Explorer",
        "Document Viewer",
    ]
)


# -----------------------------
# Run a query through the agent
# -----------------------------
def run_query(question: str, allowed_doc_types=None, k: int = 6):
    if not question.strip():
        st.warning("Please enter a question.")
        return

    with st.spinner("Thinking..."):
        result = answer_question(
            question,
            k=k,
            allowed_doc_types=allowed_doc_types,
        )

    # Answer
    st.markdown("### Answer")
    st.write(result["answer"])

    # Retrieved chunks
    st.markdown("### Retrieved Chunks (for transparency)")
    chunks_df = result["chunks"].copy()
    cols = ["chunk_id", "source", "doc_type", "year", "similarity", "text"]
    cols = [c for c in cols if c in chunks_df.columns]
    st.dataframe(chunks_df[cols], use_container_width=True)


def _get_kpi_value(df: pd.DataFrame, name: str):
    """Safe helper for KPI metric cards."""
    rows = df.loc[df["name"] == name, "value"]
    if rows.empty:
        return None
    v = rows.iloc[0]
    if pd.isna(v):
        return None
    try:
        return float(v)
    except Exception:
        return None


# -----------------------------
# Snapshot Tab
# -----------------------------
with tab_snapshot:
    st.subheader("KPI Snapshot")

    # KPI metric cards (top ESG metrics)
    try:
        col1, col2, col3, col4 = st.columns(4)

        total = _get_kpi_value(kpi_df, "Total GHG emissions (Scope 1+2+3)")
        s1 = _get_kpi_value(kpi_df, "Scope 1 emissions")
        s2 = _get_kpi_value(kpi_df, "Scope 2 emissions (market-based)")
        s3 = _get_kpi_value(kpi_df, "Scope 3 emissions")

        if total is not None:
            col1.metric("Total GHG", f"{int(total):,} tCO₂e")
        if s1 is not None:
            col2.metric("Scope 1", f"{int(s1):,} tCO₂e")
        if s2 is not None:
            col3.metric("Scope 2", f"{int(s2):,} tCO₂e")
        if s3 is not None:
            col4.metric("Scope 3", f"{int(s3):,} tCO₂e")
    except Exception:
        pass

    # Rebuild button
    if st.button("Rebuild KPIs from documents"):
        import subprocess
        import sys as _sys

        with st.spinner("Recomputing KPIs..."):
            subprocess.run([_sys.executable, "-m", "src.auto_kpis"], check=True)
            subprocess.run([_sys.executable, "-m", "src.patch_kpis"], check=True)

            # clear cache so load_kpis reads updated CSV
            st.cache_data.clear()

        st.success("KPIs rebuilt from documents. Reloaded on next run.")

    st.write(
        "Below is a summary of the currently extracted KPIs "
        "(auto-generated from documents, with Scope 1 & 2 patched manually from the ESG report)."
    )
    st.dataframe(kpi_df, use_container_width=True)

    # Simple bar chart for numeric KPIs
    numeric = kpi_df.dropna(subset=["value"]).copy()
    if not numeric.empty:
        st.markdown("#### KPI Values (Bar Chart)")
        chart_df = numeric[["name", "value"]].set_index("name")
        st.bar_chart(chart_df)

    # ESG emissions breakdown
    esg_df = kpi_df[kpi_df["category"] == "esg"].dropna(subset=["value"])
    if not esg_df.empty:
        st.markdown("#### ESG Emissions Breakdown")
        chart_df = esg_df[["name", "value"]].set_index("name")
        st.bar_chart(chart_df)

    # Confidence "heatmap" – show where confidence is weaker
    st.markdown("#### KPI Confidence Overview")
    conf_map = {"high": 3, "manual": 2, "medium": 2, "low": 1, "unknown": 0}
    conf_df = kpi_df.copy()
    conf_df["confidence_score"] = conf_df["confidence"].str.lower().map(conf_map).fillna(0)
    conf_df = conf_df.sort_values("confidence_score", ascending=True)
    st.dataframe(
        conf_df[["name", "category", "value", "unit", "year", "confidence"]],
        use_container_width=True,
    )

    # Download button
    st.download_button(
        "Download KPI Table (CSV)",
        data=kpi_df.to_csv(index=False),
        file_name="essilor_kpis.csv",
        mime="text/csv",
    )

    st.markdown(
        """
**Notes**

- Values are auto-extracted using a KPI-specific RAG prompt.
- Scope 1 and Scope 2 emissions are set to verified values and marked with `confidence="manual"`.
- All other values reflect the LLM extraction with confidence flags.
"""
    )

# -----------------------------
# Chunk Explorer Tab
# -----------------------------
with tab_chunks:
    st.subheader("Chunk Explorer")

    chunks_df_full = load_all_chunks()

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        doc_type_filter = st.selectbox(
            "Filter by doc_type",
            options=["all"] + sorted(chunks_df_full["doc_type"].dropna().unique().tolist()),
            index=0,
        )
    with col2:
        source_filter = st.selectbox(
            "Filter by source",
            options=["all"] + sorted(chunks_df_full["source"].dropna().unique().tolist()),
            index=0,
        )
    with col3:
        year_filter = st.selectbox(
            "Filter by year",
            options=["all"] + sorted(chunks_df_full["year"].dropna().unique().tolist()),
            index=0,
        )

    df = chunks_df_full.copy()
    if doc_type_filter != "all":
        df = df[df["doc_type"] == doc_type_filter]
    if source_filter != "all":
        df = df[df["source"] == source_filter]
    if year_filter != "all":
        df = df[df["year"] == year_filter]

    st.dataframe(
        df[["chunk_id", "source", "doc_type", "year", "text"]],
        use_container_width=True,
    )

# -----------------------------
# Document Viewer Tab
# -----------------------------
with tab_doc:
    st.subheader("Document Viewer (full chunk text)")

    chunks_df_full = load_all_chunks()

    col1, col2 = st.columns([1, 3])
    with col1:
        # Let user pick a chunk to inspect
        chunk_ids = chunks_df_full["chunk_id"].tolist()
        selected_chunk_id = st.selectbox("Select chunk_id", chunk_ids)

    row = chunks_df_full.loc[chunks_df_full["chunk_id"] == selected_chunk_id].iloc[0]

    with col2:
        st.markdown(f"**Source:** {row['source']}")
        st.markdown(f"**doc_type:** {row['doc_type']} | **year:** {row['year']}")
        st.markdown("**Text:**")
        st.write(row["text"])

# -----------------------------
# Financial Q&A Tab
# -----------------------------
with tab_fin:
    st.subheader("Financial Questions")

    # Optional: quick view of financial KPIs
    fin_kpis = kpi_df[kpi_df["category"] == "financial"].dropna(subset=["value"])
    if not fin_kpis.empty:
        st.markdown("#### Financial KPIs (from auto extraction)")
        st.dataframe(fin_kpis[["name", "value", "unit", "year", "confidence"]], use_container_width=True)
        st.bar_chart(fin_kpis[["name", "value"]].set_index("name"))

    q_fin = st.text_input(
        "Ask a financial question (revenue, EBITDA, etc.):",
        value="What was EssilorLuxottica's revenue and EBITDA in 2024?",
        key="q_financial",
    )

    if st.button("Ask (Financial)", key="btn_financial"):
        run_query(q_fin, allowed_doc_types=["financial", "annual"], k=6)

# -----------------------------
# ESG Q&A Tab
# -----------------------------
with tab_esg:
    st.subheader("ESG Questions")

    q_esg = st.text_input(
        "Ask an ESG question (emissions, ESG strategy, etc.):",
        value="What are EssilorLuxottica's Scope 1, 2, and 3 emissions?",
        key="q_esg",
    )

    if st.button("Ask (ESG)", key="btn_esg"):
        run_query(q_esg, allowed_doc_types=["esg"], k=6)

    st.markdown("#### ESG Narrative Summary")
    if st.button("Generate ESG Summary", key="btn_esg_summary"):
        esg_summary_question = (
            "Give a concise 4–5 sentence ESG summary of EssilorLuxottica "
            "based ONLY on the provided documents."
        )
        run_query(esg_summary_question, allowed_doc_types=["esg"], k=8)

# -----------------------------
# Custom Q&A Tab
# -----------------------------
with tab_custom:
    st.subheader("Custom Question")

    q_custom = st.text_area(
        "Ask any question over all documents:",
        value="Summarize EssilorLuxottica's overall ESG and financial profile based on the documents.",
        key="q_custom",
        height=120,
    )

    if st.button("Ask (All Docs)", key="btn_custom"):
        run_query(q_custom, allowed_doc_types=None, k=8)
