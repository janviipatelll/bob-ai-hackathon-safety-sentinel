"""demo_data.py — Synthetic demo datasets for SafetySentinel.

All data are entirely fictional.  Do NOT treat any values here as real
pharmacovigilance evidence.  They exist only to demonstrate the two
SafetySentinel workflows in a reproducible, offline setting.
"""
import pandas as pd


def demo_events() -> pd.DataFrame:
    """Return a synthetic adverse-event DataFrame with ``drug`` and ``event`` columns.

    Design decisions
    ----------------
    * 5 drugs × 4 events so the signal table exercises multiple scenarios.
    * DrugA/Hepatotoxicity: strong signal (high a, high PRR, high chi-square).
    * DrugB/Arrhythmia:     moderate signal (meets all three thresholds).
    * DrugC/Nausea:         below threshold (low PRR — event common across all drugs).
    * DrugD/Hepatotoxicity: near-threshold case (a ≥ 3 but PRR just below 2).
    * DrugE/Arrhythmia:     rare drug (a=2, below min_cases=3 threshold — shows below-threshold path).
    * No drug reports Dizziness except DrugA → c=0 for DrugB/C/D/E + Dizziness,
      which exercises the "Insufficient exposure" path.
    """
    rows = []

    # --- DrugA: hepatotoxicity signal + dizziness (unique to DrugA → c=0 for others) ---
    for _ in range(38): rows.append({"drug": "DrugA", "event": "Hepatotoxicity"})
    for _ in range(22): rows.append({"drug": "DrugA", "event": "Headache"})
    for _ in range(15): rows.append({"drug": "DrugA", "event": "Nausea"})
    for _ in range(12): rows.append({"drug": "DrugA", "event": "Dizziness"})   # only DrugA reports Dizziness
    for _ in range(3):  rows.append({"drug": "DrugA", "event": "Arrhythmia"})

    # --- DrugB: arrhythmia signal ---
    for _ in range(5):  rows.append({"drug": "DrugB", "event": "Hepatotoxicity"})
    for _ in range(30): rows.append({"drug": "DrugB", "event": "Headache"})
    for _ in range(20): rows.append({"drug": "DrugB", "event": "Nausea"})
    for _ in range(28): rows.append({"drug": "DrugB", "event": "Arrhythmia"})

    # --- DrugC: no strong signal (headache/nausea distributed evenly) ---
    for _ in range(4):  rows.append({"drug": "DrugC", "event": "Hepatotoxicity"})
    for _ in range(45): rows.append({"drug": "DrugC", "event": "Headache"})
    for _ in range(35): rows.append({"drug": "DrugC", "event": "Nausea"})
    for _ in range(3):  rows.append({"drug": "DrugC", "event": "Arrhythmia"})

    # --- DrugD: near-threshold hepatotoxicity (a=5 but PRR ~ 1.3, below 2.0) ---
    for _ in range(5):  rows.append({"drug": "DrugD", "event": "Hepatotoxicity"})
    for _ in range(18): rows.append({"drug": "DrugD", "event": "Headache"})
    for _ in range(14): rows.append({"drug": "DrugD", "event": "Nausea"})
    for _ in range(2):  rows.append({"drug": "DrugD", "event": "Arrhythmia"})

    # --- DrugE: rare drug with arrhythmia (a=2, below min_cases threshold) ---
    for _ in range(1):  rows.append({"drug": "DrugE", "event": "Hepatotoxicity"})
    for _ in range(4):  rows.append({"drug": "DrugE", "event": "Headache"})
    for _ in range(2):  rows.append({"drug": "DrugE", "event": "Arrhythmia"})

    return pd.DataFrame(rows)


def demo_ctd() -> pd.DataFrame:
    """Return a synthetic CTD outline with deliberate gaps in every module.

    Gaps introduced (one or more per module so the gap report is meaningful):
      Module 1 — missing: 1.3 Product Information
      Module 2 — missing: 2.5 Clinical Overview
      Module 3 — missing: 3.2.P Drug Product
      Module 4 — missing: 4.2.2 Pharmacokinetics, 4.2.3 Toxicology
      Module 5 — missing: 5.3 Clinical Study Reports
    """
    return pd.DataFrame([
        # Module 1 (2/3 present)
        {"module": "Module 1", "section": "1.1 Regional Administrative Information"},
        {"module": "Module 1", "section": "1.2 Application Form"},
        # 1.3 Product Information deliberately omitted

        # Module 2 (4/5 present)
        {"module": "Module 2", "section": "2.1 CTD Table of Contents"},
        {"module": "Module 2", "section": "2.2 CTD Introduction"},
        {"module": "Module 2", "section": "2.3 Quality Overall Summary"},
        {"module": "Module 2", "section": "2.4 Nonclinical Overview"},
        # 2.5 Clinical Overview deliberately omitted

        # Module 3 (3/4 present)
        {"module": "Module 3", "section": "3.1 Table of Contents"},
        {"module": "Module 3", "section": "3.2 Body of Data"},
        {"module": "Module 3", "section": "3.2.S Drug Substance"},
        # 3.2.P Drug Product deliberately omitted

        # Module 4 (3/5 present)
        {"module": "Module 4", "section": "4.1 Table of Contents"},
        {"module": "Module 4", "section": "4.2 Study Reports"},
        {"module": "Module 4", "section": "4.2.1 Pharmacology"},
        # 4.2.2 Pharmacokinetics deliberately omitted
        # 4.2.3 Toxicology deliberately omitted

        # Module 5 (3/4 present)
        {"module": "Module 5", "section": "5.1 Table of Contents"},
        {"module": "Module 5", "section": "5.2 Tabular Listing of All Clinical Studies"},
        # 5.3 Clinical Study Reports deliberately omitted
        {"module": "Module 5", "section": "5.4 Literature References"},
    ])
