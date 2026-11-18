"""
Scores one forecast against how its question resolved, on the same scale as
Metaculus's baseline score: 0 is what a know-nothing forecast gets (50% on a
yes/no question, equal odds on every option, a flat spread on a number
question), higher is better, and a confident wrong answer costs a lot.

    yes/no      100 * ln(p(outcome) / 0.5) / ln 2
    options     100 * ln(p(outcome) * N) / ln N             (N options)
    numbers     100 * ln(p(bin of outcome) / flat p(bin)) / 2

as in Metaculus's scoring code (score_math.evaluate_forecasts_baseline_accuracy).
An outcome on the line between two bins counts in the lower bin, as on
Metaculus. The flat forecast and the floors differ a little from theirs;
every news setup is scored the same way, so it is fair for comparing them.
Each probability is floored so one forecast cannot score minus infinity.
"""
from __future__ import annotations

import bisect
import math
from datetime import datetime

FLOOR = 0.001  # yes/no and options: 0.1%
BIN_FLOOR = 0.0001  # one bin of a number question
OUT_OF_BOUNDS_FLAT = 0.05  # the flat forecast's chance for each open end


def binary(p_yes: float, resolved_yes: bool) -> float:
    p = p_yes if resolved_yes else 1.0 - p_yes
    return 100.0 * math.log2(max(p, FLOOR) / 0.5)


def brier(p_yes: float, resolved_yes: bool) -> float:
    return (p_yes - (1.0 if resolved_yes else 0.0)) ** 2


def multiple_choice(probs: dict[str, float], resolved: str) -> float:
    n = len(probs)
    if n < 2:
        raise ValueError("a multiple-choice forecast needs at least two options")
    if resolved not in probs:
        raise ValueError(f"resolved option {resolved!r} is not one of {sorted(probs)}")
    total = sum(probs.values())
    p = probs[resolved] / total if total > 0 else 0.0
    return 100.0 * math.log(max(p, FLOOR) * n) / math.log(n)


def _x(value) -> float:
    return value.timestamp() if isinstance(value, datetime) else float(value)


def numeric(
    values: list,
    cdf: list[float],
    resolved,
    open_lower: bool,
    open_upper: bool,
) -> float:
    """
    `values` and `cdf` are the forecast's CDF points (Metaculus's 201 points,
    fewer for a discrete question): cdf[i] = P(outcome below values[i]),
    cdf[0] = P(below the range), 1 - cdf[-1] = P(above it). `resolved` is the
    answer (a number or a date) or "below_lower_bound" / "above_upper_bound".
    """
    if len(values) != len(cdf) or len(cdf) < 2:
        raise ValueError("values and cdf must be the same length, at least 2")
    xs = [_x(v) for v in values]
    bins = len(cdf) - 1
    inside_flat = (1.0 - OUT_OF_BOUNDS_FLAT * open_lower - OUT_OF_BOUNDS_FLAT * open_upper) / bins
    if resolved == "below_lower_bound":
        p, flat = cdf[0], OUT_OF_BOUNDS_FLAT
    elif resolved == "above_upper_bound":
        p, flat = 1.0 - cdf[-1], OUT_OF_BOUNDS_FLAT
    else:
        x = _x(resolved)
        eps = 1e-9 * max(abs(xs[-1] - xs[0]), 1e-12)  # float noise in the CDF's x-values
        if x < xs[0] - eps:
            p, flat = cdf[0], OUT_OF_BOUNDS_FLAT
        elif x > xs[-1] + eps:
            p, flat = 1.0 - cdf[-1], OUT_OF_BOUNDS_FLAT
        else:
            # Bin k covers (xs[k-1], xs[k]]; the lower bound itself is in bin 1.
            k = min(max(bisect.bisect_left(xs, x - eps), 1), bins)
            p, flat = cdf[k] - cdf[k - 1], inside_flat
    return 100.0 * math.log(max(p, BIN_FLOOR) / flat) / 2.0
