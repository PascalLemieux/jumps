"""Download market data from public archives. No API key or account is needed.

* 1-minute klines and aggregated trades come from Binance's public archive at
  https://data.binance.vision.
* The DVOL implied-volatility index comes from Deribit's public API.

Everything is cached locally as parquet under ``data/``, so a second call reads
from disk.

Example
-------
>>> from jumps.data import load_klines, iter_agg_trades
>>> df = load_klines("BTCUSDT", "2023-01", "2024-12")
>>> df["close"].head()
>>> for day, trades in iter_agg_trades("BTCUSDT", "2026-10-01", "2026-10-07"):
...     print(day, len(trades))
"""

from __future__ import annotations

import io
import json
import sys
import urllib.error
import urllib.request
import zipfile
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

BASE_URL = "https://data.binance.vision/data/spot/monthly/klines"
DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "data"

COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "n_trades", "taker_buy_base", "taker_buy_quote", "ignore",
]
PRICE_COLUMNS = ["open", "high", "low", "close", "volume", "quote_volume"]


def _to_datetime(raw: pd.Series) -> pd.DatetimeIndex:
    """Convert Binance epoch stamps to UTC.

    Spot archives switched from milliseconds to microseconds in January 2025,
    so the unit is inferred from the magnitude of the stamp.
    """
    raw = raw.astype("int64")
    unit = "us" if raw.iloc[0] > 10**14 else "ms"
    return pd.DatetimeIndex(pd.to_datetime(raw, unit=unit, utc=True))


def _parse_month(payload: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        with zf.open(zf.namelist()[0]) as fh:
            df = pd.read_csv(fh, header=None, names=COLUMNS, low_memory=False)
    # Some archives carry a header row; drop it if present.
    if not str(df.iloc[0, 0]).isdigit():
        df = df.iloc[1:]
    df.index = _to_datetime(df["open_time"])
    df.index.name = "time"
    df = df[PRICE_COLUMNS + ["n_trades"]].astype("float64")
    return df[~df.index.duplicated()].sort_index()


def download_month(
    symbol: str,
    month: str,
    interval: str = "1m",
    cache_dir: Path | str = DEFAULT_CACHE,
    timeout: int = 60,
) -> pd.DataFrame:
    """Return one calendar month of klines, e.g. ``download_month("BTCUSDT", "2024-01")``."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"{symbol}-{interval}-{month}.parquet"
    if cached.exists():
        return pd.read_parquet(cached)

    url = f"{BASE_URL}/{symbol}/{interval}/{symbol}-{interval}-{month}.zip"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            payload = resp.read()
    except urllib.error.HTTPError as exc:
        raise FileNotFoundError(
            f"No archive at {url} (HTTP {exc.code}). Binance publishes a month "
            "only after it has ended; check the symbol and the date range."
        ) from exc

    df = _parse_month(payload)
    df.to_parquet(cached)
    return df


def load_klines(
    symbol: str = "BTCUSDT",
    start: str = "2023-01",
    end: str = "2024-12",
    interval: str = "1m",
    cache_dir: Path | str = DEFAULT_CACHE,
    verbose: bool = True,
) -> pd.DataFrame:
    """Return klines for every month from ``start`` to ``end`` inclusive (``YYYY-MM``)."""
    months = pd.period_range(start, end, freq="M").strftime("%Y-%m")
    progress = verbose and sys.stdout.isatty()  # keep executed notebooks free of progress lines
    frames = []
    for month in months:
        if progress:
            print(f"{symbol} {interval} {month}", end="\r")
        frames.append(download_month(symbol, month, interval, cache_dir))
    if verbose:
        print(f"{symbol} {interval}: {len(months)} months loaded")
    return pd.concat(frames).sort_index()


def to_daily_grid(close: pd.Series, bars_per_day: int = 1440) -> pd.DataFrame:
    """Reshape a 1-minute close series into a (day x minute) table of log prices.

    The first column is the previous day's last close, so each row holds
    ``bars_per_day + 1`` prices and yields ``bars_per_day`` intraday returns.
    Gaps of up to five minutes (exchange maintenance) are forward filled;
    days with longer gaps are dropped.
    """
    close = close.sort_index()
    full = pd.date_range(
        close.index[0].floor("D"),
        close.index[-1].ceil("D") - pd.Timedelta(minutes=1),
        freq="1min",
    )
    logp = np.log(close.reindex(full).ffill(limit=5))
    grid = logp.to_numpy().reshape(-1, bars_per_day)
    days = full[::bars_per_day]
    prev_close = np.r_[np.nan, grid[:-1, -1]]
    table = pd.DataFrame(np.column_stack([prev_close, grid]), index=days)
    return table.dropna()


# --------------------------------------------------------------------------
# Aggregated trades (tick data)
# --------------------------------------------------------------------------

AGG_TRADES_URL = "https://data.binance.vision/data/spot/daily/aggTrades"
AGG_COLUMNS = [
    "agg_id", "price", "qty", "first_id", "last_id", "time", "is_buyer_maker", "is_best_match",
]


def _fetch(url: str, timeout: int) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        raise FileNotFoundError(f"No archive at {url} (HTTP {exc.code}).") from exc


def download_agg_trades_day(
    symbol: str,
    day: str,
    cache_dir: Path | str = DEFAULT_CACHE,
    timeout: int = 180,
) -> pd.DataFrame:
    """One UTC day of Binance aggregated trades, e.g. ``("BTCUSDT", "2026-10-14")``.

    An aggregated trade merges the fills of one taker order that execute at the
    same price. Returns columns ``time_us`` (microseconds since the epoch, UTC),
    ``price``, ``qty`` and ``buyer_maker`` (True when the taker sold), in
    exchange order.
    """
    cache_dir = Path(cache_dir) / "aggTrades" / symbol
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"{symbol}-aggTrades-{day}.parquet"
    if cached.exists():
        return pd.read_parquet(cached)

    payload = _fetch(f"{AGG_TRADES_URL}/{symbol}/{symbol}-aggTrades-{day}.zip", timeout)
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        with zf.open(zf.namelist()[0]) as fh:
            raw = pd.read_csv(fh, header=None, names=AGG_COLUMNS, low_memory=False)
    if not str(raw.iloc[0, 0]).isdigit():  # header row in some archives
        raw = raw.iloc[1:]
    stamp = raw["time"].astype("int64").to_numpy()
    if stamp[0] < 10**14:  # milliseconds before 2025, microseconds after
        stamp = stamp * 1000
    df = pd.DataFrame({
        "time_us": stamp,
        "price": raw["price"].astype("float64").to_numpy(),
        "qty": raw["qty"].astype("float64").to_numpy(),
        "buyer_maker": raw["is_buyer_maker"].astype(str).str.lower().eq("true").to_numpy(),
    })
    df.to_parquet(cached, index=False)
    return df


def iter_agg_trades(
    symbol: str,
    start: str,
    end: str,
    cache_dir: Path | str = DEFAULT_CACHE,
    workers: int = 8,
) -> Iterator[tuple[pd.Timestamp, pd.DataFrame]]:
    """Yield ``(day, trades)`` for every UTC day from ``start`` to ``end`` inclusive.

    Missing days are downloaded in parallel first, then days are yielded in
    order, one at a time, so a month of BTC trades never sits in memory at once.
    """
    days = pd.date_range(start, end, freq="D")
    labels = [d.strftime("%Y-%m-%d") for d in days]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(lambda lab: download_agg_trades_day(symbol, lab, cache_dir) is None, labels))
    for day, lab in zip(days, labels):
        yield day.tz_localize("UTC"), download_agg_trades_day(symbol, lab, cache_dir)


# --------------------------------------------------------------------------
# Deribit DVOL (30-day implied volatility index)
# --------------------------------------------------------------------------

DVOL_URL = "https://www.deribit.com/api/v2/public/get_volatility_index_data"


def load_dvol(
    currency: str = "BTC",
    start: str = "2021-04-01",
    end: str | None = None,
    resolution_seconds: int = 3600,
    cache_dir: Path | str = DEFAULT_CACHE,
    timeout: int = 60,
) -> pd.DataFrame:
    """Deribit DVOL index candles (open, high, low, close), in annualised percent.

    DVOL is Deribit's 30-day implied volatility index, built from the option
    surface in the manner of the VIX. The public endpoint needs no key and
    returns 1,000 candles per call, so the history is paged backwards.
    """
    cache_dir = Path(cache_dir) / "dvol"
    cache_dir.mkdir(parents=True, exist_ok=True)
    end_ts = pd.Timestamp(end, tz="UTC") if end else pd.Timestamp.now(tz="UTC").floor("D")
    start_ts = pd.Timestamp(start, tz="UTC")
    cached = cache_dir / f"{currency}-DVOL-{resolution_seconds}-{start_ts:%Y%m%d}-{end_ts:%Y%m%d}.parquet"
    if cached.exists():
        return pd.read_parquet(cached)

    rows: list[list[float]] = []
    lo, hi = int(start_ts.timestamp() * 1000), int(end_ts.timestamp() * 1000)
    while hi > lo:
        url = (f"{DVOL_URL}?currency={currency}&start_timestamp={lo}&end_timestamp={hi}"
               f"&resolution={resolution_seconds}")
        result = json.loads(_fetch(url, timeout))["result"]
        if not result["data"]:
            break
        rows = result["data"] + rows
        if not result.get("continuation"):
            break
        hi = int(result["continuation"])
    df = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close"])
    df.index = pd.DatetimeIndex(pd.to_datetime(df.pop("time"), unit="ms", utc=True), name="time")
    df = df[~df.index.duplicated()].sort_index()
    df.to_parquet(cached)
    return df
