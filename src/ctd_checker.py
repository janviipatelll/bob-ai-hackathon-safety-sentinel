"""ctd_checker.py — ICH M4-inspired CTD module completeness checker.

Compares a submitted CTD outline (module + section records) against the
prototype required-section checklist and returns per-module completeness
scores, a detailed status table, and an overall readiness percentage.

All matching is case-insensitive and strip-normalised so that minor
formatting differences in uploaded files do not cause false gaps.

This is a prototype checklist for demonstration purposes only.  It is not
a complete regulatory dossier validation engine.
"""
from __future__ import annotations

import pandas as pd


# ---------------------------------------------------------------------------
# Prototype required-section checklist (ICH M4 inspired).
# Keys are the canonical display labels; values are lists of section labels.
# ---------------------------------------------------------------------------
REQUIRED: dict[str, list[str]] = {
    "Module 1": [
        "1.1 Regional Administrative Information",
        "1.2 Application Form",
        "1.3 Product Information",
    ],
    "Module 2": [
        "2.1 CTD Table of Contents",
        "2.2 CTD Introduction",
        "2.3 Quality Overall Summary",
        "2.4 Nonclinical Overview",
        "2.5 Clinical Overview",
    ],
    "Module 3": [
        "3.1 Table of Contents",
        "3.2 Body of Data",
        "3.2.S Drug Substance",
        "3.2.P Drug Product",
    ],
    "Module 4": [
        "4.1 Table of Contents",
        "4.2 Study Reports",
        "4.2.1 Pharmacology",
        "4.2.2 Pharmacokinetics",
        "4.2.3 Toxicology",
    ],
    "Module 5": [
        "5.1 Table of Contents",
        "5.2 Tabular Listing of All Clinical Studies",
        "5.3 Clinical Study Reports",
        "5.4 Literature References",
    ],
}


def check_ctd(df: pd.DataFrame):
    """Check a submitted CTD outline against the prototype required-section checklist.

    Parameters
    ----------
    df : DataFrame
        Must contain at least ``module`` and ``section`` columns.  Both values
        are normalised (stripped, lower-cased) before comparison so that case
        differences in uploaded files do not produce false gaps.

    Returns
    -------
    scores : DataFrame
        One row per module with columns: module, required_sections, present,
        missing, completeness_pct.
    details : DataFrame
        One row per required section with columns: module, section, status
        ("Present" or "Missing").
    overall : float
        Overall completeness percentage across all modules.
    """
    required_cols = {"module", "section"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing_cols))}")

    if df.empty:
        raise ValueError("No data rows found.")

    # Build a set of (normalised_module, normalised_section) tuples from the
    # submitted outline.  Both sides are lower-cased and stripped.
    present: set[tuple[str, str]] = {
        (str(r.module).strip().lower(), str(r.section).strip().lower())
        for r in df.itertuples()
    }

    rows: list[dict] = []
    module_scores: list[dict] = []

    for module_label, sections in REQUIRED.items():
        module_key = module_label.lower()  # normalised key for lookup
        found = 0
        for section in sections:
            section_key = section.lower()
            ok = (module_key, section_key) in present
            found += int(ok)
            rows.append(
                {
                    "module": module_label,
                    "section": section,
                    "status": "Present" if ok else "Missing",
                }
            )
        module_scores.append(
            {
                "module": module_label,
                "required_sections": len(sections),
                "present": found,
                "missing": len(sections) - found,
                "completeness_pct": round(found / len(sections) * 100, 1),
            }
        )

    details = pd.DataFrame(rows)
    scores = pd.DataFrame(module_scores)
    total_required = scores["required_sections"].sum()
    total_present = scores["present"].sum()
    overall = round(total_present / total_required * 100, 1)
    return scores, details, overall
