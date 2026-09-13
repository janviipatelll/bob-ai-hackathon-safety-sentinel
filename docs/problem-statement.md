# Problem Statement

## P2 — Drug Safety Signal Detector & Regulatory Submission Readiness Checker

### Who is affected?
- Pharmacovigilance reviewers handling adverse-event reports.
- Safety scientists who need to prioritize drug-event combinations for deeper review.
- Regulatory operations teams preparing CTD dossiers.
- Submission teams who need an early completeness check before formal review.

### Why the problem matters
The challenge statement highlights two high-volume review problems: the FAERS database contains 20M+ adverse-event reports, while a drug approval CTD dossier can span 100,000+ pages. It notes that Vioxx had 27,000+ heart attacks before its signal was acted on, and that a missing CTD section can cause major submission delays.

### What is difficult about the current workflow?
Reviewers need to transform large, heterogeneous records into a smaller set of actionable items. A safety signal requires statistical screening and human assessment; dossier readiness requires checking many sections across multiple CTD modules.

### Our interpretation
SafetySentinel does not replace expert review. It reduces the first-pass workload by:
1. aggregating event reports into drug-event pairs;
2. calculating PRR from transparent 2x2 counts;
3. ranking candidate signals using configurable heuristic indicators; and
4. checking a submitted CTD outline against a structured module checklist.

This preserves human oversight while making the first-pass evidence easier to inspect.
