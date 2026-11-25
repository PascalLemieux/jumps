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


def event_panel(events, window_minutes: int, context_minutes: int,
                title: str, subtitle: str) -> plt.Figure:
    """Small multiples of the largest ``window_minutes`` moves, one panel per event.

    ``events`` is the frame returned by :func:`jumps.estimators.largest_moves`.
    Each panel draws the 1-minute path (blue) and, over the shaded window, the
    straight segment a ``window_minutes`` bar would show (orange).
    """
    n = len(events)
    ncols = 2
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(6, 6))
    fig.subplots_adjust(left=0.10, right=0.97, top=0.76, bottom=0.08, hspace=0.75, wspace=0.30)
    minutes = np.arange(-context_minutes, window_minutes + context_minutes + 1)
    for ax, (start, ev) in zip(axes.ravel(), events.iterrows()):
        path = ev["path_pct"]
        ax.axvspan(0, window_minutes, color=GRID, alpha=0.6, lw=0, zorder=0)
        ax.plot(minutes[: len(path)], path, color=BLUE, lw=1.4, zorder=3)
        ax.plot([0, window_minutes], [path[context_minutes], path[context_minutes + window_minutes]],
                color=ORANGE, lw=1.4, ls=(0, (3, 2)), marker="o", markersize=5,
                markeredgecolor=SURFACE, markeredgewidth=1.0, zorder=4)
        move = 100 * ev["window_return"]
        ax.set_title(f"{start:%d %b %Y}, {start:%H:%M} UTC\n"
                     f"{move:+.1f}% in {window_minutes} min, biggest minute {100 * ev['largest_minute_share']:.0f}%",
                     loc="left", fontsize=8, color=INK, linespacing=1.35)
        ax.set_xticks([-context_minutes, 0, window_minutes, window_minutes + context_minutes])
        ax.tick_params(labelsize=7.5, length=2)
        ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(decimals=0))
        ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(4))
        ax.grid(axis="y", lw=0.6)
    for ax in axes.ravel()[n:]:
        ax.axis("off")
    for ax in axes[-1]:
        ax.set_xlabel("Minutes from window start", fontsize=8, color=INK_2)
    titled(fig, title, subtitle)
    handles = [mpl.lines.Line2D([], [], color=BLUE, lw=1.4, label="1-minute path"),
               mpl.lines.Line2D([], [], color=ORANGE, lw=1.4, ls=(0, (3, 2)), marker="o", markersize=5,
                                markeredgecolor=SURFACE, label=f"the same move as one {window_minutes}-minute bar")]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.075, 0.865), ncol=2,
               fontsize=8.5, frameon=False, handlelength=2.0, columnspacing=1.5)
    return fig


def sampling_curves(curves: dict, labels: list[str], title: str, subtitle: str,
                    top_label: str = "Share of variance attributed to jumps",
                    bottom_label: str = "Days flagged by the BNS test at 1%") -> plt.Figure:
    """Two stacked panels: jump share and days flagged, against sampling interval.

    ``curves`` maps a series name to ``{"x", "jump_share", "days_flagged", "color", "marker"}``
    with values in percent and ``x`` positions into ``labels``.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 6), sharex=True)
    fig.subplots_adjust(left=0.12, right=0.84, top=0.77, bottom=0.09, hspace=0.32)
    for ax, key, ylab in ((ax1, "jump_share", top_label), (ax2, "days_flagged", bottom_label)):
        for name, c in curves.items():
            ax.plot(c["x"], c[key], color=c["color"], marker=c.get("marker", "o"),
                    markeredgecolor=SURFACE, markeredgewidth=1.5, label=name, zorder=3)
        ax.set_title(ylab, loc="left", fontsize=10.5, color=INK)
        ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(decimals=0))
        ax.set_ylim(bottom=0)
        _end_labels(ax, {name: (list(c["x"])[-1], list(c[key])[-1]) for name, c in curves.items()})
    ax2.axhline(1, color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=1)
    ax2.text(len(labels) - 0.65, 1, "nominal 1%", fontsize=8.5, color=INK_2, va="bottom", ha="right")
    ax2.set_xticks(range(len(labels)), labels)
    ax2.set_xlim(-0.4, len(labels) - 0.6)
    ax2.set_xlabel("Sampling interval")
    ax1.legend(loc="upper left", bbox_to_anchor=(0.0, 1.36), ncol=len(curves), fontsize=9,
               handlelength=1.6, columnspacing=1.2, borderaxespad=0)
    titled(fig, title, subtitle)
    return fig


def worlds_plot(series: list[dict], labels: list[str], title: str, subtitle: str) -> plt.Figure:
    """Jump share against sampling interval for simulated worlds, with an empirical overlay.

    ``series`` items: ``{"name", "x", "y", "color", "marker", "ls", "dy"}``; ``y`` in percent.
    """
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.subplots_adjust(left=0.12, right=0.78, top=0.76, bottom=0.10)
    for s in series:
        ax.plot(s["x"], s["y"], color=s["color"], marker=s.get("marker", "o"), ls=s.get("ls", "-"),
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=s["name"], zorder=3)
        i = s.get("label_at", -1)
        ax.annotate(s["name"], (list(s["x"])[i], list(s["y"])[i]), xytext=(9, s.get("dy", 0)),
                    textcoords="offset points", fontsize=9.5, color=INK, va="center")
    ax.set_xticks(range(len(labels)), labels)
    ax.set_xlim(-0.4, len(labels) - 0.6)
    ax.set_ylim(-3, 103)
    ax.set_xlabel("Sampling interval")
    ax.set_ylabel("Estimated jump share of variance")
    ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(decimals=0))
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.14), ncol=2, fontsize=9,
              handlelength=1.8, columnspacing=1.2, borderaxespad=0)
    titled(fig, title, subtitle)
    return fig


def _end_labels(ax, points: dict, min_gap_pt: float = 11.0) -> None:
    """Direct labels at the last point of each series, pushed apart if they collide."""
    names = sorted(points, key=lambda k: points[k][1])
    y_pix = [ax.transData.transform((points[k][0], points[k][1]))[1] for k in names]
    offsets = [0.0] * len(names)
    dpi_scale = ax.figure.dpi / 72.0
    for j in range(1, len(names)):
        gap = (y_pix[j] + offsets[j]) - (y_pix[j - 1] + offsets[j - 1])
        if gap < min_gap_pt * dpi_scale:
            offsets[j] += min_gap_pt * dpi_scale - gap
    for name, off in zip(names, offsets):
        x, y = points[name]
        ax.annotate(name, (x, y), xytext=(9, off / dpi_scale), textcoords="offset points",
                    fontsize=9.5, color=INK, va="center")


# --------------------------------------------------------------------------
# Post 2: intraday seasonality
# --------------------------------------------------------------------------

def before_after_bars(before, after, labels, title: str, subtitle: str,
                      before_name: str = "Before", after_name: str = "After",
                      xlabel: str = "", ylabel: str = "", tick_every: int = 3,
                      notes: list[dict] | None = None) -> plt.Figure:
    """Paired bars for two counts over the same categories, e.g. hours of the day.

    ``notes`` items: ``{"x", "y", "text"}`` place a short annotation in data units.
    """
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.subplots_adjust(left=0.12, right=0.96, top=0.78, bottom=0.11)
    w = 0.40
    ax.bar(x - w / 2, before, width=w - 0.04, color=AXIS, label=before_name, zorder=3)
    ax.bar(x + w / 2, after, width=w - 0.04, color=BLUE, label=after_name, zorder=3)
    ax.set_xticks(x[::tick_every], [labels[i] for i in range(0, len(labels), tick_every)])
    ax.set_xlim(-0.7, len(labels) - 0.3)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", length=0)
    for n in notes or []:
        ax.annotate(n["text"], (n["x"], n["y"]), xytext=n.get("offset", (0, 6)),
                    textcoords="offset points", fontsize=9, color=INK_2,
                    ha=n.get("ha", "center"), va="bottom")
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.10), ncol=2, fontsize=9.5,
              handlelength=1.2, columnspacing=1.6, borderaxespad=0)
    titled(fig, title, subtitle)
    return fig


def week_panels(panels: list[dict], minutes: int, title: str, subtitle: str,
                xlabel: str = "Day of the week", notes: list[dict] | None = None) -> plt.Figure:
    """One stacked panel per period: a statistic for every slot of the week.

    ``panels`` items: ``{"name", "y", "color"}`` with one value per slot, Monday
    first. ``notes`` items: ``{"panel", "x", "y", "text", "offset", "ha"}``.
    """
    per_day = 1440 // minutes
    fig, axes = plt.subplots(len(panels), 1, figsize=(6, 6), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.10, right=0.96, top=0.80, bottom=0.10, hspace=0.30)
    axes = np.atleast_1d(axes)
    top = max(float(np.nanmax(p["y"])) for p in panels)
    for ax, p in zip(axes, panels):
        for d in range(1, 7):
            ax.axvline(d * per_day, color=GRID, lw=0.8, zorder=1)
        ax.axhline(1.0, color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=2)
        ax.plot(np.arange(len(p["y"])), p["y"], color=p["color"], lw=0.9, zorder=3)
        ax.set_title(p["name"], loc="left", fontsize=10.5, color=INK)
        ax.set_ylim(0, top * 1.12)
        ax.set_xlim(0, 7 * per_day)
        ax.tick_params(axis="x", length=0)
        ax.grid(axis="y", lw=0.6)
    for n in notes or []:
        axes[n["panel"]].annotate(n["text"], (n["x"], n["y"]), xytext=n.get("offset", (0, 6)),
                                  textcoords="offset points", fontsize=8.5, color=INK_2,
                                  ha=n.get("ha", "center"), va="bottom")
    axes[-1].set_xticks((np.arange(7) + 0.5) * per_day, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    axes[-1].set_xlabel(xlabel)
    titled(fig, title, subtitle)
    return fig


def slot_panels(panels: list[dict], labels: list[str], title: str, subtitle: str,
                marks: list[dict] | None = None, tick_every: int = 12, xlabel: str = "") -> plt.Figure:
    """Stacked bar panels over the same intraday slots, sharing both axes.

    ``panels`` items: ``{"name", "y", "color"}``. ``marks`` items: ``{"slot", "text"}``
    label a slot in every panel.
    """
    n = len(panels)
    fig, axes = plt.subplots(n, 1, figsize=(6, 6), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.11, right=0.96, top=0.80, bottom=0.11, hspace=0.30)
    x = np.arange(len(labels))
    top = max(float(np.max(p["y"])) for p in panels)
    for ax, p in zip(np.atleast_1d(axes), panels):
        ax.bar(x, p["y"], width=0.8, color=p["color"], zorder=3)
        ax.set_title(p["name"], loc="left", fontsize=10.5, color=INK)
        ax.set_ylim(0, top * 1.18)
        ax.tick_params(axis="x", length=0)
        for m in marks or []:
            ax.axvline(m["slot"], color=MUTED, lw=0.8, ls=(0, (2, 2)), zorder=1)
            ax.text(m["slot"], top * 1.16, m["text"], fontsize=8.5, color=INK_2, ha="center", va="top",
                    bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5))
    last = np.atleast_1d(axes)[-1]
    last.set_xticks(x[::tick_every], [labels[i] for i in range(0, len(labels), tick_every)])
    last.set_xlim(-1, len(labels))
    last.set_xlabel(xlabel)
    titled(fig, title, subtitle)
    return fig
