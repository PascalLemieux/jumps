"""Download 1-minute klines from Binance's public data archive.

No API key or account is needed: files come from https://data.binance.vision,
one zip per symbol and calendar month. Each month is cached locally as parquet,
so a second call reads from disk.

Example
-------
>>> from jumps.data import load_klines
>>> df = load_klines("BTCUSDT", "2023-01", "2024-12")
>>> df["close"].head()
"""

from __future__ import annotations

import io
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

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
    frames = []
    for month in months:
        if verbose:
            print(f"{symbol} {interval} {month}", end="\r")
        frames.append(download_month(symbol, month, interval, cache_dir))
    if verbose:
        print(f"{symbol} {interval}: {len(months)} months loaded" + " " * 10)
    return pd.concat(frames).sort_index()


def to_daily_grid(close: pd.Series, bars_per_day: int = 1440) -> pd.DataFrame:
    """Reshape a 1-minute close series into a (day x minute) table of log prices.

    The first column is the previous day's last close, so each row holds
    ``bars_per_day + 1`` prices and yields ``bars_per_day`` intraday returns.
    Gaps of up to five minutes (exchange maintenance) are forward filled;
    days with longer gaps are dropped.
    """
    import numpy as np

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
