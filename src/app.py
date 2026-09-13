"""app.py — SafetySentinel Streamlit UI.

Two workflow modes:
  1. Signal Detection  — loads adverse-event data, runs PRR-based screening,
     shows a prioritised candidate-signal table with transparent 2×2 counts.
  2. Submission Readiness — loads a CTD outline, checks it against the prototype
     ICH M4 required-section checklist, and produces a module-level gap report.
"""
import io
import math

import pandas as pd
import streamlit as st

from signal_detector import calculate_signal_table
from ctd_checker import check_ctd
from demo_data import demo_events, demo_ctd

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="SafetySentinel", page_icon="🛡️", layout="wide")
st.title("🛡️ SafetySentinel")
st.caption(
    "Drug Safety Signal Detector & Regulatory Submission Readiness Checker — P2 prototype  \n"
    "⚠️ Prototype only — outputs require expert pharmacovigilance / regulatory review."
)

mode = st.sidebar.radio("Choose workflow", ["Signal Detection", "Submission Readiness"])

# ---------------------------------------------------------------------------
# ── Mode 1: Signal Detection ─────────────────────────────────────────────
# ---------------------------------------------------------------------------
if mode == "Signal Detection":
    st.header("1. Drug Safety Signal Detection")
    st.write(
        "Upload a CSV with `drug` and `event` columns, or use the synthetic demo dataset.  "
        "The engine builds a 2×2 contingency table for every drug-event pair, calculates PRR "
        "and chi-square, and flags candidate signals using the configurable thresholds below."
    )

    with st.expander("ℹ️ How to read the signal table"):
        st.markdown(
            """
**2×2 contingency table for a drug-event pair:**

|  | Target event | Other events |
|---|---|---|
| **Target drug** | **a** (cases) | b |
| **Other drugs** | c | d |

| Column | Meaning |
|---|---|
| `cases_a` | Reports of *this drug* AND *this event* |
| `drug_other_events_b` | Reports of *this drug* AND *other events* |
| `other_drugs_event_c` | Reports of *other drugs* AND *this event* |
| `other_drugs_other_events_d` | Reports of *other drugs* AND *other events* |
| `prr` | Proportional Reporting Ratio = [a/(a+b)] ÷ [c/(c+d)] — values > 1 suggest disproportionate reporting |
| `chi_square` | Association statistic from the 2×2 table (no Yates' correction) |
| `signal_flag` | ✅ if a ≥ min_cases AND PRR ≥ threshold AND chi² ≥ threshold |

**PRR is an association measure, not proof of causality.  All flagged pairs require expert review.**
"""
        )

    upload = st.file_uploader("Adverse-event CSV", type=["csv"])
    if "events" not in st.session_state:
        st.session_state.events = None

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Load demo data"):
            st.session_state.events = demo_events()
            # Clear previous result when new data is loaded
            st.session_state.pop("signal_result", None)
    with c2:
        if upload:
            st.session_state.events = pd.read_csv(upload)
            st.session_state.pop("signal_result", None)

    if st.session_state.events is not None:
        df_events = st.session_state.events
        n_drugs = df_events["drug"].nunique() if "drug" in df_events.columns else "—"
        n_events = df_events["event"].nunique() if "event" in df_events.columns else "—"
        m1, m2, m3 = st.columns(3)
        m1.metric("Total reports", len(df_events))
        m2.metric("Unique drugs", n_drugs)
        m3.metric("Unique events", n_events)
        st.dataframe(df_events.head(20), use_container_width=True)

        st.subheader("Detection thresholds")
        t1, t2, t3 = st.columns(3)
        with t1:
            min_cases = st.number_input("Minimum cases (a)", min_value=1, value=3)
        with t2:
            prr_threshold = st.number_input("PRR threshold", min_value=0.1, value=2.0, step=0.1)
        with t3:
            chi2_threshold = st.number_input("Chi-square threshold", min_value=0.0, value=4.0, step=0.5)

        if st.button("Run signal detection", type="primary"):
            try:
                result = calculate_signal_table(
                    df_events, int(min_cases), float(prr_threshold), float(chi2_threshold)
                )
                st.session_state.signal_result = result
            except Exception as e:
                st.error(str(e))

    if "signal_result" in st.session_state:
        result = st.session_state.signal_result
        flagged = result[result.signal_flag]

        r1, r2, r3 = st.columns(3)
        r1.metric("Drug-event pairs screened", int(len(result)))
        r2.metric("Candidate signals", int(len(flagged)))
        r3.metric(
            "Signal rate",
            f"{round(len(flagged)/len(result)*100, 1)}%" if len(result) else "—",
        )

        # Render signal_flag as emoji for readability
        display = result.copy()
        display["signal_flag"] = display["signal_flag"].map({True: "✅", False: "⬜"})

        st.subheader("Prioritised signals (flagged first)")
        show_df = flagged if not flagged.empty else result.head(20)
        show_display = display.loc[show_df.index]
        st.dataframe(show_display, use_container_width=True)

        if flagged.empty:
            st.info("No pairs met all three thresholds with the current settings. Showing top 20 rows.")
        else:
            st.success(
                f"{len(flagged)} candidate signal(s) flagged. "
                "These are prototype screening results only — expert review is required."
            )

        with st.expander("Show full screening table (all pairs)"):
            st.dataframe(display, use_container_width=True)

        st.download_button(
            "⬇️ Download full signal report (CSV)",
            result.to_csv(index=False),
            "safety_signal_report.csv",
            "text/csv",
        )

# ---------------------------------------------------------------------------
# ── Mode 2: Submission Readiness ─────────────────────────────────────────
# ---------------------------------------------------------------------------
else:
    st.header("2. Regulatory Submission Readiness")
    st.write(
        "Upload a CTD outline CSV with `module` and `section` columns, or use the synthetic "
        "demo outline.  The checker compares submitted sections against the prototype ICH M4 "
        "required-section checklist and produces a module-level completeness score and gap report."
    )

    with st.expander("ℹ️ About the CTD checklist"):
        st.markdown(
            """
**ICH M4 module structure (prototype)**

| Module | Contents |
|---|---|
| Module 1 | Regional administrative information |
| Module 2 | Summaries and overviews |
| Module 3 | Quality (chemistry, manufacturing, controls) |
| Module 4 | Nonclinical study reports |
| Module 5 | Clinical study reports |

The checklist is a **prototype** inspired by ICH M4 — it is not a complete regulatory validation engine.
Section matching is case-insensitive.  Upload a CSV with columns `module` and `section`.
"""
        )

    upload = st.file_uploader("CTD outline CSV", type=["csv"], key="ctd_upload")
    if "ctd_data" not in st.session_state:
        st.session_state.ctd_data = None

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Load demo CTD outline"):
            st.session_state.ctd_data = demo_ctd()
            st.session_state.pop("ctd_scores", None)
    with c2:
        if upload:
            st.session_state.ctd_data = pd.read_csv(upload)
            st.session_state.pop("ctd_scores", None)

    if st.session_state.ctd_data is not None:
        st.dataframe(st.session_state.ctd_data, use_container_width=True)
        if st.button("Check readiness", type="primary"):
            try:
                scores, details, overall = check_ctd(st.session_state.ctd_data)
                st.session_state.ctd_scores = scores
                st.session_state.ctd_details = details
                st.session_state.ctd_overall = overall
            except Exception as e:
                st.error(str(e))

    if "ctd_scores" in st.session_state:
        overall = st.session_state.ctd_overall

        # Colour the overall metric via delta trick
        if overall >= 80:
            delta_str, delta_color = "Good", "normal"
        elif overall >= 50:
            delta_str, delta_color = "Needs attention", "off"
        else:
            delta_str, delta_color = "Critical gaps", "inverse"

        st.metric(
            "Overall prototype completeness",
            f"{overall}%",
            delta=delta_str,
            delta_color=delta_color,
        )

        # Module scores with a simple ASCII progress bar
        scores_display = st.session_state.ctd_scores.copy()
        scores_display["progress"] = scores_display["completeness_pct"].apply(
            lambda p: "█" * int(p // 10) + "░" * (10 - int(p // 10))
        )
        st.subheader("Module completeness scores")
        st.dataframe(
            scores_display[["module", "required_sections", "present", "missing", "completeness_pct", "progress"]],
            use_container_width=True,
        )

        # Gap report — highlight missing rows
        details = st.session_state.ctd_details
        gaps = details[details.status == "Missing"].reset_index(drop=True)

        st.subheader("Gap report — missing sections")
        if gaps.empty:
            st.success("No missing sections — prototype checklist complete.")
        else:
            st.warning(f"{len(gaps)} missing section(s) identified.")
            # Style missing rows red
            def _highlight_missing(row):
                return ["background-color: #fde8e8; color: #7f0000"] * len(row)

            styled = gaps.style.apply(_highlight_missing, axis=1)
            st.dataframe(styled, use_container_width=True)

        with st.expander("Show full section status (present + missing)"):
            st.dataframe(details, use_container_width=True)

        st.download_button(
            "⬇️ Download CTD gap report (CSV)",
            gaps.to_csv(index=False),
            "ctd_gap_report.csv",
            "text/csv",
        )
