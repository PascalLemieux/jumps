"""Realized measures and the Barndorff-Nielsen-Shephard jump test.

All functions take ``r``, an array of intraday log returns with shape
``(n_days, n_intraday)``, and return one value per day.

References
----------
Barndorff-Nielsen & Shephard (2004, 2006); Huang & Tauchen (2005).
"""

from __future__ import annotations

import numpy as np
from scipy.special import gamma
from scipy.stats import norm

MU_1 = np.sqrt(2.0 / np.pi)                              # E|Z|
MU_43 = 2.0 ** (2.0 / 3.0) * gamma(7.0 / 6.0) / gamma(0.5)  # E|Z|^(4/3)
THETA = (np.pi / 2.0) ** 2 + np.pi - 5.0                 # ~0.609


def subsample_returns(logp: np.ndarray, step: int) -> np.ndarray:
    """Log returns from a (days x prices) table, keeping every ``step``-th price."""
    return np.diff(np.asarray(logp)[:, ::step], axis=1)


def realized_variance(r: np.ndarray) -> np.ndarray:
    """RV = sum r_i^2. Converges to integrated variance plus squared jumps."""
    return np.sum(r**2, axis=1)


def bipower_variation(r: np.ndarray) -> np.ndarray:
    """BV = mu_1^-2 sum |r_i||r_{i-1}|. Converges to integrated variance only."""
    n = r.shape[1]
    a = np.abs(r)
    return (n / (n - 1)) * np.sum(a[:, 1:] * a[:, :-1], axis=1) / MU_1**2


def tripower_quarticity(r: np.ndarray) -> np.ndarray:
    """Jump-robust estimate of integrated quarticity."""
    n = r.shape[1]
    a = np.abs(r) ** (4.0 / 3.0)
    s = np.sum(a[:, 2:] * a[:, 1:-1] * a[:, :-2], axis=1)
    return n * (n / (n - 2)) * s / MU_43**3


def bns_jump_test(r: np.ndarray) -> dict[str, np.ndarray]:
    """Ratio-form BNS test with the Huang-Tauchen max adjustment.

    Under the null of no jumps on a day, ``z`` is asymptotically N(0, 1).
    Large positive values reject. Returns RV, BV, the relative jump measure
    ``rj = (RV - BV) / RV``, the statistic ``z`` and its one-sided p-value.
    """
    n = r.shape[1]
    rv = realized_variance(r)
    bv = bipower_variation(r)
    tq = tripower_quarticity(r)
    rj = (rv - bv) / rv
    z = rj / np.sqrt(THETA / n * np.maximum(1.0, tq / bv**2))
    return {"rv": rv, "bv": bv, "rj": rj, "z": z, "pvalue": norm.sf(z)}


def jump_summary(logp: np.ndarray, steps: list[int], alpha: float = 0.01) -> dict[str, np.ndarray]:
    """Jump share of variance and share of days flagged, per sampling step.

    ``steps`` are multiples of the base grid of ``logp``. The jump share is
    ``1 - sum(BV) / sum(RV)`` over all days, so it is not floored at zero and
    stays unbiased when the true share is zero.
    """
    share, flagged = [], []
    for step in steps:
        res = bns_jump_test(subsample_returns(logp, step))
        share.append(1.0 - res["bv"].sum() / res["rv"].sum())
        flagged.append(np.mean(res["pvalue"] < alpha))
    return {"jump_share": np.array(share), "days_flagged": np.array(flagged)}
