"""Rewrite the header cell of every notebook from ``jumps.series``.

Usage: ``python tools/stamp_headers.py`` from the repo root. Only the first
cell of each ``notebooks/NN_*.ipynb`` is touched; outputs are left alone.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jumps.series import header_markdown  # noqa: E402


def main() -> None:
    notebooks = sorted((ROOT / "notebooks").glob("[0-9][0-9]_*.ipynb"))
    built = {p.stem for p in notebooks}
    for path in notebooks:
        nb = json.loads(path.read_text())
        first = nb["cells"][0]
        if first["cell_type"] != "markdown":
            raise SystemExit(f"{path.name}: first cell is not markdown, refusing to overwrite it")
        new = header_markdown(int(path.stem[:2]), built)
        old = first["source"] if isinstance(first["source"], str) else "".join(first["source"])
        if old != new:
            first["source"] = new
            path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
            print(f"stamped  {path.name}")
        else:
            print(f"current  {path.name}")


if __name__ == "__main__":
    main()
