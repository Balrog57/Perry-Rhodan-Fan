#!/usr/bin/env python3
"""Per-chapter translation QA: German text left in French files, missing/mismatched
numbers, chapter-marker counts, size ratios, encoding artifacts."""
import math
import re
import sys
from pathlib import Path

OUT_DIR = Path(r"C:\Users\Marc\AppData\Local\Temp\opencode\pr-check")

DE_FILLERS = (" der ", " und ", " die ", " das ", " von ", " nicht ", " ist ",
              " er ", " sie ", " es ", " mit ", " aus ", " auf ", " ihn ",
              " seinem ", " keinen ", " noch ", " über ", " ein ", " eine ")
FR_FILLERS = (" le ", " la ", " les ", " et ", " un ", " une ", " des ", " de ",
              " dans ", " sur ", " il ", " elle ", " ils ", " elles ", " pas ",
              " plus ", " pour ", " avec ", " ce ", " cette ", " que ", " qui ")


def german_score(s: str) -> float:
    s = s.lower()
    de = sum(s.count(w) for w in DE_FILLERS)
    fr = sum(s.count(w) for w in FR_FILLERS)
    total = de + fr
    return de / total if total else 0.0


def main() -> None:
    issues = []
    for issue in sorted(int(p.stem.split("-")[0]) for p in OUT_DIR.glob("*-fr.txt")):
        fr = (OUT_DIR / f"{issue}-fr.txt").read_text(encoding="utf-8").split("\n")
        de = (OUT_DIR / f"{issue}-de.txt").read_text(encoding="utf-8").split("\n")

        fr_chars = sum(len(p) for p in fr)
        de_chars = sum(len(p) for p in de)
        ratio = fr_chars / de_chars if de_chars else 0

        ff = sum(1 for p in fr if "\ufffd" in p)

        german_paras = []
        for i, p in enumerate(fr):
            if len(p.strip()) < 12:
                continue
            g = german_score(p)
            if g >= 0.55:
                german_paras.append((i, g, p[:110]))

        # short numeric markers like "1." in both
        de_markers = [i for i, p in enumerate(de) if re.fullmatch(r"\s*\d{1,3}\.\s*", p)]
        fr_markers = [i for i, p in enumerate(fr) if re.fullmatch(r"\s*\d{1,3}\.\s*", p)]

        flag = []
        if ratio < 0.82 or ratio > 1.10:
            flag.append(f"ratio={ratio:.2f}")
        if ff:
            flag.append(f"{ff}xU+FFFD")
        if len(de_markers) != len(fr_markers):
            flag.append(f"markers DE={len(de_markers)} FR={len(fr_markers)}")
        if len(german_paras) > 3:
            flag.append(f"{len(german_paras)} German-para")
        badge = ("FLAG " + ";".join(flag)) if flag else "ok"
        print(f"{issue:>4}  DE={de_chars:>7} FR={fr_chars:>7} ratio={ratio:5.2f}  "
              f"markers {len(de_markers)}/{len(fr_markers)}  GERM={len(german_paras):>3}  {badge}")
        if german_paras:
            for i, g, head in german_paras[:6]:
                print(f"        FR#{i} germ={g:.2f}: {head}")
            if len(german_paras) > 6:
                print(f"        ... and {len(german_paras) - 6} more")


if __name__ == "__main__":
    main()