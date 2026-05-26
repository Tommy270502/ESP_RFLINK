from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER_RE = re.compile(r"^(<<<<<<<|=======|>>>>>>>)", re.MULTILINE)
IGNORED_PARTS = {".git", ".pio", ".venv", "__pycache__", "node_modules", "dist"}
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".zip", ".gz", ".tar", ".bin", ".elf", ".hex",
    ".kicad_pcb", ".kicad_sch", ".kicad_pro",
    ".gbr", ".drl", ".gbl", ".gbs", ".gbo", ".gtl", ".gts", ".gto", ".gm1",
}


def main() -> int:
    found: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if IGNORED_PARTS.intersection(path.parts):
            continue
        if path.suffix.lower() in BINARY_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for match in MARKER_RE.finditer(text):
            line_num = text[:match.start()].count("\n") + 1
            found.append(f"{path.relative_to(ROOT)}:{line_num}: {match.group(0)}")

    if found:
        print("Conflict markers found:")
        for item in found:
            print(f"  {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
