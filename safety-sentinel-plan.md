# SafetySentinel — Implementation & Testing Plan

## Top-Level Overview

**Goal:** Bring both P2 workflows (Signal Detection and Submission Readiness) to a fully
working, demo-ready state. The core statistical and checklist logic already exists in first-draft
form; this plan focuses on the gaps, quality issues, and the test harness that will verify the
implementation before the hackathon submission.

**Scope**
- Fix the one critical correctness bug in `signal_detector.py` (wrong PRR denominator formula).
- Harden both engine modules with input validation and edge-case handling.
- Enrich demo data so that every meaningful code path is exercised in the live demo.
- Add a `src/tests/` directory with pytest unit tests for both engines.
- Polish the Streamlit UI (column explanations, better metrics, evidence detail expander).
- Ensure the GitHub Actions CI pipeline installs test dependencies and runs the tests.
- Fill in the remaining `submission.yaml` placeholder values and README placeholders.

**Non-goals**
- No external database or live API integrations.
- No production auth, GxP validation, or deployment.
- No LLM calls from inside the app.

**Approach:** Each sub-task is self-contained and can be reviewed in isolation. Implement
them in order because later tasks depend on the stable core produced by earlier ones.

---

## Sub-Task 1 — Fix the PRR formula and harden signal_detector.py

**Status:** `[x] done`

**Intent**
The current implementation computes PRR as `(a/(a+b)) / (c/(c+d))`.  This is correct only when
`a+b` and `c+d` are both non-zero, but the guard already handles that.  However there is a subtle
issue: pairs where `c == 0` produce `nan` PRR and are silently skipped, yet the triage reason
message does not distinguish "no exposure" from "does not meet threshold".  More importantly,
the chi-square call wraps `[[a,b],[c,d]]`; when either row sums to zero the
`chi2_contingency` raises or returns a degenerate result. We must tighten the guard and ensure
the returned DataFrame always has a predictable, non-nan-or-inf set of values for rows where
the calculation is valid.

**Expected Outcomes**
- PRR and chi-square are `NaN` only when mathematically undefined (a=0 or c=0 or a+b=0 or c+d=0).
- Rows with valid counts always have numeric PRR and chi-square values.
- The `triage_reason` column carries one of three explicit messages:
  - `"Candidate signal — meets PRR/case-count/chi-square screen"`
  - `"Insufficient exposure (c=0 or a=0)"`
  - `"Below threshold"`
- All existing demo-data rows that currently produce a flagged signal still produce one.

**Todo List**
1. In `signal_detector.py`, tighten the NaN guard to also cover the case where `a+b == 0`.
2. Add a third triage reason literal for the "insufficient exposure" case (a==0 or c==0).
3. Verify the chi-square call always receives a valid 2×2 table before calling scipy.
4. Confirm the sort order: `signal_flag DESC`, `prr DESC`, `cases_a DESC`.
5. Add a docstring describing the 2×2 table layout for reviewers.

**Relevant Context**
- [`src/signal_detector.py`](src/signal_detector.py:9) — `calculate_signal_table`
- `a/(a+b)` is the exposure-adjusted proportion for the target drug.
- `c/(c+d)` is the background proportion across all other drugs.

---

## Sub-Task 2 — Enrich demo_data.py for full coverage

**Status:** `[x] done`

**Intent**
The current `demo_events()` has only 3 drugs and 3 events with 205 rows.  That is enough to show
the happy path but:
- No pair currently triggers the "insufficient exposure" path (c=0).
- There is no pair near the threshold that a reviewer might want to investigate.
- `demo_ctd()` is missing deliberate gaps in every module so the gap report is meaningful.

**Expected Outcomes**
- `demo_events()` produces at least 5 drugs × 4 events covering:
  - At least 2 clearly flagged pairs (PRR ≥ 2, chi2 ≥ 4, a ≥ 3).
  - At least 1 pair below threshold for contrast.
  - At least 1 drug with rare-event exposure (a≥1 but c=0) showing "Insufficient exposure".
- `demo_ctd()` is missing at least one section per module so every module shows a gap.

**Todo List**
1. Add two more drugs (`DrugD`, `DrugE`) and one more event (`Arrhythmia`) to `demo_events()`.
2. Keep totals manageable (< 400 rows) so the UI table renders quickly.
3. In `demo_ctd()`, remove `1.3 Product Information` (Module 1), `2.5 Clinical Overview` (Module 2),
   `3.2.P Drug Product` (Module 3), `4.2.2 Pharmacokinetics` + `4.2.3 Toxicology` (Module 4), and
   `5.3 Clinical Study Reports` (Module 5) so each module has at least one visible gap.
4. Do not change function signatures (callers in `app.py` import them directly).

**Relevant Context**
- [`src/demo_data.py`](src/demo_data.py:1)
- [`src/app.py`](src/app.py:24) — `demo_events()` and `demo_ctd()` are called directly.

---

## Sub-Task 3 — Harden ctd_checker.py

**Status:** `[x] done`

**Intent**
The matching in `check_ctd` lower-cases the submitted section but compares against
`section.lower()` of the required list.  The module key, however, is compared without
normalization — so `"module 1"` (lowercase) in the uploaded CSV would silently appear as all
missing because it never matches `"Module 1"`.  We must normalize both sides of the module
comparison.  Also, the `present` set currently stores the raw `r.module` string without
lower-casing, which is inconsistent.

**Expected Outcomes**
- Module matching is case-insensitive and strip-normalized for both the uploaded CSV and the
  required dictionary keys.
- Section matching is case-insensitive and strip-normalized (already partially done).
- A CSV with `module 1` (lowercase) produces the same result as `Module 1`.
- `check_ctd` raises `ValueError` for empty DataFrames or missing required columns.

**Todo List**
1. In `check_ctd`, normalize `r.module` with `.strip().lower()` before building the `present` set.
2. Normalize the required dictionary keys when building lookup keys (convert `"Module 1"` →
   `"module 1"` for comparison purposes, keeping the display label unchanged).
3. Add an empty-DataFrame guard: raise `ValueError("No data rows found.")` if `df` is empty.
4. Keep the `REQUIRED` dict as-is (it is the authoritative display label).

**Relevant Context**
- [`src/ctd_checker.py`](src/ctd_checker.py:38) — `check_ctd`

---

## Sub-Task 4 — Add pytest test suite (src/tests/)

**Status:** `[x] done`

**Intent**
A hackathon submission without tests cannot demonstrate that the core logic is correct.  The
tests should be minimal but meaningful — they must verify the numerical outputs, the edge cases,
and the validation errors rather than just checking that the functions run without crashing.

**Expected Outcomes**
- `src/tests/test_signal_detector.py` covers:
  - Known-value PRR calculation (hand-computed expected value).
  - `signal_flag=True` when all three thresholds are met.
  - `signal_flag=False` when PRR is below threshold.
  - `ValueError` on missing columns.
  - `ValueError` on empty DataFrame.
  - Pairs where a=0 or c=0 produce `NaN` PRR (not a crash).
- `src/tests/test_ctd_checker.py` covers:
  - All-present input → 100 % completeness, no missing rows.
  - All-missing input → 0 % completeness, all rows missing.
  - Partial input (demo_ctd) → expected per-module scores.
  - Case-insensitive module matching.
  - Case-insensitive section matching.
  - `ValueError` on missing columns.
  - `ValueError` on empty DataFrame.
- `src/tests/__init__.py` exists (empty) so pytest discovers the package.
- `src/tests/conftest.py` adds `src/` to `sys.path` so absolute imports work.

**Todo List**
1. Create `src/tests/__init__.py` (empty).
2. Create `src/tests/conftest.py` that prepends `src/` to `sys.path`.
3. Create `src/tests/test_signal_detector.py` with the cases listed above.
4. Create `src/tests/test_ctd_checker.py` with the cases listed above.
5. Verify tests pass locally: `pytest src/tests/ -v`.

**Relevant Context**
- [`src/signal_detector.py`](src/signal_detector.py:9) — function under test.
- [`src/ctd_checker.py`](src/ctd_checker.py:38) — function under test.
- [`src/demo_data.py`](src/demo_data.py:1) — reuse helpers in tests.

---

## Sub-Task 5 — Update CI to run tests

**Status:** `[x] done`

**Intent**
The GitHub Actions workflow currently only validates the repo structure and `submission.yaml`.
It does not install the app dependencies or run the test suite.  Adding a second job that installs
`requirements.txt` + pytest and runs `pytest src/tests/ -v` gives continuous verification.

**Expected Outcomes**
- The `validate.yml` workflow has a second job `test` that:
  - Installs Python 3.11.
  - Installs `src/requirements.txt` and `pytest`.
  - Runs `pytest src/tests/ -v`.
  - Fails the build if any test fails.
- The existing `validate` job is unchanged.

**Todo List**
1. In `.github/workflows/validate.yml`, add a `test` job after the `validate` job.
2. The `test` job installs `pip install pytest -r src/requirements.txt`.
3. The `test` job runs `pytest src/tests/ -v --tb=short`.

**Relevant Context**
- [`.github/workflows/validate.yml`](.github/workflows/validate.yml:1)

---

## Sub-Task 6 — Polish the Streamlit UI

**Status:** `[x] done`

**Intent**
The UI works end-to-end but lacks explanatory context that helps a hackathon judge understand
what they are looking at without reading the docs.  Key gaps:
- Column headers in the signal table have terse names (`cases_a`, `drug_other_events_b`, …).
- No inline explanation of what PRR means or what the 2×2 counts represent.
- No per-signal expandable detail view.
- The CTD mode shows the gap report but does not highlight per-module completion percentages
  visually.

**Expected Outcomes**
- Signal Detection page:
  - An expander "How to read this table" explains a, b, c, d, PRR, chi-square, and the flag.
  - The `signal_flag` column is rendered as ✅ / ⬜ rather than `True`/`False`.
  - Metrics show total drugs and total events screened in addition to candidate signals.
- Submission Readiness page:
  - Module scores table shows a simple bar made of █ characters proportional to completeness %.
  - Missing sections are highlighted (red background via `st.dataframe` + a Styler).
  - Overall completeness shown as a large metric with colour (green ≥ 80 %, amber 50–79 %, red < 50 %).

**Todo List**
1. In `app.py` Signal Detection section, add a `st.expander` with a 2×2 table explanation.
2. Map `signal_flag` boolean to emoji string before passing to `st.dataframe`.
3. Add two more `st.metric` calls: total drugs and total events.
4. In the Submission Readiness section, add a `bar` column to the scores DataFrame.
5. Add `st.metric` colour via `delta` parameter based on completeness bracket.
6. Style the gap report `st.dataframe` to highlight missing rows.

**Relevant Context**
- [`src/app.py`](src/app.py:1)
- Streamlit `st.dataframe` accepts a pandas Styler.
- `st.metric` accepts a `delta` / `delta_color` to show green/red.

---

## Sub-Task 7 — Fill submission.yaml and README placeholders

**Status:** `[x] done`

**Intent**
The CI workflow warns when `README.md` contains `YOUR_` or `[` placeholders.  The
`submission.yaml` still has `YOUR TEAM NAME`, `YOUR_EMAIL`, etc.  These must be filled with the
actual information before final submission or the validator will warn.

**Expected Outcomes**
- `submission.yaml` has a real team name, lead email, and at least one member entry (even if
  placeholder values are acceptable for the hackathon demo — but the format must be valid YAML
  with no `YOUR_` literals).
- `README.md` has no `YOUR_` literals in the team section.
- `demo/demo-video-link.txt` and `demo/live-demo-url.txt` reference the actual artifacts or note
  "NOT RECORDED YET" as directed by the hackathon guide.

**Confirmed team details (from user):**
- Team name: `Janvi Patel`
- Lead: Janvi Patel — `23bph050@charusat.edu.in`
- Members: Priyanshi Thakkar, Devanshi Pandit, Divyraje Dabhi

**Todo List**
1. Update `submission.yaml`: team name → `"Janvi Patel"`, lead email → `"23bph050@charusat.edu.in"`, members → Priyanshi Thakkar, Devanshi Pandit, Divyraje Dabhi.
2. Update `README.md` team section to use the real names above and remove `YOUR_EMAIL` / `YOUR MEMBER 2`.
3. Check `demo/demo-video-link.txt` and `demo/live-demo-url.txt` for content.

**Relevant Context**
- [`submission.yaml`](submission.yaml:1)
- [`README.md`](README.md:1)
- [`.github/workflows/validate.yml`](.github/workflows/validate.yml:26) — the line that checks for `YOUR_`.

---

## Sub-Task 8 — End-to-end smoke test and demo validation

**Status:** `[x] done`

**Intent**
Verify that the full demo script in `docs/demo-script.md` works top to bottom from a clean state:
load demo data → run detection → download CSV; load demo CTD → check readiness → download gap
report.  This is not an automated test — it is a manual checklist run before the submission
video recording.

**Expected Outcomes**
- `streamlit run src/app.py` starts without errors.
- Signal Detection with demo data produces ≥ 2 flagged rows with non-NaN PRR.
- The downloaded CSV contains all expected columns.
- Submission Readiness with demo CTD produces per-module scores, overall completeness, and a
  gap report with at least one missing section per module.
- The downloaded gap report CSV is non-empty.
- No Python tracebacks appear in the Streamlit UI.

**Todo List**
1. Run `pip install -r src/requirements.txt` in a clean venv.
2. Run `streamlit run src/app.py`.
3. Walk through the demo script step by step.
4. Record any failures and return to the relevant sub-task to fix them.
5. Update `demo/demo-video-link.txt` with the recording URL once captured.

**Relevant Context**
- [`docs/demo-script.md`](docs/demo-script.md:1)
- [`docs/setup-guide.md`](docs/setup-guide.md:1)

---

## Execution Order

Sub-tasks are designed to be implemented in order:

```
1 (Fix signal_detector) → 2 (Enrich demo_data) → 3 (Harden ctd_checker)
    → 4 (Add tests) → 5 (Update CI) → 6 (Polish UI) → 7 (Fill placeholders)
        → 8 (Smoke test)
```

Sub-tasks 1–3 are core correctness; sub-tasks 4–5 are verification; sub-tasks 6–7 are
presentation; sub-task 8 is final validation.
