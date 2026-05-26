from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", ".pio", ".venv", "__pycache__", "node_modules", "dist"}

BANNED_TERMS = [
    (re.compile(r"\bdesktop workbench\b", re.IGNORECASE), "desktop workbench", "local web workbench"),
    (re.compile(r"\bdesktop app\b", re.IGNORECASE), "desktop app", "local web workbench"),
    (re.compile(r"\bTkinter workbench\b", re.IGNORECASE), "Tkinter workbench", "local web workbench"),
    (re.compile(r"(?<![Ff]irmware )browser dashboard\b"), "browser dashboard (without 'firmware' prefix)", "firmware browser dashboard"),
]


def main() -> int:
    issues: list[str] = []

    for path in ROOT.rglob("*.md"):
        if IGNORED_PARTS.intersection(path.parts):
            continue
        if path.name in ("ROADMAP.md", "CLAUDE.md"):
            continue
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)

        for pattern, term, replacement in BANNED_TERMS:
            for match in pattern.finditer(text):
                line_num = text[:match.start()].count("\n") + 1
                issues.append(f"{rel}:{line_num}: found '{term}', use '{replacement}'")

    if issues:
        print("Docs consistency issues:")
        for item in issues:
            print(f"  {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
