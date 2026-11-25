"""Is volatility rough? Scaling of log-volatility increments, and what measurement does to it.

Gatheral, Jaisson and Rosenbaum (2018) measure the smoothness of volatility
from the moments of its log increments,

    m(q, lag) = mean |log sigma_{t+lag} - log sigma_t|^q   ~   lag^(q H),

and find ``H`` near 0.1, far below the 0.5 of a Brownian-driven volatility.
Cont and Das (2024) argue that the estimation error in realized volatility is
enough to produce such a value. The functions here compute the scaling, and
remove the part of it that the estimation error explains.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import polygamma

from .estimators import bipower_variation, realized_variance, subsample_returns, tripower_quarticity


def daily_measures(grid: pd.DataFrame, step: int = 5) -> pd.DataFrame:
    """Realized variance, bipower variation and quarticity ratio for each day of a price grid.

    ``grid`` is the (day x minute) table of log prices from
    :func:`jumps.data.to_daily_grid`; ``step`` is the sampling interval in
    minutes. ``kappa`` is ``TQ / BV^2``, the integrated quarticity over the
    squared integrated variance: 1 when volatility is flat within the day,
    larger when it moves.
    """
    r = subsample_returns(grid.to_numpy(), step)
    bv = bipower_variation(r)
    return pd.DataFrame({"rv": realized_variance(r), "bv": bv,
                         "kappa": tripower_quarticity(r) / bv**2, "n": r.shape[1]}, index=grid.index)


def log_volatility(rv: pd.Series, freq: str = "D") -> pd.Series:
    """``0.5 * log(rv)`` on a complete calendar, with NaN where a period is missing."""
    x = 0.5 * np.log(rv)
    return x.reindex(pd.date_range(x.index[0], x.index[-1], freq=freq))


def structure_function(x: pd.Series | np.ndarray, lags: np.ndarray, q: float = 2.0) -> np.ndarray:
    """``m(q, lag)``: mean of ``|x_{t+lag} - x_t|^q`` over all pairs that exist."""
    v = np.asarray(x, dtype=float)
    return np.array([np.nanmean(np.abs(v[lag:] - v[:-lag]) ** q) for lag in lags])


def scaling_exponents(x: pd.Series | np.ndarray, lags: np.ndarray, qs: list[float]) -> pd.DataFrame:
    """Slope ``zeta_q`` of ``log m(q, lag)`` on ``log lag`` for each ``q``, with the fit's R-squared."""
    rows = {}
    lx = np.log(lags)
    for q in qs:
        ly = np.log(structure_function(x, lags, q))
        slope, intercept = np.polyfit(lx, ly, 1)
        resid = ly - (slope * lx + intercept)
        rows[q] = {"zeta": slope, "H": slope / q, "r2": 1.0 - resid.var() / ly.var()}
    return pd.DataFrame(rows).T.rename_axis("q")


def hurst(x: pd.Series | np.ndarray, lags: np.ndarray, qs: list[float]) -> float:
    """``H`` as the slope of ``zeta_q`` against ``q``, through the origin."""
    z = scaling_exponents(x, lags, qs)["zeta"].to_numpy()
    q = np.asarray(qs, dtype=float)
    return float(np.sum(q * z) / np.sum(q * q))


def noise_variance(n: np.ndarray | float, kappa: np.ndarray | float = 1.0) -> np.ndarray:
    """Variance of the estimation error in a log realized volatility.

    A realized variance built from ``n`` returns with flat volatility is a
    scaled chi-squared with ``n`` degrees of freedom, so its log has variance
    ``trigamma(n / 2)``, close to ``2 / n``. When volatility moves within the
    window the effective sample is ``n / kappa``. The log volatility is half the
    log variance, hence the factor one quarter.
    """
    return 0.25 * polygamma(1, np.asarray(n, dtype=float) / (2.0 * np.asarray(kappa, dtype=float)))


def hurst_noise_corrected(x: pd.Series | np.ndarray, lags: np.ndarray, noise: float) -> tuple[float, float]:
    """``H`` from the second moment, before and after removing the estimation error.

    Independent errors of variance ``noise`` in each observation add ``2 * noise``
    to ``m(2, lag)`` at every lag. Returns the two slopes divided by two.
    """
    m2 = structure_function(x, lags, 2.0)
    lx = np.log(lags)
    raw = np.polyfit(lx, np.log(m2), 1)[0] / 2.0
    clean = m2 - 2.0 * noise
    ok = clean > 0
    corrected = np.polyfit(lx[ok], np.log(clean[ok]), 1)[0] / 2.0 if ok.sum() >= 3 else np.nan
    return float(raw), float(corrected)


def remove_periodic_mean(x: pd.Series, key: np.ndarray, breaks: list[str] | None = None) -> pd.Series:
    """Subtract the mean of ``x`` for each value of ``key``, separately on each sub-period.

    With ``key`` the day of the week this removes the weekend effect from a
    daily log-volatility; with the hour of the week it removes the intraweek
    rhythm of post 2 from an hourly one. The overall mean of each sub-period is
    kept.
    """
    key = np.asarray(key)
    tz = x.index.tz
    edges = ([x.index[0]] + [pd.Timestamp(b, tz=tz) for b in (breaks or [])]
             + [x.index[-1] + pd.Timedelta(seconds=1)])
    out = x.copy()
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = np.asarray((x.index >= lo) & (x.index < hi))
        part = x[m]
        out[m] = part - part.groupby(key[m]).transform("mean") + part.mean()
    return out


def hourly_measures(close: pd.Series) -> pd.DataFrame:
    """Realized variance and quarticity ratio of every full hour of 1-minute returns."""
    from .seasonality import regular_returns

    r = regular_returns(close, 1)
    hours = pd.date_range(r.index[0].ceil("h"), r.index[-1].floor("h") - pd.Timedelta(hours=1), freq="h")
    minutes = pd.date_range(hours[0] + pd.Timedelta(minutes=1), hours[-1] + pd.Timedelta(hours=1), freq="1min")
    block = r.reindex(minutes).to_numpy().reshape(-1, 60)
    good = np.isfinite(block).all(axis=1) & (np.abs(block).sum(axis=1) > 0)
    rv = np.full(len(hours), np.nan)
    kappa = np.full(len(hours), np.nan)
    rv[good] = realized_variance(block[good])
    with np.errstate(divide="ignore", invalid="ignore"):
        kappa[good] = tripower_quarticity(block[good]) / bipower_variation(block[good]) ** 2
    return pd.DataFrame({"rv": rv, "kappa": kappa, "n": 60}, index=hours)


def fractional_brownian_motion(n: int, hurst: float, rng: np.random.Generator) -> np.ndarray:
    """``n`` values of a fractional Brownian motion at times 1..n, by Cholesky factorisation.

    Exact, and fine for a few thousand points. ``hurst = 0.5`` gives a random walk.
    """
    t = np.arange(1, n + 1, dtype=float)
    cov = 0.5 * (t[:, None] ** (2 * hurst) + t[None, :] ** (2 * hurst)
                 - np.abs(t[:, None] - t[None, :]) ** (2 * hurst))
    return np.linalg.cholesky(cov) @ rng.standard_normal(n)


def simulate_log_volatility(kind: str, n_days: int, level_sd: float = 0.59,
                            daily_change_sd: float = 0.32, half_life: float = 20.0,
                            seed: int = 0) -> np.ndarray:
    """Daily log-volatility paths with a known answer, for the placebo.

    * ``"smooth"``: Brownian-driven and mean-reverting, an AR(1) with the given
      half-life in days and a stationary standard deviation of ``level_sd``.
      True ``H`` is 0.5.
    * ``"rough"``: a fractional Brownian motion with ``H = 0.1`` whose one-day
      change has standard deviation ``daily_change_sd``.
    """
    rng = np.random.default_rng(seed)
    if kind == "rough":
        return daily_change_sd * fractional_brownian_motion(n_days, 0.1, rng)
    if kind != "smooth":
        raise ValueError("kind must be 'smooth' or 'rough'")
    phi = 0.5 ** (1.0 / half_life)
    x = np.zeros(n_days)
    shocks = rng.standard_normal(n_days) * np.sqrt(1.0 - phi**2)
    x[0] = rng.standard_normal()
    for t in range(1, n_days):
        x[t] = phi * x[t - 1] + shocks[t]
    return level_sd * x


def measured_log_volatility(true_log_vol: np.ndarray, n_returns: int, kappa: float = 1.0,
                            seed: int = 0) -> np.ndarray:
    """Log realized volatility of each day, as estimated from ``n_returns`` intraday returns.

    The realized variance of a day is its true variance times a chi-squared
    with ``n_returns / kappa`` degrees of freedom, divided by that number:
    ``kappa = 1`` is flat volatility within the day, larger values mimic a
    volatility that moves. The only difference between output and input is the
    estimation error.
    """
    rng = np.random.default_rng(seed)
    dof = n_returns / kappa
    return true_log_vol + 0.5 * np.log(rng.chisquare(dof, size=len(true_log_vol)) / dof)
