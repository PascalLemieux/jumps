"""The series at a glance: the bio, the list of posts and the notebook header.

Every notebook opens with the same header cell. It is generated here, so the
bio, the links and the table of posts are written once. After editing this
file, run ``python tools/stamp_headers.py`` to refresh the first cell of every
notebook.
"""

from __future__ import annotations

LINKEDIN = "https://linkedin.com/in/pascal-lemieux"
GITHUB = "https://github.com/PascalLemieux/jumps"

BIO = (
    "Pascal Lemieux is a quant with 15+ years across J.P. Morgan, RBC, Société Générale and "
    "First Abu Dhabi Bank, spanning structured products, derivatives pricing and volatility "
    "modelling. He now focuses on digital-asset derivatives: crypto options, volatility surfaces "
    "and hedging, including deep reinforcement learning for hedging and execution, work he began "
    "as co-founder of Affresco. M.Sc. Financial Mathematics, Bayes Business School."
)

PITCH = (
    "This series tests what the jump literature claims against crypto market data, from 1-minute "
    "bars to tick trades. Every result is reproducible from the code in this repo. Every post asks "
    "the same question of a different effect: **is it real, or is it the measurement?**"
)

# (number, title, notebook stem or None when the notebook is not built yet)
POSTS: list[tuple[int, str, str | None]] = [
    (1, 'Most "jumps" are not jumps', "01_jumps_vs_vol_bursts"),
    (2, "Intraday seasonality and false jumps", "02_intraday_seasonality"),
    (3, "Bid-ask bounce and microstructure noise", "03_microstructure_noise"),
    (4, "Finite or infinite activity", "04_jump_activity"),
    (5, "What jump activity does to your hedge", "05_hedging_error"),
    (6, "Is volatility rough?", "06_rough_volatility"),
    (7, "Jumps or roughness in the smile?", None),
    (8, "The jump risk premium", None),
    (9, "Hedging with self-exciting jumps", None),
]


def header_markdown(number: int, built: set[str] | None = None) -> str:
    """Markdown for the first cell of notebook ``number``.

    ``built`` is the set of notebook stems that exist, so only those are linked.
    """
    title = next(t for n, t, _ in POSTS if n == number)
    rows = []
    for n, t, stem in POSTS:
        if n == number:
            rows.append(f"| **{n}** | **{t}** |")
        elif stem and (built is None or stem in built):
            rows.append(f"| {n} | [{t}]({stem}.ipynb) |")
        else:
            rows.append(f"| {n} | {t} |")
    return "\n".join([
        f"# {title}",
        "",
        f"**Jumps in financial time series, post {number} of {len(POSTS)}**",
        "",
        f"> {BIO}",
        ">",
        f"> [LinkedIn]({LINKEDIN}) · [GitHub]({GITHUB}) · [The series]({GITHUB}#the-series)",
        "",
        PITCH,
        "",
        "| # | Post |",
        "|:-:|------|",
        *rows,
    ])


def footer_markdown() -> str:
    """Closing line shared by every notebook."""
    return (
        "---\n\n"
        f"*Code, data loaders and figures: [github.com/PascalLemieux/jumps]({GITHUB}). "
        f"Comments and corrections welcome on [LinkedIn]({LINKEDIN}).*"
    )
