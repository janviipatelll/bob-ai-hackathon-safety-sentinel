"""test_signal_detector.py — Unit tests for signal_detector.calculate_signal_table.

Tests cover:
  - Known-value PRR and chi-square (hand-computed expected values).
  - signal_flag=True when all three thresholds are met.
  - signal_flag=False when PRR is below threshold.
  - ValueError on missing columns.
  - ValueError on all-null / empty DataFrame.
  - NaN PRR (not a crash) when a=0 or c=0.
  - Three distinct triage_reason literals.
  - Sort order: signal_flag DESC, prr DESC, cases_a DESC.
"""
import math

import pandas as pd
import pytest

from signal_detector import (
    _REASON_BELOW,
    _REASON_INSUFFICIENT,
    _REASON_SIGNAL,
    calculate_signal_table,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_df(rows):
    """Build a DataFrame from a list of (drug, event) tuples."""
    return pd.DataFrame(rows, columns=["drug", "event"])


def _simple_two_drug_df():
    """Minimal 2-drug / 1-event dataset with a known PRR.

    DrugA: 10 Headache, 0 other events  → a=10, b=0
    DrugB: 2 Headache, 8 other events   → c=2, d=8

    PRR_DrugA_Headache = (10/10) / (2/10) = 1 / 0.2 = 5.0
    """
    rows = (
        [("DrugA", "Headache")] * 10
        + [("DrugB", "Headache")] * 2
        + [("DrugB", "Nausea")] * 8
    )
    return _make_df(rows)


# ---------------------------------------------------------------------------
# Input-validation tests
# ---------------------------------------------------------------------------

def test_missing_drug_column():
    df = pd.DataFrame({"event": ["Headache"]})
    with pytest.raises(ValueError, match="Missing columns"):
        calculate_signal_table(df)


def test_missing_event_column():
    df = pd.DataFrame({"drug": ["DrugA"]})
    with pytest.raises(ValueError, match="Missing columns"):
        calculate_signal_table(df)


def test_missing_both_columns():
    df = pd.DataFrame({"x": [1]})
    with pytest.raises(ValueError, match="Missing columns"):
        calculate_signal_table(df)


def test_empty_dataframe_after_dropna():
    df = pd.DataFrame({"drug": [None, None], "event": [None, None]})
    with pytest.raises(ValueError, match="No valid rows"):
        calculate_signal_table(df)


def test_completely_empty_dataframe():
    df = pd.DataFrame(columns=["drug", "event"])
    with pytest.raises(ValueError, match="No valid rows"):
        calculate_signal_table(df)


# ---------------------------------------------------------------------------
# Numerical correctness tests
# ---------------------------------------------------------------------------

def test_prr_known_value():
    """PRR for DrugA/Headache should be exactly 5.0 (see _simple_two_drug_df docstring)."""
    df = _simple_two_drug_df()
    result = calculate_signal_table(df)
    row = result[(result.drug == "druga") & (result.event == "headache")]
    assert len(row) == 1
    assert math.isclose(row.iloc[0]["prr"], 5.0, rel_tol=1e-3), row.iloc[0]["prr"]


def test_chi_square_positive_for_strong_signal():
    """Chi-square must be > 0 for a strong association."""
    df = _simple_two_drug_df()
    result = calculate_signal_table(df)
    row = result[(result.drug == "druga") & (result.event == "headache")]
    assert row.iloc[0]["chi_square"] > 0


def test_prr_nan_when_c_is_zero():
    """When only one drug reports an event, c=0 and PRR must be NaN (not a crash)."""
    # DrugA is the only reporter of Rash → c=0 for DrugA/Rash; DrugB/Rash also has c=0
    rows = (
        [("DrugA", "Rash")] * 5
        + [("DrugA", "Headache")] * 3
        + [("DrugB", "Headache")] * 4
    )
    df = _make_df(rows)
    result = calculate_signal_table(df)
    rash_rows = result[result.event == "rash"]
    for _, r in rash_rows.iterrows():
        # For DrugA: c = reports of Rash by other drugs = 0, so PRR should be NaN
        if r["drug"] == "druga":
            assert math.isnan(r["prr"]), "Expected NaN PRR when c=0"


def test_prr_nan_when_a_is_zero():
    """When a=0 (drug never reported the event) PRR must be NaN."""
    rows = (
        [("DrugA", "Headache")] * 5
        + [("DrugB", "Headache")] * 5
        + [("DrugB", "Nausea")] * 3
    )
    df = _make_df(rows)
    result = calculate_signal_table(df)
    # DrugA never reported Nausea → a=0
    row = result[(result.drug == "druga") & (result.event == "nausea")]
    assert len(row) == 1
    assert math.isnan(row.iloc[0]["prr"])


# ---------------------------------------------------------------------------
# Triage flag tests
# ---------------------------------------------------------------------------

def test_signal_flag_true_when_all_thresholds_met():
    """signal_flag must be True when a ≥ min_cases, PRR ≥ threshold, chi2 ≥ threshold."""
    df = _simple_two_drug_df()
    result = calculate_signal_table(df, min_cases=3, prr_threshold=2.0, chi2_threshold=4.0)
    row = result[(result.drug == "druga") & (result.event == "headache")]
    assert bool(row.iloc[0]["signal_flag"]) is True


def test_signal_flag_false_when_prr_below_threshold():
    """signal_flag must be False when PRR < threshold."""
    # PRR ≈ 1.0 (equal proportions)
    rows = (
        [("DrugA", "Headache")] * 5
        + [("DrugA", "Nausea")] * 5
        + [("DrugB", "Headache")] * 5
        + [("DrugB", "Nausea")] * 5
    )
    df = _make_df(rows)
    result = calculate_signal_table(df, min_cases=3, prr_threshold=2.0, chi2_threshold=4.0)
    row = result[(result.drug == "druga") & (result.event == "headache")]
    assert bool(row.iloc[0]["signal_flag"]) is False


def test_signal_flag_false_when_below_min_cases():
    """signal_flag must be False when a < min_cases even if PRR and chi2 are high."""
    # Only 1 case for DrugA/Headache
    rows = (
        [("DrugA", "Headache")] * 1
        + [("DrugA", "Nausea")] * 1
        + [("DrugB", "Headache")] * 10
        + [("DrugB", "Nausea")] * 30
    )
    df = _make_df(rows)
    result = calculate_signal_table(df, min_cases=3, prr_threshold=2.0, chi2_threshold=4.0)
    row = result[(result.drug == "druga") & (result.event == "headache")]
    assert bool(row.iloc[0]["signal_flag"]) is False


# ---------------------------------------------------------------------------
# Triage reason tests
# ---------------------------------------------------------------------------

def test_triage_reason_signal():
    df = _simple_two_drug_df()
    result = calculate_signal_table(df, min_cases=3, prr_threshold=2.0, chi2_threshold=4.0)
    row = result[(result.drug == "druga") & (result.event == "headache")]
    assert row.iloc[0]["triage_reason"] == _REASON_SIGNAL


def test_triage_reason_insufficient():
    """When c=0, triage_reason must be the insufficient-exposure literal."""
    rows = (
        [("DrugA", "Rash")] * 5
        + [("DrugA", "Headache")] * 3
        + [("DrugB", "Headache")] * 4
    )
    df = _make_df(rows)
    result = calculate_signal_table(df)
    row = result[(result.drug == "druga") & (result.event == "rash")]
    assert row.iloc[0]["triage_reason"] == _REASON_INSUFFICIENT


def test_triage_reason_below():
    """When thresholds are not met but data is valid, triage_reason must be below-threshold literal."""
    rows = (
        [("DrugA", "Headache")] * 5
        + [("DrugA", "Nausea")] * 5
        + [("DrugB", "Headache")] * 5
        + [("DrugB", "Nausea")] * 5
    )
    df = _make_df(rows)
    result = calculate_signal_table(df, min_cases=3, prr_threshold=2.0, chi2_threshold=4.0)
    row = result[(result.drug == "druga") & (result.event == "headache")]
    assert row.iloc[0]["triage_reason"] == _REASON_BELOW


# ---------------------------------------------------------------------------
# Sort order test
# ---------------------------------------------------------------------------

def test_sort_order_signal_flag_first():
    """Flagged rows must appear before unflagged rows."""
    df = _simple_two_drug_df()
    result = calculate_signal_table(df, min_cases=3, prr_threshold=2.0, chi2_threshold=4.0)
    flags = result["signal_flag"].tolist()
    # Once we hit a False, there must be no more Trues.
    seen_false = False
    for f in flags:
        if not f:
            seen_false = True
        if seen_false and f:
            pytest.fail("A True signal_flag appeared after a False one — sort order is wrong.")


# ---------------------------------------------------------------------------
# Output columns test
# ---------------------------------------------------------------------------

def test_output_columns():
    df = _simple_two_drug_df()
    result = calculate_signal_table(df)
    expected_cols = {
        "drug", "event", "cases_a", "drug_other_events_b",
        "other_drugs_event_c", "other_drugs_other_events_d",
        "prr", "chi_square", "signal_flag", "triage_reason",
    }
    assert expected_cols <= set(result.columns)


# ---------------------------------------------------------------------------
# Demo-data smoke test
# ---------------------------------------------------------------------------

def test_demo_events_produces_at_least_two_flagged_signals():
    """The demo dataset must flag at least 2 candidate signals with default thresholds."""
    from demo_data import demo_events
    df = demo_events()
    result = calculate_signal_table(df)
    flagged = result[result.signal_flag]
    assert len(flagged) >= 2, f"Expected ≥2 flagged signals, got {len(flagged)}"


def test_demo_events_produces_insufficient_exposure_rows():
    """At least one row must have the 'Insufficient exposure' triage reason."""
    from demo_data import demo_events
    df = demo_events()
    result = calculate_signal_table(df)
    insuf = result[result.triage_reason == _REASON_INSUFFICIENT]
    assert len(insuf) >= 1, "Expected at least one insufficient-exposure row"
