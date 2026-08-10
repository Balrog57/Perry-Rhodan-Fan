#!/usr/bin/env python3
"""Detect untranslated German paragraphs in the French chapter texts and export
them as per-chapter JSON lists for manual translation: {idx, text}."""
import json
import re
import sys
from pathlib import Path

OUT_DIR = Path(r"C:\Users\Marc\AppData\Local\Temp\opencode\pr-check")

# German filler words (with spaces) vs French fillers.
DE_FILLERS = (
    " der ", " und ", " die ", " das ", " von ", " nicht ", " ist ", " er ",
    " sie ", " es ", " mit ", " aus ", " auf ", " ihn ", " seinem ", " keinen ",
    " über ", " ein ", " eine ", " einen ", " auch ", " aber ", " nur ", " wie ",
    " noch ", " schon ", " dann ", " zum ", " zur ", " dem ", " den ", " war ",
    " wurde ", " hatte ", " haben ", " waren ", " würden ", " gegen ",
)
FR_FILLERS = (
    " le ", " la ", " les ", " des ", " de ", " un ", " une ", " du ", " dans ",
    " sur ", " il ", " elle ", " ils ", " elles ", " pas ", " plus ", " pour ",
    " avec ", " que ", " qui ", " est ", " sont ", " et ", " lui ", " mais ",
    " ne ", " se ", " au ", " aux ", " on ", " tous ", " tout ", " une ",
)

GERMAN_WORDS = (
    "der ", "und ", "die ", "das ", "von ", "nicht ", "ist ", "mit ", "eine ",
    "auf ", "den ", "er ", "sie ", "es ", "aus ", "ich ", "wir ", "ihr ",
    "sein ", "waren ", "wird ", "daß ", "über ", "auch ", "noch ", "schon ",
    "dieser ", "diese ", "dieses ", "etwas ", "wieder ", "zur ", "zum ",
    "einen ", "keine ", "nur ", "aber ", "wie ", "nach ", "um ", "vor ",
    "sich ", "gegen ", "durch ", "wir ", "mehr ", "war ", "hat ", "haben ",
)


def german_score(s: str) -> float:
    low = s.lower()
    de = sum(low.count(w) for w in DE_FILLERS)
    fr = sum(low.count(w) for w in FR_FILLERS)
    tot = de + fr
    return de / tot if tot else 0.0


def main() -> None:
    total_germ = 0
    for pr in sorted(int(p.stem.split("-")[0]) for p in OUT_DIR.glob("*-fr.txt")):
        fr = (OUT_DIR / f"{pr}-fr.txt").read_text(encoding="utf-8").split("\n")
        hits = []
        for i, p in enumerate(fr):
            if len(p.strip()) < 12:
                continue
            g = german_score(p)
            is_german = g >= 0.62
            if not is_german and g >= 0.5:
                # borderline: check a German-words signal
                low = p.lower()
                n_de = sum(low.count(w) for w in GERMAN_WORDS)
                if n_de >= 4:
                    is_german = True
            if is_german:
                hits.append({"i": i, "text": p})
        if hits:
            chars = sum(len(h["text"]) for h in hits)
            (OUT_DIR / f"{pr}-german.json").write_text(
                json.dumps(hits, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"PR {pr}: {len(hits)} paragraphs, {chars} chars ({chars / sum(len(x) for x in fr) * 100:.2f}% of chapter)")
        else:
            print(f"PR {pr}: none")


if __name__ == "__main__":
    main()