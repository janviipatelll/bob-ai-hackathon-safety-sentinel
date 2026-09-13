# SafetySentinel — Drug Safety Signal & CTD Readiness Copilot

**Track:** AI  
**Problem:** P2 — Drug Safety Signal Detector & Regulatory Submission Readiness Checker

## Team
- **Lead:** Janvi Patel — `23bph050@charusat.edu.in`
- **Members:** Priyanshi Thakkar, Devanshi Pandit, Divyraje Dabhi

## Problem Statement
Pharmacovigilance teams must review large volumes of adverse-event reports to identify emerging drug-event patterns. Regulatory teams separately review very large CTD dossiers for missing or incomplete sections. SafetySentinel brings these two review-heavy workflows into one reproducible interface.

## Solution
SafetySentinel has two modes:
1. **Signal Detection:** reads an adverse-event dataset, aggregates drug-event counts, builds 2x2 tables, calculates PRR, and prioritizes potential signals.
2. **Submission Readiness:** accepts a CTD outline, checks it against an ICH M4-inspired required-section checklist, scores completeness per module, and produces a gap report.

The app is intentionally a decision-support prototype: it does not make clinical or regulatory decisions.

## Key Features
- PRR calculation with transparent numerator/denominator counts.
- Signal ranking and evidence table.
- Explainable rule-based triage indicators.
- CTD Modules 1–5 completeness dashboard.
- Missing-section gap report.
- CSV/JSON input and downloadable results.
- Demo datasets included for a reproducible offline demo.

## Tech Stack
- Python 3.11+
- Streamlit
- pandas
- scipy
- PyYAML

## How to Run
See [`docs/setup-guide.md`](docs/setup-guide.md).

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r src/requirements.txt
streamlit run src/app.py
```

## Demo
- Video: replace `demo/demo-video-link.txt` with your real 3–5 minute video.
- Live demo: replace `demo/live-demo-url.txt` or leave `NOT DEPLOYED`.
- Screenshots: add at least 3 screenshots to `demo/screenshots/`.

## IBM Bob Integration
Bob is used as the AI SDLC partner for planning, implementation, review, and terminal-driven testing. The reproducible workflow is documented in [`bob/README.md`](bob/README.md). The project keeps the analytical logic deterministic and inspectable while Bob assists the engineering workflow.

## Known Limitations
- The CTD checklist is a prototype checklist inspired by ICH M4; it is not a complete regulatory dossier validation engine.
- PRR is an association metric, not proof of causality.
- Demo data is synthetic and must not be treated as real pharmacovigilance evidence.
- No production database, validated GxP workflow, or regulatory submission system is included.

## What We're Most Proud Of
The strongest part of the project is the shared evidence-first design: every flagged signal exposes its underlying 2x2 counts and PRR, while every CTD gap identifies the missing module/section rather than returning only a single readiness score.
