#!/usr/bin/env python3
"""Apply per-chapter DELETE lists (from the review fix files) to the site md files."""
import re
import sys
from pathlib import Path

OUT = Path(r"C:\Users\Marc\AppData\Local\Temp\opencode\pr-check")
CHAP = Path(r"C:\Users\Marc\Documents\1G1R\_Programmation\Perry Rhodan Fan\src\content\chapitres")

# chapter -> fix file
FIX_FILES = {
    610: "fix-610.txt",
    611: "611-fix.txt",
    613: "613-fix.txt",
    614: "614-fix.txt",
    615: "615-fix.txt",
    616: "616-fix.txt",
    617: "617-fix.txt",
}

LINE_RE = re.compile(r"DELETE\s*[:|]\s*(\d+)(?:\s*-\s*(\d+))?")


def parse_fix(path: Path) -> list[list[int]]:
    """Return list of line ranges (inclusive) to delete."""
    ranges = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        m = LINE_RE.match(line.strip())
        if not m:
            continue
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        ranges.append([a, b])
    return ranges


def main() -> None:
    for pr in sorted(FIX_FILES):
        fp = OUT / FIX_FILES[pr]
        if not fp.exists():
            print(f"{pr}: no fix file {FIX_FILES[pr]}")
            continue
        ranges = parse_fix(fp)
        md = CHAP / f"de-{pr:04d}.md"
        lines = md.read_text(encoding="utf-8").splitlines(keepends=True)
        n = len(lines)
        # expand to a set of 0-based indices
        todel: set[int] = set()
        for a, b in ranges:
            if a < 1 or b > n:
                print(f"  {pr}: range {a}-{b} out of bounds (file {n} lines)")
                continue
            for i in range(a, b + 1):
                todel.add(i - 1)
        removed = []
        for i in sorted(todel, reverse=True):
            removed.append(lines[i].rstrip("\n"))
            del lines[i]
        md.write_text("".join(lines), encoding="utf-8")
        print(f"{pr}: requested ranges={len(ranges)} deleted_lines={len(removed)}")
        for r in removed[:8]:
            print(f"    - {r[:80]}")
        if len(removed) > 8:
            print(f"    ... and {len(removed)-8} more")


if __name__ == "__main__":
    main()