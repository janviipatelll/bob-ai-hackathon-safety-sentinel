"""signal_detector.py — Drug-event safety signal screening.

2×2 contingency table layout for a given (drug, event) pair:

                 | target event | other events |  row total
  ---------------+--------------+--------------+----------
  target drug    |      a       |      b       |   a + b
  other drugs    |      c       |      d       |   c + d
  ---------------+--------------+--------------+----------
  column total   |    a + c     |    b + d     |    N

PRR = [a / (a+b)] / [c / (c+d)]

Interpretation:
  PRR > 1  — the event is proportionally more common with the target drug.
  PRR ≥ 2 (prototype threshold) combined with ≥ 3 cases and chi-square ≥ 4
  triggers the candidate-signal flag.  These are configurable thresholds.

This module performs association screening only.  Flagged pairs require
expert pharmacovigilance review.  PRR is not proof of causality.
"""
from __future__ import annotations

import math

import pandas as pd
from scipy.stats import chi2_contingency


def _norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower()


# Human-readable triage reason literals (three distinct outcomes).
_REASON_SIGNAL = "Candidate signal — meets PRR/case-count/chi-square screen"
_REASON_INSUFFICIENT = "Insufficient exposure (a=0 or c=0)"
_REASON_BELOW = "Below prototype threshold"


def calculate_signal_table(
    df: pd.DataFrame,
    min_cases: int = 3,
    prr_threshold: float = 2.0,
    chi2_threshold: float = 4.0,
) -> pd.DataFrame:
    """Build a drug-event signal screening table.

    Parameters
    ----------
    df : DataFrame
        Must contain at least ``drug`` and ``event`` columns.
    min_cases : int
        Minimum value of *a* (target drug + target event count) required to
        flag a pair.
    prr_threshold : float
        Minimum PRR required to flag a pair.
    chi2_threshold : float
        Minimum chi-square statistic required to flag a pair.

    Returns
    -------
    DataFrame
        One row per (drug, event) pair, sorted by signal_flag DESC, prr DESC,
        cases_a DESC.  Columns: drug, event, cases_a, drug_other_events_b,
        other_drugs_event_c, other_drugs_other_events_d, prr, chi_square,
        signal_flag, triage_reason.
    """
    required = {"drug", "event"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")

    data = df[["drug", "event"]].dropna().copy()
    data["drug"] = _norm(data["drug"])
    data["event"] = _norm(data["event"])

    if data.empty:
        raise ValueError("No valid rows found after dropping nulls.")

    drugs = data["drug"].unique()
    events = data["event"].unique()
    rows = []

    for drug in drugs:
        for event in events:
            a = int(((data.drug == drug) & (data.event == event)).sum())
            b = int(((data.drug == drug) & (data.event != event)).sum())
            c = int(((data.drug != drug) & (data.event == event)).sum())
            d = int(((data.drug != drug) & (data.event != event)).sum())

            # PRR and chi-square are undefined when a=0, c=0, or either row
            # sums to zero (would cause a division-by-zero or degenerate table).
            if a == 0 or c == 0 or (a + b) == 0 or (c + d) == 0:
                prr = math.nan
                chi2 = math.nan
                triage = _REASON_INSUFFICIENT
            else:
                prr = (a / (a + b)) / (c / (c + d))
                try:
                    chi2 = float(
                        chi2_contingency([[a, b], [c, d]], correction=False)[0]
                    )
                except ValueError:
                    chi2 = math.nan

                flag_conditions = (
                    a >= min_cases
                    and not math.isnan(prr)
                    and prr >= prr_threshold
                    and not math.isnan(chi2)
                    and chi2 >= chi2_threshold
                )
                triage = _REASON_SIGNAL if flag_conditions else _REASON_BELOW

            flag = triage == _REASON_SIGNAL

            rows.append(
                {
                    "drug": drug,
                    "event": event,
                    "cases_a": a,
                    "drug_other_events_b": b,
                    "other_drugs_event_c": c,
                    "other_drugs_other_events_d": d,
                    "prr": round(prr, 4) if not math.isnan(prr) else prr,
                    "chi_square": round(chi2, 4) if not math.isnan(chi2) else chi2,
                    "signal_flag": flag,
                    "triage_reason": triage,
                }
            )

    out = pd.DataFrame(rows)
    return out.sort_values(
        ["signal_flag", "prr", "cases_a"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
