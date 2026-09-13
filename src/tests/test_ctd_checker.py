"""test_ctd_checker.py — Unit tests for ctd_checker.check_ctd.

Tests cover:
  - All-present input → 100% completeness, zero missing rows.
  - All-missing input → 0% completeness, all rows missing.
  - Partial input (demo_ctd fixture) → expected per-module scores.
  - Case-insensitive module matching (lowercase module key in CSV).
  - Case-insensitive section matching.
  - ValueError on missing columns.
  - ValueError on empty DataFrame.
  - Return types and column presence.
"""
import pytest
import pandas as pd

from ctd_checker import REQUIRED, check_ctd


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------

def _all_present_df():
    """DataFrame with every required section present exactly once."""
    rows = []
    for module, sections in REQUIRED.items():
        for section in sections:
            rows.append({"module": module, "section": section})
    return pd.DataFrame(rows)


def _all_missing_df():
    """DataFrame with valid columns but no matching content."""
    return pd.DataFrame([{"module": "Module 99", "section": "99.1 Nonexistent"}])


# ---------------------------------------------------------------------------
# Input-validation tests
# ---------------------------------------------------------------------------

def test_missing_module_column():
    df = pd.DataFrame({"section": ["1.1 Regional Administrative Information"]})
    with pytest.raises(ValueError, match="Missing columns"):
        check_ctd(df)


def test_missing_section_column():
    df = pd.DataFrame({"module": ["Module 1"]})
    with pytest.raises(ValueError, match="Missing columns"):
        check_ctd(df)


def test_empty_dataframe():
    df = pd.DataFrame(columns=["module", "section"])
    with pytest.raises(ValueError, match="No data rows"):
        check_ctd(df)


# ---------------------------------------------------------------------------
# All-present → 100% completeness
# ---------------------------------------------------------------------------

def test_all_present_overall_100():
    scores, details, overall = check_ctd(_all_present_df())
    assert overall == 100.0, f"Expected 100.0 overall, got {overall}"


def test_all_present_no_missing_rows():
    scores, details, overall = check_ctd(_all_present_df())
    missing_rows = details[details.status == "Missing"]
    assert missing_rows.empty, f"Expected no missing rows, found:\n{missing_rows}"


def test_all_present_module_completeness_100():
    scores, details, overall = check_ctd(_all_present_df())
    for _, row in scores.iterrows():
        assert row["completeness_pct"] == 100.0, (
            f"{row['module']} completeness is {row['completeness_pct']}, expected 100"
        )


# ---------------------------------------------------------------------------
# All-missing → 0% completeness
# ---------------------------------------------------------------------------

def test_all_missing_overall_0():
    scores, details, overall = check_ctd(_all_missing_df())
    assert overall == 0.0, f"Expected 0.0 overall, got {overall}"


def test_all_missing_all_rows_missing():
    scores, details, overall = check_ctd(_all_missing_df())
    present_rows = details[details.status == "Present"]
    assert present_rows.empty, f"Expected all rows missing, but some are Present:\n{present_rows}"


# ---------------------------------------------------------------------------
# Case-insensitive matching
# ---------------------------------------------------------------------------

def test_module_matching_is_case_insensitive():
    """Submitting 'module 1' (lowercase) must match 'Module 1' in the checklist."""
    df = pd.DataFrame([
        {"module": "module 1", "section": "1.1 Regional Administrative Information"},
        {"module": "module 1", "section": "1.2 Application Form"},
        {"module": "module 1", "section": "1.3 Product Information"},
    ])
    scores, details, overall = check_ctd(df)
    m1 = scores[scores.module == "Module 1"].iloc[0]
    assert m1["present"] == 3, f"Expected 3 present for Module 1, got {m1['present']}"
    assert m1["completeness_pct"] == 100.0


def test_section_matching_is_case_insensitive():
    """Section labels in upper-case must still match the checklist."""
    df = pd.DataFrame([
        {"module": "Module 2", "section": "2.1 CTD TABLE OF CONTENTS"},
        {"module": "Module 2", "section": "2.2 CTD INTRODUCTION"},
        {"module": "Module 2", "section": "2.3 QUALITY OVERALL SUMMARY"},
        {"module": "Module 2", "section": "2.4 NONCLINICAL OVERVIEW"},
        {"module": "Module 2", "section": "2.5 CLINICAL OVERVIEW"},
    ])
    scores, details, overall = check_ctd(df)
    m2 = scores[scores.module == "Module 2"].iloc[0]
    assert m2["completeness_pct"] == 100.0


# ---------------------------------------------------------------------------
# Partial input — demo_ctd expected scores
# ---------------------------------------------------------------------------

def test_demo_ctd_expected_module_scores():
    """Verify per-module completeness matches the documented demo gaps.

    demo_ctd() gaps:
      Module 1: 2/3  → 66.7%
      Module 2: 4/5  → 80.0%
      Module 3: 3/4  → 75.0%
      Module 4: 3/5  → 60.0%
      Module 5: 3/4  → 75.0%
    """
    from demo_data import demo_ctd
    df = demo_ctd()
    scores, details, overall = check_ctd(df)

    expected = {
        "Module 1": (2, 66.7),
        "Module 2": (4, 80.0),
        "Module 3": (3, 75.0),
        "Module 4": (3, 60.0),
        "Module 5": (3, 75.0),
    }
    for module, (exp_present, exp_pct) in expected.items():
        row = scores[scores.module == module].iloc[0]
        assert row["present"] == exp_present, (
            f"{module}: expected present={exp_present}, got {row['present']}"
        )
        assert abs(row["completeness_pct"] - exp_pct) < 0.2, (
            f"{module}: expected {exp_pct}%, got {row['completeness_pct']}%"
        )


def test_demo_ctd_has_gap_in_every_module():
    """Every module in the demo CTD must have at least one missing section."""
    from demo_data import demo_ctd
    df = demo_ctd()
    scores, details, overall = check_ctd(df)
    for _, row in scores.iterrows():
        assert row["missing"] >= 1, (
            f"{row['module']} has no missing sections — demo gaps not exercised"
        )


def test_demo_ctd_overall_below_100():
    from demo_data import demo_ctd
    df = demo_ctd()
    scores, details, overall = check_ctd(df)
    assert overall < 100.0, f"Expected overall < 100, got {overall}"


# ---------------------------------------------------------------------------
# Return-type and column tests
# ---------------------------------------------------------------------------

def test_return_types():
    scores, details, overall = check_ctd(_all_present_df())
    assert isinstance(scores, pd.DataFrame)
    assert isinstance(details, pd.DataFrame)
    assert isinstance(overall, float)


def test_scores_columns():
    scores, _, _ = check_ctd(_all_present_df())
    expected_cols = {"module", "required_sections", "present", "missing", "completeness_pct"}
    assert expected_cols <= set(scores.columns)


def test_details_columns():
    _, details, _ = check_ctd(_all_present_df())
    expected_cols = {"module", "section", "status"}
    assert expected_cols <= set(details.columns)


def test_details_status_values_only_present_or_missing():
    _, details, _ = check_ctd(_all_present_df())
    assert set(details["status"].unique()) <= {"Present", "Missing"}


def test_scores_has_one_row_per_module():
    scores, _, _ = check_ctd(_all_present_df())
    assert len(scores) == len(REQUIRED)
