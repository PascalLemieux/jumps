"""Delta hedging a short option along real price paths.

A short at-the-money call is sold at the start of a window and delta-hedged
with the underlying until expiry, rebalancing at a chosen interval. The model
enters only through the Black-Scholes delta; the path is whatever the market
did. Rates and carry are set to zero.

The hedged profit of the seller is

    premium - payoff + sum of delta_j * (S_{j+1} - S_j),

and its dispersion across windows is the hedging error.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import ndtr

MINUTES_PER_YEAR = 365 * 1440


def bs_call(spot: np.ndarray, strike: np.ndarray, sigma: np.ndarray, tau: np.ndarray) -> np.ndarray:
    """Black-Scholes call price with zero rates. ``tau`` in years; at ``tau = 0`` the payoff."""
    spot, strike, sigma, tau = np.broadcast_arrays(spot, strike, sigma, tau)
    out = np.maximum(spot - strike, 0.0).astype(float)
    live = tau > 0
    v = sigma[live] * np.sqrt(tau[live])
    d1 = np.log(spot[live] / strike[live]) / v + 0.5 * v
    out[live] = spot[live] * ndtr(d1) - strike[live] * ndtr(d1 - v)
    return out


def bs_delta(spot: np.ndarray, strike: np.ndarray, sigma: np.ndarray, tau: np.ndarray) -> np.ndarray:
    """Black-Scholes call delta with zero rates, for ``tau > 0``."""
    v = sigma * np.sqrt(tau)
    return ndtr(np.log(spot / strike) / v + 0.5 * v)


def bs_gamma(spot: np.ndarray, strike: np.ndarray, sigma: np.ndarray, tau: np.ndarray) -> np.ndarray:
    """Black-Scholes gamma with zero rates, for ``tau > 0``."""
    v = sigma * np.sqrt(tau)
    d1 = np.log(spot / strike) / v + 0.5 * v
    return np.exp(-0.5 * d1**2) / np.sqrt(2.0 * np.pi) / (spot * v)


def windows(close: pd.Series, days: int, start_hour: int = 8, weekday: int | None = None,
            first: str | None = None, last: str | None = None) -> tuple[pd.DatetimeIndex, np.ndarray]:
    """Non-overlapping price windows of ``days`` days on the 1-minute grid.

    Each window starts at ``start_hour`` UTC (08:00 is Deribit's expiry time),
    on every day for one-day windows or on the given ``weekday`` otherwise, and
    holds ``days * 1440 + 1`` prices. Gaps of up to five minutes are forward
    filled; windows with longer gaps are dropped. Returns the start times and
    the (window x minute) price matrix.
    """
    close = close.sort_index()
    grid = pd.date_range(close.index[0].ceil("D"), close.index[-1].floor("D"), freq="1min")
    # A bar stamped hh:mm closes one minute later, so the price *at* time t is the close of the bar before.
    px = close.reindex(grid - pd.Timedelta(minutes=1)).ffill(limit=5).to_numpy()
    n = days * 1440
    starts = pd.date_range(grid[0].floor("D") + pd.Timedelta(hours=start_hour), grid[-1], freq=f"{days}D")
    if weekday is not None:
        offset = (weekday - starts[0].dayofweek) % 7
        starts = pd.date_range(starts[0] + pd.Timedelta(days=offset), grid[-1], freq=f"{days}D")
    if first:
        starts = starts[starts >= pd.Timestamp(first, tz="UTC")]
    if last:
        starts = starts[starts <= pd.Timestamp(last, tz="UTC")]
    pos = ((starts - grid[0]) / pd.Timedelta(minutes=1)).astype(int).to_numpy()
    pos_ok = pos[(pos >= 0) & (pos + n < len(px))]
    block = np.stack([px[p: p + n + 1] for p in pos_ok])
    keep = np.isfinite(block).all(axis=1)
    return starts[(pos >= 0) & (pos + n < len(px))][keep], block[keep]


def realised_volatility(paths: np.ndarray) -> np.ndarray:
    """Annualised volatility of each window from its 1-minute returns."""
    r = np.diff(np.log(paths), axis=1)
    return np.sqrt(np.sum(r**2, axis=1) * MINUTES_PER_YEAR / r.shape[1])


def hedge(paths: np.ndarray, sigma: np.ndarray, step: int,
          clock: np.ndarray | None = None) -> dict[str, np.ndarray]:
    """Sell an at-the-money call on each path and delta-hedge every ``step`` minutes.

    ``paths`` is (windows x minutes + 1); ``sigma`` is one annualised volatility
    per window, used for the premium and for every delta. ``clock``, if given,
    is a (windows x minutes) array of weights saying how the variance of each
    window is expected to be spread over its minutes; the delta then uses the
    share of variance still to come instead of the share of time. Returns, per
    window, the seller's profit ``pnl``, the ``premium``, and the ``turnover``:
    the notional traded in the underlying, including the first hedge and the
    final unwind.
    """
    n = paths.shape[1] - 1
    strike = paths[:, 0]
    sig = np.asarray(sigma, dtype=float)
    idx = np.arange(0, n, step)
    s = paths[:, idx]
    if clock is None:
        tau = (n - idx)[None, :] / MINUTES_PER_YEAR
    else:
        spent = np.c_[np.zeros(len(clock)), np.cumsum(clock, axis=1)]
        remaining = 1.0 - spent[:, idx] / spent[:, -1:]
        tau = remaining * n / MINUTES_PER_YEAR
    delta = bs_delta(s, strike[:, None], sig[:, None], tau)
    nxt = paths[:, np.r_[idx[1:], n]]
    premium = bs_call(strike, strike, sig, np.full(len(strike), n / MINUTES_PER_YEAR))
    pnl = premium - np.maximum(paths[:, -1] - strike, 0.0) + np.sum(delta * (nxt - s), axis=1)
    trades = np.abs(np.diff(delta, axis=1, prepend=0.0)) * s
    turnover = trades.sum(axis=1) + np.abs(delta[:, -1]) * paths[:, -1]
    return {"pnl": pnl, "premium": premium, "turnover": turnover}


def simulate_paths(start: np.ndarray, sigma: np.ndarray, minutes: int, jump_share: float = 0.0,
                   jumps_per_day: float = 1.0, seed: int = 0) -> np.ndarray:
    """Benchmark paths on the 1-minute grid, one per entry of ``sigma``.

    Constant-volatility geometric Brownian motion with the given annualised
    volatility. With ``jump_share > 0`` that share of the variance comes from
    compound Poisson jumps with Gaussian sizes instead, a Merton jump diffusion
    with the same total variance.
    """
    rng = np.random.default_rng(seed)
    sig = np.asarray(sigma, dtype=float)[:, None]
    dt = 1.0 / MINUTES_PER_YEAR
    r = sig * np.sqrt((1.0 - jump_share) * dt) * rng.standard_normal((len(sigma), minutes))
    if jump_share > 0:
        lam = jumps_per_day / 1440.0
        jump_sd = sig * np.sqrt(jump_share * dt / lam)
        r = r + (rng.random(r.shape) < lam) * jump_sd * rng.standard_normal(r.shape)
    return np.asarray(start)[:, None] * np.exp(np.c_[np.zeros(len(sigma)), np.cumsum(r, axis=1)])


def seasonal_clock(starts: pd.DatetimeIndex, minutes: int, factor: pd.Series) -> np.ndarray:
    """Expected share of variance of each minute of each window, from a seasonality factor.

    ``factor`` is the seasonality factor of 5-minute returns indexed by the end
    of each interval, as estimated in post 2. The weight of a minute is the
    squared factor of the 5-minute slot it falls in.
    """
    step = np.timedelta64(1, "m").astype(f"timedelta64[{starts.unit}]").astype(np.int64)
    ends = starts.asi8[:, None] + np.arange(1, minutes + 1, dtype=np.int64)[None, :] * step
    stamps = pd.DatetimeIndex(ends.ravel().astype(f"datetime64[{starts.unit}]"), tz="UTC").ceil("5min")
    w = factor.reindex(stamps).to_numpy().reshape(len(starts), minutes) ** 2
    return np.where(np.isfinite(w), w, 1.0)


def variance_timing(paths: np.ndarray, sigma: np.ndarray, block: int = 1) -> np.ndarray:
    """Profit of a continuously hedged short call implied by where the variance fell.

    ``0.5 * sum of gamma * S^2 * (sigma^2 dt - r^2)`` over the minutes of each
    window: the option was sold for a variance of ``sigma^2`` spread evenly over
    time, and pays for the variance that occurred, weighted by the gamma at
    that moment. With ``block > 1`` both the gamma and the variance are
    aggregated over blocks of that many minutes first, which keeps only the
    information of which block was volatile.
    """
    n = paths.shape[1] - 1
    s = paths[:, :-1]
    tau = (n - np.arange(n))[None, :] / MINUTES_PER_YEAR
    sig = np.asarray(sigma, dtype=float)[:, None]
    gamma = bs_gamma(s, paths[:, :1], sig, tau)
    gap = sig**2 * s**2 / MINUTES_PER_YEAR - np.diff(paths, axis=1) ** 2
    if block > 1:
        gamma = gamma.reshape(len(paths), -1, block).mean(axis=2)
        gap = gap.reshape(len(paths), -1, block).sum(axis=2)
    return 0.5 * np.sum(gamma * gap, axis=1)
