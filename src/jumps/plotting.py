"""Shared figure style for the series, sized for LinkedIn (1200 x 1200 px)."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

FIGURES = Path(__file__).resolve().parents[2] / "figures"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"


def set_style() -> None:
    """Apply the series style to matplotlib."""
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "figure.dpi": 100, "savefig.dpi": 200,
        "font.family": "DejaVu Sans", "font.size": 11,
        "text.color": INK, "axes.labelcolor": INK_2,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelcolor": INK_2, "ytick.labelcolor": INK_2,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.grid.axis": "y",
        "grid.color": GRID, "grid.linewidth": 0.8,
        "lines.linewidth": 2.0, "lines.markersize": 7,
        "legend.frameon": False, "mathtext.fontset": "cm",
    })


def save(fig: plt.Figure, name: str) -> Path:
    """Save a figure to ``figures/<name>.png`` at 200 dpi."""
    FIGURES.mkdir(exist_ok=True)
    path = FIGURES / f"{name}.png"
    fig.savefig(path)
    return path


def titled(fig: plt.Figure, title: str, subtitle: str) -> None:
    """Left-aligned title and subtitle above the plot area."""
    fig.text(0.08, 0.955, title, fontsize=16, fontweight="bold", color=INK, va="top")
    fig.text(0.08, 0.905, subtitle, fontsize=11, color=INK_2, va="top")


def render_equation(latex: str, name: str, caption: str | None = None, fontsize: int = 26) -> Path:
    """Render one equation as an image, since LinkedIn does not display LaTeX."""
    fig = plt.figure(figsize=(6, 2.2))
    fig.text(0.5, 0.58 if caption else 0.5, f"${latex}$", fontsize=fontsize,
             ha="center", va="center", color=INK)
    if caption:
        fig.text(0.5, 0.14, caption, fontsize=11, ha="center", va="center", color=INK_2)
    path = save(fig, name)
    plt.close(fig)
    return path


def signature_plot(series: list[dict], labels: list[str], truth: list[dict] | None = None,
                   title: str = "", subtitle: str = "", ylabel: str = "") -> plt.Figure:
    """Line chart of a statistic against sampling interval.

    ``series`` items: ``{"name", "x", "y", "color", "marker"}`` where ``x`` holds
    positions into ``labels``. ``truth`` items: ``{"y", "color", "text"}`` draw
    dashed reference levels.
    """
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.subplots_adjust(left=0.11, right=0.80, top=0.80, bottom=0.11)
    for ref in truth or []:
        ax.axhline(ref["y"], color=ref["color"], lw=1.0, ls=(0, (4, 3)), alpha=0.7, zorder=1)
        ax.text(-0.3, ref["y"], ref["text"], fontsize=9, color=INK_2, va="bottom", ha="left")
    for s in series:
        ax.plot(s["x"], s["y"], color=s["color"], marker=s.get("marker", "o"),
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=s["name"], zorder=3)
        ax.annotate(s["name"], (s["x"][-1], s["y"][-1]), xytext=(10, s.get("dy", 0)),
                    textcoords="offset points", fontsize=10, color=INK, va="center")
    ax.set_xticks(range(len(labels)), labels)
    ax.set_xlim(-0.4, len(labels) - 0.6)
    ax.set_xlabel("Sampling interval")
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(decimals=0))
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.10), ncol=len(series),
              fontsize=9, handlelength=1.6, columnspacing=1.2, borderaxespad=0)
    titled(fig, title, subtitle)
    return fig


def two_clocks_plot(logp_fine: np.ndarray, dt_seconds: int, coarse_seconds: int,
                    event_index: int, title: str, subtitle: str) -> plt.Figure:
    """One intraday window on a coarse grid, then a zoom into one coarse interval.

    ``event_index`` is the coarse interval (0-based, within the window) to zoom into.
    """
    k = coarse_seconds // dt_seconds
    minutes = np.arange(len(logp_fine)) * dt_seconds / 60.0
    ret = 100.0 * (logp_fine - logp_fine[0])
    lo, hi = event_index * k, (event_index + 1) * k
    fig, axes = plt.subplots(2, 1, figsize=(6, 6))
    fig.subplots_adjust(left=0.12, right=0.95, top=0.80, bottom=0.10, hspace=0.42)

    axes[0].axvspan(minutes[lo], minutes[hi], color=GRID, alpha=0.7, lw=0, zorder=0)
    axes[0].plot(minutes[::k], ret[::k], color=ORANGE, marker="o",
                 markeredgecolor=SURFACE, markeredgewidth=1.5)
    axes[0].set_title(f"Sampled every {coarse_seconds // 60} minutes: it looks like a jump",
                      loc="left", fontsize=11, color=INK)
    axes[1].plot(minutes[lo : hi + 1], ret[lo : hi + 1], color=BLUE, lw=1.6)
    axes[1].set_title(f"Inside the shaded interval, every {dt_seconds} seconds: a continuous slide",
                      loc="left", fontsize=11, color=INK)
    axes[1].set_xlabel("Minutes")
    for ax in axes:
        ax.set_ylabel("Return (%)")
    titled(fig, title, subtitle)
    return fig
