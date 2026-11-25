"""Intraday jump detection and the intraweek seasonality of volatility.

* :func:`lee_mykland` is the test of Lee and Mykland (2008): each return is
  divided by a local volatility estimate built from bipower variation over a
  trailing window, and flagged when it exceeds a Gumbel threshold.
* :func:`periodicity` estimates the seasonality factor of volatility for each
  slot of the week with the estimators of Boudt, Croux and Laurent (2011): the
  standard deviation (not robust), the shortest half, and the weighted standard
  deviation built on it.

Dividing the test statistic by the seasonality factor gives the filtered test
of Boudt, Croux and Laurent, their equation (3.4).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

C = np.sqrt(2.0 / np.pi)  # E|Z| for a standard normal, the constant c of Lee and Mykland


def regular_returns(close: pd.Series, minutes: int = 5) -> pd.Series:
    """Log returns on a regular ``minutes`` grid from a 1-minute close series.

    A return is NaN when either of its two prices is missing, so a data gap
    never shows up as one large return.
    """
    close = close.sort_index()
    full = pd.date_range(close.index[0].ceil(f"{minutes}min"),
                         close.index[-1].floor(f"{minutes}min"), freq="1min")
    logp = np.log(close.reindex(full))
    # The bar stamped hh:mm closes at the end of that minute, so the price at the
    # end of a 5-minute interval is the close of its last 1-minute bar.
    last = logp[(full.minute % minutes) == (minutes - 1)]
    r = last.diff()
    r.index = r.index + pd.Timedelta(minutes=1)  # stamp each return at the end of its interval
    return r.iloc[1:]


def default_window(per_day: int, days_per_year: int = 252) -> int:
    """Smallest window K allowed by Lee and Mykland: ``ceil(sqrt(days_per_year * per_day))``.

    With their 252 days and 288 five-minute returns a day this gives the K = 270
    they recommend.
    """
    return int(np.ceil(np.sqrt(days_per_year * per_day)))


def local_volatility(r: pd.Series, window: int, min_fraction: float = 0.9) -> pd.Series:
    """Trailing bipower estimate of the standard deviation of one return.

    Equation (8) of Lee and Mykland, rescaled by pi/2 so that it estimates the
    standard deviation itself:
    ``s_i^2 = (pi/2) / (K - 2) * sum_{j=i-K+2}^{i-1} |r_j| |r_{j-1}|``.
    The return being tested is not in its own window. Windows with fewer than
    ``min_fraction`` of their products available return NaN.
    """
    a = r.abs()
    prod = a * a.shift(1)
    mean = prod.shift(1).rolling(window - 2, min_periods=int(min_fraction * (window - 2))).mean()
    return np.sqrt(mean / C**2)


def gumbel_threshold(n: int, alpha: float = 0.01) -> float:
    """Level exceeded with probability ``alpha`` by the largest of ``n`` absolute standard normals.

    ``-log(-log(1 - alpha)) * b_n + a_n`` with the constants of Lee and Mykland's
    Lemma 1, written for a statistic with unit variance. For n = 288 and
    alpha = 1% it is 4.305.
    """
    root = np.sqrt(2.0 * np.log(n))
    a_n = root - (np.log(np.pi) + np.log(np.log(n))) / (2.0 * root)
    b_n = 1.0 / root
    return float(-np.log(-np.log(1.0 - alpha)) * b_n + a_n)


def week_slot(index: pd.DatetimeIndex, minutes: int = 5, tz: str = "UTC") -> np.ndarray:
    """Slot of the week of each interval end, on the clock of ``tz``.

    Slot 0 is Monday 00:00 to 00:05. Using ``"America/New_York"`` keeps the US
    cash open and US data releases in the same slot all year, whereas on the UTC
    clock they move by an hour with daylight saving.
    """
    start = (index - pd.Timedelta(minutes=minutes)).tz_convert(tz)
    return np.asarray((start.dayofweek * 1440 + start.hour * 60 + start.minute) // minutes)


def shortest_half(x: np.ndarray) -> float:
    """Shortest half scale of Rousseeuw and Leroy, consistent under normality.

    ``0.741`` times the length of the shortest interval that covers
    ``floor(n/2) + 1`` of the sorted observations.
    """
    x = np.sort(x[np.isfinite(x)])
    h = len(x) // 2 + 1
    return 0.741 * float(np.min(x[h - 1:] - x[: len(x) - h + 1]))


def periodicity(standardised: pd.Series, slot: np.ndarray, n_slots: int) -> pd.DataFrame:
    """Seasonality factor of volatility for every slot of the cycle.

    ``standardised`` holds returns divided by their local volatility. Returns a
    frame indexed by slot with three estimates of the factor, each normalised
    so that its square averages one over the cycle:

    * ``sd``: root mean square, efficient without jumps, ruined by one of them;
    * ``shorth``: shortest half, the most robust and the least efficient;
    * ``wsd``: weighted standard deviation, ``sqrt(1.081 * mean of x^2)`` over
      the observations with ``(x / shorth)^2 <= 6.635``, the 99% quantile of a
      chi-squared with one degree of freedom.
    """
    x = standardised.to_numpy()
    ok = np.isfinite(x)
    order = np.argsort(slot[ok], kind="stable")
    xs, ss = x[ok][order], slot[ok][order]
    bounds = np.searchsorted(ss, np.arange(n_slots + 1))
    sd = np.full(n_slots, np.nan)
    sh = np.full(n_slots, np.nan)
    for k in range(n_slots):
        g = xs[bounds[k]: bounds[k + 1]]
        if len(g) > 10:
            sd[k] = np.sqrt(np.mean(g**2))
            sh[k] = shortest_half(g)
    norm = lambda v: v / np.sqrt(np.nanmean(v**2))  # noqa: E731
    f_sh = norm(sh)
    wsd = np.full(n_slots, np.nan)
    for k in range(n_slots):
        g = xs[bounds[k]: bounds[k + 1]]
        if len(g) > 10:
            keep = (g / f_sh[k]) ** 2 <= 6.635
            wsd[k] = np.sqrt(1.081 * np.mean(g[keep] ** 2))
    return pd.DataFrame({"sd": norm(sd), "shorth": f_sh, "wsd": norm(wsd)},
                        index=pd.RangeIndex(n_slots, name="slot"))


def seasonal_factor(
    standardised: pd.Series,
    slot: np.ndarray,
    n_slots: int,
    breaks: list[str] | None = None,
    estimator: str = "wsd",
) -> tuple[pd.Series, dict[str, pd.DataFrame]]:
    """Seasonality factor of every return, estimated separately on each sub-period.

    ``breaks`` are the dates at which a new sub-period starts, e.g.
    ``["2021-01-01", "2024-01-01"]`` for three periods. Returns the factor
    aligned with ``standardised`` and the per-slot estimates of each period,
    keyed by the period's first date.
    """
    idx = standardised.index
    edges = [idx[0]] + [pd.Timestamp(b, tz="UTC") for b in (breaks or [])] + [idx[-1] + pd.Timedelta(seconds=1)]
    factor = pd.Series(np.nan, index=idx)
    tables: dict[str, pd.DataFrame] = {}
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = np.asarray((idx >= lo) & (idx < hi))
        table = periodicity(standardised[m], slot[m], n_slots)
        tables[f"{lo:%Y-%m-%d}"] = table
        factor[m] = table[estimator].to_numpy()[slot[m]]
    return factor, tables


def lee_mykland(
    r: pd.Series,
    window: int,
    per_block: int,
    alpha: float = 0.01,
    factor: pd.Series | np.ndarray | None = None,
) -> pd.DataFrame:
    """Lee and Mykland (2008) jump test, optionally filtered for seasonality.

    Parameters
    ----------
    r
        Returns on a regular grid.
    window
        K, the number of returns in the trailing volatility window.
    per_block
        Number of returns over which the test controls its size, usually one
        day. The threshold is the level the largest of ``per_block`` statistics
        exceeds with probability ``alpha`` when there is no jump.
    factor
        Seasonality factor of each return. When given, the statistic is
        ``|r_i| / (f_i * s_i)``, the filtered test of Boudt, Croux and Laurent.

    Returns a frame with the local volatility ``s``, the statistic ``J`` (which
    is ``c |L(i)|`` in Lee and Mykland's notation, absolute standard normal when
    there is no jump) and the boolean ``jump``.
    """
    s = local_volatility(r, window)
    j = r.abs() / s
    if factor is not None:
        j = j / np.asarray(factor)
    threshold = gumbel_threshold(per_block, alpha)
    out = pd.DataFrame({"r": r, "s": s, "J": j})
    out["jump"] = out["J"] > threshold
    out.attrs["threshold"] = threshold
    return out


def standardised_returns(
    close: pd.Series,
    minutes: int,
    breaks: list[str] | None = None,
    tz: str = "America/New_York",
) -> pd.Series:
    """Bar returns in units of their local volatility, with the weekly seasonality removed.

    The seasonality factor is estimated on 5-minute returns as in post 2
    (weighted standard deviation, one factor per slot of the week, per
    sub-period). Each return is divided by the factor of the 5-minute slots it
    covers, then by the trailing bipower volatility of the deseasonalised
    returns over the Lee-Mykland window. Without jumps the result is roughly
    standard normal.
    """
    r5 = regular_returns(close, 5)
    base = lee_mykland(r5, default_window(288), 288)
    f5, _ = seasonal_factor(r5 / base["s"], week_slot(r5.index, 5, tz), 7 * 288, breaks)
    r = regular_returns(close, minutes)
    if minutes < 5:
        f = f5.reindex(r.index.ceil("5min")).to_numpy()
    else:
        f = np.sqrt((f5**2).rolling(minutes // 5).mean()).reindex(r.index).to_numpy()
    adjusted = r / f
    return adjusted / local_volatility(adjusted, default_window(1440 // minutes))
