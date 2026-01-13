#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Translation Accuracy Test Tool - Web UI
Streamlit-based web interface for translation testing
"""
import streamlit as st
import pandas as pd
import json
import tempfile
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from extractors import extract_from_pptx, extract_from_pdf
from tts import EdgeTTSClient
from translators import FeloTranslator
from evaluators import TextComparator
from reporters import ReportGenerator

# Page config
st.set_page_config(
    page_title="Translation Accuracy Test Tool",
    page_icon="🔤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .error-highlight {
        background-color: #ffcccc;
        padding: 2px 5px;
        border-radius: 3px;
    }
    .success-highlight {
        background-color: #ccffcc;
        padding: 2px 5px;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'test_results' not in st.session_state:
        st.session_state.test_results = None
    if 'summary' not in st.session_state:
        st.session_state.summary = None
    if 'before_summary' not in st.session_state:
        st.session_state.before_summary = None
    if 'after_summary' not in st.session_state:
        st.session_state.after_summary = None


def extract_text_from_file(uploaded_file):
    """Extract text pairs from uploaded file"""
    suffix = Path(uploaded_file.name).suffix.lower()

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = Path(tmp.name)

    try:
        if suffix == ".pptx":
            pairs = extract_from_pptx(tmp_path)
        elif suffix == ".pdf":
            pairs = extract_from_pdf(tmp_path)
        else:
            st.error(f"Unsupported file format: {suffix}")
            return []

        return [
            {
                "japanese": p.japanese,
                "vietnamese": p.vietnamese,
                "source_info": {
                    "file": uploaded_file.name,
                    "slide": getattr(p, "slide_number", None),
                    "page": getattr(p, "page_number", None)
                }
            }
            for p in pairs
        ]
    finally:
        tmp_path.unlink()


def run_evaluation(references, hypotheses, source_infos=None):
    """Run evaluation on text pairs"""
    comparator = TextComparator()
    results = []

    for i, (ref, hyp) in enumerate(zip(references, hypotheses)):
        info = source_infos[i] if source_infos else {"item": i + 1}
        result = comparator.compare(ref, hyp, info)
        results.append(result)

    summary = comparator.summarize(results)
    return results, summary


def display_metrics(summary):
    """Display evaluation metrics"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Accuracy",
            value=f"{summary['avg_accuracy']:.1f}%",
            delta=None
        )

    with col2:
        st.metric(
            label="WER",
            value=f"{summary['avg_wer']:.2%}",
            delta=None,
            delta_color="inverse"
        )

    with col3:
        st.metric(
            label="CER",
            value=f"{summary['avg_cer']:.2%}",
            delta=None,
            delta_color="inverse"
        )

    with col4:
        st.metric(
            label="Errors",
            value=summary['total_errors'],
            delta=None,
            delta_color="inverse"
        )


def display_comparison_metrics(before_summary, after_summary):
    """Display comparison metrics"""
    col1, col2, col3, col4 = st.columns(4)

    acc_diff = after_summary['avg_accuracy'] - before_summary['avg_accuracy']
    wer_diff = before_summary['avg_wer'] - after_summary['avg_wer']
    cer_diff = before_summary['avg_cer'] - after_summary['avg_cer']
    err_diff = before_summary['total_errors'] - after_summary['total_errors']

    with col1:
        st.metric(
            label="Accuracy",
            value=f"{after_summary['avg_accuracy']:.1f}%",
            delta=f"+{acc_diff:.1f}%" if acc_diff >= 0 else f"{acc_diff:.1f}%"
        )

    with col2:
        st.metric(
            label="WER",
            value=f"{after_summary['avg_wer']:.2%}",
            delta=f"-{wer_diff:.2%}" if wer_diff >= 0 else f"+{abs(wer_diff):.2%}",
            delta_color="normal" if wer_diff >= 0 else "inverse"
        )

    with col3:
        st.metric(
            label="CER",
            value=f"{after_summary['avg_cer']:.2%}",
            delta=f"-{cer_diff:.2%}" if cer_diff >= 0 else f"+{abs(cer_diff):.2%}",
            delta_color="normal" if cer_diff >= 0 else "inverse"
        )

    with col4:
        st.metric(
            label="Errors",
            value=after_summary['total_errors'],
            delta=f"-{err_diff}" if err_diff >= 0 else f"+{abs(err_diff)}",
            delta_color="normal" if err_diff >= 0 else "inverse"
        )


def display_error_table(results):
    """Display error details table"""
    error_data = []
    for i, result in enumerate(results):
        if result.errors:
            error_data.append({
                "No.": i + 1,
                "Reference": result.reference[:50] + "..." if len(result.reference) > 50 else result.reference,
                "Hypothesis": result.hypothesis[:50] + "..." if len(result.hypothesis) > 50 else result.hypothesis,
                "Accuracy": f"{result.accuracy:.1f}%",
                "Error Types": ", ".join(set(e.error_type for e in result.errors[:3]))
            })

    if error_data:
        df = pd.DataFrame(error_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.success("No errors found!")


def main():
    init_session_state()

    st.title("🔤 Translation Accuracy Test Tool")
    st.markdown("Felo Subtitles translation accuracy verification tool")

    # Sidebar
    with st.sidebar:
        st.header("Settings")

        mode = st.radio(
            "Mode",
            ["Single Test", "Before/After Comparison", "Manual Input"],
            format_func=lambda x: "Multi-File Test" if x == "Single Test" else x,
            help="Select test mode"
        )

        st.divider()

        st.subheader("API Settings")
        felo_endpoint = st.text_input("Felo API Endpoint", value="", type="password")
        felo_key = st.text_input("Felo API Key", value="", type="password")

        if not felo_endpoint or not felo_key:
            st.warning("API not configured. Running in mock mode.")

    # Main content
    if mode == "Manual Input":
        st.header("Manual Input Test")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Reference (Japanese)")
            reference_text = st.text_area(
                "Enter reference text (one per line)",
                height=200,
                placeholder="ヘルメットを着用してください\n安全帯を必ず装着すること"
            )

        with col2:
            st.subheader("Hypothesis (Translated)")
            hypothesis_text = st.text_area(
                "Enter translated text (one per line)",
                height=200,
                placeholder="ヘルメットを着用して下さい\n安全体を必ず装着すること"
            )

        if st.button("Evaluate", type="primary"):
            if reference_text and hypothesis_text:
                refs = [line.strip() for line in reference_text.split("\n") if line.strip()]
                hyps = [line.strip() for line in hypothesis_text.split("\n") if line.strip()]

                if len(refs) != len(hyps):
                    st.error(f"Line count mismatch: Reference={len(refs)}, Hypothesis={len(hyps)}")
                else:
                    with st.spinner("Evaluating..."):
                        results, summary = run_evaluation(refs, hyps)
                        st.session_state.test_results = results
                        st.session_state.summary = summary
            else:
                st.warning("Please enter both reference and hypothesis texts.")

    elif mode == "Single Test":
        st.header("Multi-File Test")

        uploaded_files = st.file_uploader(
            "Upload bilingual files (PPTX/PDF)",
            type=["pptx", "pdf"],
            accept_multiple_files=True,
            help="Upload one or more files containing Japanese-Vietnamese bilingual content"
        )

        if uploaded_files:
            all_pairs = []
            file_stats = []

            with st.spinner("Extracting text from files..."):
                progress_bar = st.progress(0)
                for idx, uploaded_file in enumerate(uploaded_files):
                    pairs = extract_text_from_file(uploaded_file)
                    all_pairs.extend(pairs)
                    file_stats.append({"file": uploaded_file.name, "pairs": len(pairs)})
                    progress_bar.progress((idx + 1) / len(uploaded_files))

            if all_pairs:
                # Show file statistics
                st.success(f"Extracted {len(all_pairs)} text pairs from {len(uploaded_files)} files")

                # File breakdown table
                st.subheader("File Summary")
                stats_df = pd.DataFrame(file_stats)
                st.dataframe(stats_df, use_container_width=True)

                # Show extracted pairs
                with st.expander("View Extracted Text Pairs"):
                    for i, pair in enumerate(all_pairs):
                        file_name = pair['source_info'].get('file', 'Unknown')
                        st.markdown(f"**{i+1}.** [{file_name}] JA: {pair['japanese'][:40]}... / VI: {pair['vietnamese'][:40]}...")

                if st.button("Run Test", type="primary"):
                    with st.spinner("Running test pipeline..."):
                        # For demo, use mock translations
                        refs = [p["japanese"] for p in all_pairs]
                        hyps = [f"[Mock] {p['vietnamese'][:20]}" for p in all_pairs]
                        infos = [p["source_info"] for p in all_pairs]

                        results, summary = run_evaluation(refs, hyps, infos)
                        st.session_state.test_results = results
                        st.session_state.summary = summary
            else:
                st.warning("No text pairs could be extracted from the uploaded files.")

    elif mode == "Before/After Comparison":
        st.header("Dictionary Before/After Comparison")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Before Dictionary")
            before_file = st.file_uploader(
                "Upload 'Before' results (JSON)",
                type=["json"],
                key="before_file"
            )

        with col2:
            st.subheader("After Dictionary")
            after_file = st.file_uploader(
                "Upload 'After' results (JSON)",
                type=["json"],
                key="after_file"
            )

        # Demo button
        if st.button("Run Demo Comparison", type="secondary"):
            # Use demo data
            st.session_state.before_summary = {
                "total_items": 16,
                "avg_accuracy": 91.4,
                "avg_wer": 0.75,
                "avg_cer": 0.0858,
                "avg_bleu": 0.0,
                "total_errors": 14,
                "error_breakdown": {"Same Sound Different Char": 10, "Deletion": 3, "Insertion": 1}
            }
            st.session_state.after_summary = {
                "total_items": 16,
                "avg_accuracy": 100.0,
                "avg_wer": 0.0,
                "avg_cer": 0.0,
                "avg_bleu": 0.0,
                "total_errors": 0,
                "error_breakdown": {}
            }

    # Display Results
    st.divider()

    if mode == "Before/After Comparison" and st.session_state.before_summary and st.session_state.after_summary:
        st.header("📊 Comparison Results")
        display_comparison_metrics(st.session_state.before_summary, st.session_state.after_summary)

        # Comparison chart
        st.subheader("Accuracy Comparison")
        chart_data = pd.DataFrame({
            "Stage": ["Before", "After"],
            "Accuracy (%)": [
                st.session_state.before_summary['avg_accuracy'],
                st.session_state.after_summary['avg_accuracy']
            ]
        })
        st.bar_chart(chart_data.set_index("Stage"))

        # Error breakdown
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Before - Error Breakdown")
            if st.session_state.before_summary['error_breakdown']:
                st.json(st.session_state.before_summary['error_breakdown'])
            else:
                st.info("No errors")

        with col2:
            st.subheader("After - Error Breakdown")
            if st.session_state.after_summary['error_breakdown']:
                st.json(st.session_state.after_summary['error_breakdown'])
            else:
                st.success("No errors!")

    elif st.session_state.summary:
        st.header("📊 Test Results")
        display_metrics(st.session_state.summary)

        if st.session_state.test_results:
            st.subheader("Error Details")
            display_error_table(st.session_state.test_results)

            # Error breakdown chart
            if st.session_state.summary['error_breakdown']:
                st.subheader("Error Type Distribution")
                error_df = pd.DataFrame(
                    list(st.session_state.summary['error_breakdown'].items()),
                    columns=['Error Type', 'Count']
                )
                st.bar_chart(error_df.set_index('Error Type'))

    # Footer
    st.divider()
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Translation Accuracy Test Tool v1.0 | Powered by Streamlit"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
