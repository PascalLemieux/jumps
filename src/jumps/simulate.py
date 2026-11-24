"""Simulated price paths where the truth about jumps is known.

Two worlds share the same stochastic-volatility backbone (a persistent daily
level and an intraday periodic pattern):

* ``kind="bursts"``: the path is continuous. Volatility occasionally spikes
  for a few minutes and then decays. There are no jumps at all.
* ``kind="jumps"``: no volatility spikes, but genuine price discontinuities
  arrive at random times.
* ``kind="vg"``: a variance gamma process, i.e. Brownian motion run on a gamma
  clock. It is purely discontinuous with infinite activity and has no diffusion
  component at all. It shares the daily volatility level and intraday pattern
  of the other two worlds, applied as a deterministic time change.

Both return a (days x prices) table of log prices on a regular grid, in the
layout produced by :func:`jumps.data.to_daily_grid`.
"""

from __future__ import annotations

import numpy as np

SECONDS_PER_DAY = 86_400


def simulate_log_prices(
    kind: str = "bursts",
    n_days: int = 300,
    dt_seconds: int = 5,
    annual_vol: float = 0.50,
    events_per_day: float = 0.5,
    burst_size: tuple[float, float] = (10.0, 25.0),
    burst_half_life: float = 60.0,
    jump_variance_share: float = 0.10,
    vg_nu: float = 0.02,
    seed: int = 0,
) -> np.ndarray:
    """Simulate log prices; see the module docstring for the two ``kind`` values.

    burst_size
        Range of the peak multiplier applied to volatility at a burst.
    burst_half_life
        Half-life of a burst in seconds.
    jump_variance_share
        Target share of total variance due to jumps when ``kind="jumps"``.
    vg_nu
        Variance of the gamma clock per unit of business time, in days, when
        ``kind="vg"``. Smaller values make the path closer to Brownian motion.
        With 0.02 the gamma increment over one hour has shape 1/(24*0.02) = 2.1.
    """
    if kind not in {"bursts", "jumps", "vg"}:
        raise ValueError("kind must be 'bursts', 'jumps' or 'vg'")
    rng = np.random.default_rng(seed)
    n = SECONDS_PER_DAY // dt_seconds
    total = n_days * n

    # Persistent daily volatility level (AR(1) in logs).
    log_level = np.zeros(n_days)
    for d in range(1, n_days):
        log_level[d] = 0.95 * log_level[d - 1] + 0.10 * rng.standard_normal()
    level = np.repeat(np.exp(log_level), n)

    # Intraday periodicity: one smooth cycle per day.
    tod = np.tile(np.arange(n) / n, n_days)
    periodic = 1.0 + 0.35 * np.cos(2.0 * np.pi * tod)

    sigma = np.sqrt(annual_vol**2 / 365.0 / n) * level * periodic
    n_events = rng.poisson(events_per_day * n_days)
    starts = rng.integers(0, total, size=n_events)

    if kind == "bursts":
        tau = burst_half_life / np.log(2.0) / dt_seconds  # decay in steps
        window = int(12 * tau)
        decay = np.exp(-np.arange(window) / tau)
        mult = np.ones(total)
        for s, peak in zip(starts, rng.uniform(*burst_size, size=n_events)):
            end = min(s + window, total)
            mult[s:end] += peak * decay[: end - s]
        sigma = sigma * mult

    if kind == "vg":
        # Symmetric variance gamma: subordinate a Brownian motion to a gamma
        # clock whose mean matches the diffusive variance budget of each step.
        dt_days = dt_seconds / SECONDS_PER_DAY
        g = rng.gamma(shape=dt_days / vg_nu, scale=vg_nu / dt_days, size=total)  # mean 1
        r = sigma * np.sqrt(g) * rng.standard_normal(total)
    else:
        r = sigma * rng.standard_normal(total)

    if kind == "jumps":
        # Size jumps so they carry the target share of total variance.
        diffusive_var = np.sum(sigma**2)
        jump_sd = np.sqrt(
            jump_variance_share / (1.0 - jump_variance_share) * diffusive_var / max(n_events, 1)
        )
        np.add.at(r, starts, jump_sd * rng.standard_normal(n_events))

    logp = np.log(100.0) + np.cumsum(r)
    grid = logp.reshape(n_days, n)
    prev_close = np.r_[np.log(100.0), grid[:-1, -1]]
    return np.column_stack([prev_close, grid])
