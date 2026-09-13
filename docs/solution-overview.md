# Solution Overview

## Two-mode reviewer copilot

### Mode 1 — Signal Detection
Input: adverse-event records with at least `drug` and `event` columns.

Pipeline:
1. Normalize text.
2. Build counts for each drug-event pair:
   - a = target drug + target event
   - b = target drug + other events
   - c = other drugs + target event
   - d = other drugs + other events
3. Calculate:
   `PRR = [a/(a+b)] / [c/(c+d)]`
4. Calculate a chi-square association statistic.
5. Apply a transparent prototype triage rule and rank candidate signals.
6. Display the evidence behind each flag.

### Mode 2 — Submission Readiness
Input: a CTD outline represented as module/section records.

Pipeline:
1. Normalize module and section names.
2. Compare submitted sections with the required prototype checklist.
3. Calculate completeness per module.
4. List missing sections and priorities.
5. Produce an overall readiness score and downloadable gap report.

## Why this is different
A naive dashboard could return only a score. SafetySentinel exposes the evidence behind the score, allowing a reviewer to inspect the exact counts and missing sections.

## Key design decisions
- **Transparent statistics:** PRR inputs are displayed rather than hidden.
- **Deterministic core:** the prototype can run without an external model or API key.
- **Human-in-the-loop:** outputs are framed as screening and readiness assistance.
- **Offline demo:** synthetic datasets make judging reproducible.
