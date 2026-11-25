"""Tick data, microstructure noise and noise-robust realized measures.

The observed log price of a trade is modelled as the efficient price plus
noise, ``Y_i = X_i + u_i``. The functions here measure the noise (Roll spread,
first-order autocovariance), show what it does to realized variance (the
volatility signature), and remove it by pre-averaging.

The pre-averaged estimators follow Christensen, Oomen and Podolskij (2014),
equations (8) to (11) and (21), which build on Jacod, Li, Mykland, Podolskij
and Vetter (2009) and Podolskij and Vetter (2009).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .seasonality import default_window, gumbel_threshold

US_PER_DAY = 86_400 * 10**6


def to_ticks(trades: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Observation times (microseconds) and log prices, one per distinct timestamp.

    Records that share a timestamp are the fills of one order walking through
    several price levels. They are collapsed into a single observation at the
    last price, so that one order is one tick.
    """
    t = trades["time_us"].to_numpy()
    last = np.r_[t[1:] != t[:-1], True]
    return t[last], np.log(trades["price"].to_numpy()[last])


def roll_spread(logp: np.ndarray) -> float:
    """Roll (1984) implied spread, as a fraction of the price.

    ``2 * sqrt(-cov(dp_t, dp_{t-1}))``, defined when the first-order
    autocovariance of trade-to-trade returns is negative, NaN otherwise.
    """
    r = np.diff(logp)
    cov = np.mean((r[1:] - r[1:].mean()) * (r[:-1] - r[:-1].mean()))
    return 2.0 * np.sqrt(-cov) if cov < 0 else np.nan


def noise_variance(logp: np.ndarray) -> float:
    """Variance of the noise from the first-order autocovariance of tick returns.

    ``-1/(N-1) * sum r_i r_{i-1}``, the estimator of Oomen (2006) used by
    Christensen, Oomen and Podolskij, equation (11). It can be negative in a
    small sample when the bounce is weak.
    """
    r = np.diff(logp)
    return float(-np.sum(r[1:] * r[:-1]) / (len(r) - 1))


def preaveraged_returns(logp: np.ndarray, k: int) -> np.ndarray:
    """Returns between adjacent local averages of ``k/2`` prices, equation (8).

    ``r*_i = (mean of Y_{i+k/2..i+k-1}) - (mean of Y_{i..i+k/2-1})``, divided by
    two, for every start ``i``. ``k`` must be even. Bounce flips sign from one
    trade to the next and cancels in the averages; a jump shifts the level and
    survives.
    """
    if k % 2:
        raise ValueError("k must be even")
    c = np.r_[0.0, np.cumsum(logp)]
    half = k // 2
    first = c[half: len(logp) - half + 1] - c[: len(logp) - k + 1]
    second = c[k:] - c[half: len(logp) - half + 1]
    return (second - first) / k


def preaveraging_window(n_returns: int, theta: float = 1.0) -> int:
    """Even window ``K`` closest to ``theta * sqrt(N)``, at least 2."""
    k = int(round(theta * np.sqrt(n_returns) / 2.0)) * 2
    return max(k, 2)


def preaveraged_measures(logp: np.ndarray, theta: float = 1.0) -> dict[str, float]:
    """Noise-robust realized variance and bipower variation for one day of ticks.

    Equations (9) and (10) of Christensen, Oomen and Podolskij with
    ``psi_K = (1 + 2/K^2) / 12`` and the bias correction
    ``omega^2 / (theta^2 psi_K)``. ``theta`` is recomputed from the even ``K``
    actually used. Also returns the raw tick-level RV and BV for comparison.
    """
    r = np.diff(logp)
    n = len(r)
    k = preaveraging_window(n, theta)
    th = k / np.sqrt(n)
    psi = (1.0 + 2.0 / k**2) / 12.0
    w2 = noise_variance(logp)
    bias = w2 / (th**2 * psi)
    rs = np.abs(preaveraged_returns(logp, k))
    rv_star = n / (n - k + 2) / (k * psi) * np.sum(rs**2) - bias
    bv_star = n / (n - 2 * k + 2) / (k * psi) * (np.pi / 2.0) * np.sum(rs[k:] * rs[:-k]) - bias
    a = np.abs(r)
    return {
        "n": n, "k": k, "omega2": w2,
        "rv": float(np.sum(r**2)),
        "bv": float(n / (n - 1) * (np.pi / 2.0) * np.sum(a[1:] * a[:-1])),
        "rv_star": float(rv_star), "bv_star": float(bv_star),
    }


def previous_tick(time_us: np.ndarray, logp: np.ndarray, day_start_us: int, seconds: float) -> np.ndarray:
    """Log prices on a clock grid over one UTC day, by previous-tick sampling.

    Grid points before the first trade of the day are dropped.
    """
    step = int(seconds * 10**6)
    grid = day_start_us + np.arange(0, US_PER_DAY + 1, step, dtype=np.int64)
    idx = np.searchsorted(time_us, grid, side="right") - 1
    return logp[idx[idx >= 0]]


def rv_bv(logp_grid: np.ndarray) -> tuple[float, float]:
    """Realized variance and bipower variation of a sampled price path."""
    r = np.diff(logp_grid)
    n = len(r)
    a = np.abs(r)
    return float(np.sum(r**2)), float(n / (n - 1) * (np.pi / 2.0) * np.sum(a[1:] * a[:-1]))


def lee_mykland_flags(returns: np.ndarray, window: int, per_block: int, alpha: float = 0.01) -> np.ndarray:
    """Lee and Mykland statistic on a plain array of returns; True where a jump is flagged.

    The local volatility of return ``i`` is the bipower variation of the
    ``window`` returns before it. The threshold controls the size over
    ``per_block`` returns. Returns without a full window, or with a window that
    contains no price change at all, are not tested.
    """
    a = np.abs(returns)
    c = np.r_[0.0, np.cumsum(a[1:] * a[:-1])]        # c[m] = sum of the first m products
    i = np.arange(window, len(returns))
    s2 = (np.pi / 2.0) * (c[i - 1] - c[i - window + 1]) / (window - 2)
    flags = np.zeros(len(returns), dtype=bool)
    ok = s2 > 0
    flags[i[ok]] = a[i[ok]] / np.sqrt(s2[ok]) > gumbel_threshold(per_block, alpha)
    return flags


def nonoverlapping_preaveraged(logp: np.ndarray, k: int) -> np.ndarray:
    """Pre-averaged returns over adjacent, non-overlapping blocks of ``k`` ticks."""
    return preaveraged_returns(logp, k)[::k]


def tick_profile(
    symbol: str,
    start: str,
    end: str,
    intervals: dict[str, float],
    thetas: tuple[float, ...] = (0.5, 1.0, 2.0),
) -> pd.DataFrame:
    """One row per UTC day: noise diagnostics and realized measures at every clock.

    Columns: number of ticks, share of zero tick returns, autocorrelation of
    tick returns at lags 1 and 5, autocorrelation of trade signs, Roll spread,
    noise variance, tick size relative to the price, tick-level ``rv`` and
    ``bv``, pre-averaged ``rv_star_<theta>`` and ``bv_star_<theta>``, and
    ``rv_<label>`` / ``bv_<label>`` for each clock interval in ``intervals``
    (label to seconds).
    """
    from .data import iter_agg_trades

    rows = []
    for day, trades in iter_agg_trades(symbol, start, end):
        t, logp = to_ticks(trades)
        r = np.diff(logp)
        d = r - r.mean()
        price = trades["price"].to_numpy()
        step = np.abs(np.diff(price))
        sign = np.where(trades["buyer_maker"].to_numpy(), -1.0, 1.0)
        row = {
            "day": day, "records": len(trades), "ticks": len(logp),
            "zero_share": float(np.mean(r == 0)),
            "ac1": float(np.mean(d[1:] * d[:-1]) / np.mean(d * d)),
            "ac5": float(np.mean(d[5:] * d[:-5]) / np.mean(d * d)),
            "sign_ac1": float(np.corrcoef(sign[1:], sign[:-1])[0, 1]),
            "roll": roll_spread(logp),
            "tick_size": float(step[step > 0].min() / np.median(price)),
        }
        for th in thetas:
            m = preaveraged_measures(logp, th)
            row[f"rv_star_{th}"], row[f"bv_star_{th}"] = m["rv_star"], m["bv_star"]
        row |= {"omega2": m["omega2"], "rv": m["rv"], "bv": m["bv"]}
        d0 = int(day.timestamp() * 10**6)
        for label, seconds in intervals.items():
            row[f"rv_{label}"], row[f"bv_{label}"] = rv_bv(previous_tick(t, logp, d0, seconds))
        rows.append(row)
    return pd.DataFrame(rows).set_index("day")


def tick_detections(
    symbol: str,
    start: str,
    end: str,
    thetas: tuple[float, ...] = (0.5, 1.0, 2.0),
    alpha: float = 0.01,
) -> dict[str, float]:
    """Lee and Mykland detections per day at three clocks, on the same trades.

    * 5-minute bars, with their K = 270;
    * raw tick returns;
    * non-overlapping pre-averaged tick returns, for each ``theta``.

    Days are chained into one series, since the market never closes. Each test
    controls its size at ``alpha`` per day. For each clock the result also gives
    the share of that clock's realized variance carried by the flagged returns.
    """
    from .data import iter_agg_trades

    ticks, bars, n_days = [], [], 0
    for day, trades in iter_agg_trades(symbol, start, end):
        t, logp = to_ticks(trades)
        ticks.append(logp)
        bars.append(previous_tick(t, logp, int(day.timestamp() * 10**6), 300.0)[:-1])
        n_days += 1
    logp = np.concatenate(ticks)

    def run(returns: np.ndarray, per_day: float, window: int | None = None) -> tuple[float, float]:
        window = window or default_window(int(per_day))
        flags = lee_mykland_flags(returns, window, int(per_day), alpha)
        return flags.sum() / n_days, float(np.sum(returns[flags] ** 2) / np.sum(returns**2))

    r_tick = np.diff(logp)
    per_day = len(r_tick) / n_days
    out = {"ticks_per_day": per_day}
    out["bars_per_day"], out["bars_jv"] = run(np.diff(np.concatenate(bars)), 288, 270)
    out["raw_per_day"], out["raw_jv"] = run(r_tick, per_day)
    for th in thetas:
        k = preaveraging_window(int(per_day), th)
        r_star = nonoverlapping_preaveraged(logp, k)
        out[f"pre_per_day_{th}"], out[f"pre_jv_{th}"] = run(r_star, len(r_star) / n_days)
        if th == 1.0:
            out["block_ticks"] = k
            out["blocks_per_day"] = len(r_star) / n_days
    return out


def clock_prices(symbol: str, start: str, end: str, seconds: list[float]) -> dict[float, np.ndarray]:
    """Log prices on clock grids over the whole period, by previous-tick sampling.

    Days are chained, so the grids run without a break from the first full
    interval after the first trade to the end of the last day. Every grid starts
    at the same instant, a multiple of the coarsest interval.
    """
    from .data import iter_agg_trades

    times, prices = [], []
    for _, trades in iter_agg_trades(symbol, start, end):
        t, logp = to_ticks(trades)
        times.append(t)
        prices.append(logp)
    t, logp = np.concatenate(times), np.concatenate(prices)
    coarse = int(max(seconds) * 10**6)
    first = (t[0] // coarse + 1) * coarse
    last = int((pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)).timestamp() * 10**6)
    out = {}
    for s in seconds:
        grid = np.arange(first, last + 1, int(s * 10**6), dtype=np.int64)
        out[s] = logp[np.searchsorted(t, grid, side="right") - 1]
    return out
