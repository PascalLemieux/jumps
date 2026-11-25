"""Jump activity: counting large increments, after Aït-Sahalia and Jacod.

The Blumenthal-Getoor index ``beta`` of a jump process is the smallest power
``p`` for which the sum of ``|jump|^p`` over a finite interval is finite. It
lies in [0, 2]: 0 for compound Poisson and variance gamma, ``Y`` for CGMY,
``alpha`` for an alpha-stable process.

Aït-Sahalia and Jacod (2009) estimate it from the number of increments larger
than a threshold: that number scales like ``threshold^(-beta)``. Their
companion paper (2011) tests finite against infinite activity with truncated
power variations at two sampling frequencies.
"""

from __future__ import annotations

import numpy as np
from scipy.special import gamma
from scipy.stats import norm


def exceedance_counts(z: np.ndarray, thresholds: np.ndarray) -> np.ndarray:
    """Number of observations with ``|z|`` above each threshold. NaNs are ignored."""
    a = np.sort(np.abs(z[np.isfinite(z)]))
    return len(a) - np.searchsorted(a, thresholds, side="right")


def gaussian_counts(n: int, thresholds: np.ndarray) -> np.ndarray:
    """Expected number of exceedances among ``n`` standard normal observations."""
    return n * 2.0 * norm.sf(thresholds)


def activity_index(count_low: float, count_high: float, ratio: float) -> tuple[float, float]:
    """Estimate of the activity index from counts at two thresholds, with its standard error.

    Equation (16) of Aït-Sahalia and Jacod (2009):
    ``beta = log(U(alpha) / U(alpha')) / log(alpha' / alpha)`` with
    ``ratio = alpha' / alpha > 1``. By their Theorem 3 the standard error is
    ``sqrt(1/U(alpha') - 1/U(alpha)) / log(alpha' / alpha)``.
    Returns NaNs when the upper count is zero.
    """
    if count_high <= 0 or count_low <= 0:
        return np.nan, np.nan
    beta = np.log(count_low / count_high) / np.log(ratio)
    se = np.sqrt(1.0 / count_high - 1.0 / count_low) / np.log(ratio)
    return float(beta), float(se)


def index_table(z: np.ndarray, alphas: list[float], ratio: float = 2.0) -> list[dict[str, float]]:
    """Activity index estimates for several lower thresholds ``alpha`` and ``alpha' = ratio * alpha``."""
    rows = []
    for a in alphas:
        low, high = exceedance_counts(z, np.array([a, ratio * a]))
        beta, se = activity_index(low, high, ratio)
        rows.append({"alpha": a, "count above alpha": int(low), "count above alpha'": int(high),
                     "beta": beta, "se": se})
    return rows


def truncated_power_ratio(r: np.ndarray, cutoff: np.ndarray | float, p: float = 4.0, k: int = 2) -> float:
    """Aït-Sahalia and Jacod (2011) statistic ``S_n = B(p, u, k*Delta) / B(p, u, Delta)``.

    ``B`` is the sum of ``|increment|^p`` over increments no larger than the
    cutoff ``u``. With finite-activity jumps and a Brownian part the ratio tends
    to ``k^(p/2 - 1)``; with infinitely active jumps it tends to 1. ``cutoff``
    may vary through time, one value per fine increment.
    """
    m = (len(r) // k) * k
    fine = r[:m]
    cut = np.broadcast_to(np.asarray(cutoff, dtype=float), r.shape)[:m]
    coarse = fine.reshape(-1, k).sum(axis=1)
    cut_coarse = cut.reshape(-1, k)[:, 0]
    ok_f, ok_c = np.isfinite(fine) & np.isfinite(cut), np.isfinite(coarse) & np.isfinite(cut_coarse)
    b_fine = np.sum(np.abs(fine[ok_f & (np.abs(fine) <= cut)]) ** p)
    b_coarse = np.sum(np.abs(coarse[ok_c & (np.abs(coarse) <= cut_coarse)]) ** p)
    return float(b_coarse / b_fine)


def symmetric_stable(alpha: float, size: int, rng: np.random.Generator) -> np.ndarray:
    """Standard symmetric alpha-stable draws by the Chambers-Mallows-Stuck method."""
    v = rng.uniform(-np.pi / 2.0, np.pi / 2.0, size)
    w = rng.exponential(1.0, size)
    return (np.sin(alpha * v) / np.cos(v) ** (1.0 / alpha)
            * (np.cos(v - alpha * v) / w) ** ((1.0 - alpha) / alpha))


def simulate_increments(kind: str, n: int, jump_share: float = 0.10, alpha: float = 1.5,
                        jumps_per_10k: float = 5.0, burst_tail: float = 3.0,
                        bursts_per_10k: float = 8.0, burst_half_life: float = 12.0,
                        seed: int = 0) -> np.ndarray:
    """Increments of a unit-variance Brownian motion plus something else, for sanity checks.

    * ``"stable"``: symmetric alpha-stable increments, scaled so that a typical
      one (their median absolute value) is ``sqrt(jump_share)`` of the Brownian
      one. Infinite activity with index ``alpha``.
    * ``"poisson"``: compound Poisson jumps with Gaussian sizes carrying
      ``jump_share`` of the variance. Finite activity, index 0.
    * ``"bursts"``: no jumps at all. Volatility spikes at random times and
      decays with ``burst_half_life`` increments; the size of a spike is Pareto
      with tail exponent ``burst_tail``. The path is continuous.
    * ``"diffusion"``: constant volatility, no jumps.
    """
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    if kind == "bursts":
        starts = np.flatnonzero(rng.random(n) < bursts_per_10k / 1e4)
        peaks = rng.pareto(burst_tail, len(starts)) + 1.0
        tau = burst_half_life / np.log(2.0)
        window = int(12 * tau)
        decay = np.exp(-np.arange(window) / tau)
        extra = np.zeros(n)
        for s0, peak in zip(starts, peaks):
            end = min(s0 + window, n)
            extra[s0:end] += peak * decay[: end - s0]
        x = x * (1.0 + extra)
    elif kind == "stable":
        s = symmetric_stable(alpha, n, rng)
        x = x + np.sqrt(jump_share) * 0.6745 / np.median(np.abs(s)) * s
    elif kind == "poisson":
        hits = rng.random(n) < jumps_per_10k / 1e4
        size = np.sqrt(jump_share / (1.0 - jump_share) / (jumps_per_10k / 1e4))
        x = x + hits * size * rng.standard_normal(n)
    elif kind != "diffusion":
        raise ValueError("kind must be 'stable', 'poisson', 'bursts' or 'diffusion'")
    return x


def clock_scale(prices: dict[float, np.ndarray], seconds: float,
                base: float = 60.0, window: int = 603) -> np.ndarray:
    """Local standard deviation of each return on the ``seconds`` clock.

    The trailing bipower volatility of the ``base`` clock (one minute by
    default, over ``window`` returns), scaled by the square root of time. One
    ruler for every clock keeps thresholds comparable and avoids the zero
    returns of the finest clocks.
    """
    import pandas as pd

    from .seasonality import local_volatility

    n = len(prices[seconds]) - 1
    s_base = local_volatility(pd.Series(np.diff(prices[base])), window).to_numpy()
    if seconds <= base:
        scale = np.repeat(s_base, int(base // seconds)) * np.sqrt(seconds / base)
    else:
        step = int(seconds // base)
        scale = s_base[::step] * np.sqrt(step)
    out = np.full(n, np.nan)
    m = min(n, len(scale))
    out[:m] = scale[:m]
    return out


def standardise_clock(prices: dict[float, np.ndarray], seconds: float,
                      base: float = 60.0, window: int = 603) -> np.ndarray:
    """Returns on the ``seconds`` clock in units of their local standard deviation."""
    return np.diff(prices[seconds]) / clock_scale(prices, seconds, base, window)


def inside_large_moves(prices: dict[float, np.ndarray], coarse: float = 60.0, fine: float = 1.0,
                       sigmas: float = 5.0, window: int = 603) -> dict[str, float]:
    """Look inside every large ``coarse`` return at the ``fine`` clock.

    A coarse return is large when it exceeds ``sigmas`` local standard
    deviations. For each one, the share of the move carried by its largest fine
    return, and the number of fine intervals needed to cover half of it. A true
    discontinuity scores close to 100% and 1.
    """
    import pandas as pd

    from .seasonality import local_volatility

    r_c, r_f = np.diff(prices[coarse]), np.diff(prices[fine])
    k = int(coarse // fine)
    inside = r_f[: len(r_c) * k].reshape(-1, k)
    s = local_volatility(pd.Series(r_c), window).to_numpy()
    big = np.flatnonzero(np.abs(r_c) > sigmas * s)
    size = np.abs(r_c[big])
    share = np.abs(inside[big]).max(axis=1) / size
    half = np.array([(np.abs(np.cumsum(inside[b])) >= 0.5 * abs(r_c[b])).argmax() + 1 for b in big])
    return {"moves": len(big), "median_size": float(np.median(size)),
            "median_share": float(np.median(share)), "share_over_half": int((share > 0.5).sum()),
            "share_over_80": int((share > 0.8).sum()), "median_to_half": float(np.median(half))}
