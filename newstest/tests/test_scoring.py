import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scoring  # noqa: E402


def test_binary_matches_metaculus_baseline():
    assert scoring.binary(0.5, True) == pytest.approx(0)
    assert scoring.binary(0.8, True) == pytest.approx(100 * math.log2(1.6))
    assert scoring.binary(0.8, False) == pytest.approx(100 * math.log2(0.4))
    assert scoring.binary(1.0, False) == pytest.approx(100 * math.log2(0.001 / 0.5))  # floored
    assert scoring.brier(0.8, False) == pytest.approx(0.64)


def test_multiple_choice():
    even = {"a": 0.25, "b": 0.25, "c": 0.25, "d": 0.25}
    assert scoring.multiple_choice(even, "c") == pytest.approx(0)
    assert scoring.multiple_choice({"a": 1.0, "b": 0.0}, "a") == pytest.approx(100)
    assert scoring.multiple_choice({"a": 0.5, "b": 0.25, "c": 0.25}, "a") > 0
    with pytest.raises(ValueError):
        scoring.multiple_choice(even, "e")


def _flat(n=201, lo=0.0, hi=200.0):
    values = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
    cdf = [i / (n - 1) for i in range(n)]
    return values, cdf


def test_numeric_flat_forecast_scores_zero_inside_closed_bounds():
    values, cdf = _flat()
    assert scoring.numeric(values, cdf, 123.4, False, False) == pytest.approx(0)
    assert scoring.numeric(values, cdf, 200.0, False, False) == pytest.approx(0)  # top edge is the last bin
    assert scoring.numeric(values, cdf, 0.0, False, False) == pytest.approx(0)


def test_numeric_rewards_mass_on_the_outcome_and_handles_open_ends():
    values, _ = _flat()
    # 90% of the mass in the bin [100, 101], the rest spread evenly.
    cdf = [0.0]
    for i in range(200):
        cdf.append(cdf[-1] + (0.9 if i == 100 else 0.1 / 199))
    assert scoring.numeric(values, cdf, 100.5, False, False) > 200
    assert scoring.numeric(values, cdf, 10.0, False, False) < 0
    # Open upper end with 5% above it: an outcome above the range gets that 5%, vs a flat 5%.
    cdf_open = [c * 0.95 for c in _flat()[1]]
    assert scoring.numeric(values, cdf_open, "above_upper_bound", False, True) == pytest.approx(0)
    assert scoring.numeric(values, cdf_open, 250.0, False, True) == pytest.approx(0)


def test_numeric_dates_compare_as_timestamps():
    lo = datetime(2026, 11, 1, tzinfo=timezone.utc).timestamp()
    values, cdf = _flat(lo=lo, hi=lo + 200 * 86400)
    day = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)
    assert scoring.numeric(values, cdf, day, False, False) == pytest.approx(0)


def test_numeric_uses_natural_log_halved_like_metaculus():
    values, _ = _flat()
    # Bin (100, 101] holds twice the flat 1/200, the rest shares what is left.
    cdf = [0.0]
    for i in range(200):
        cdf.append(cdf[-1] + (2 / 200 if i == 100 else (1 - 2 / 200) / 199))
    assert scoring.numeric(values, cdf, 100.5, False, False) == pytest.approx(50 * math.log(2), rel=1e-6)


def test_outcome_on_a_bin_line_counts_in_the_lower_bin():
    values, _ = _flat()
    cdf = [0.0]
    for i in range(200):
        # all mass in bin (99, 100], none in (100, 101]
        cdf.append(cdf[-1] + (1.0 if i == 99 else 0.0))
    assert scoring.numeric(values, cdf, 100.0, False, False) > 200
    assert scoring.numeric(values, cdf, 100.0 + 1e-13, False, False) > 200  # float noise stays put
    assert scoring.numeric(values, cdf, 100.5, False, False) < 0
