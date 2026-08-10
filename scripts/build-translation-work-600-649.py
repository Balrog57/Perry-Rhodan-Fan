#!/usr/bin/env python3
"""Build per-chapter translation work files: for each untranslated German
paragraph, provide previous/next French context and the German paragraph.
Output: pr-check/NNNN-work.txt  (one block per paragraph, 'I::' index marker)"""
import json
import sys
from pathlib import Path

OUT_DIR = Path(r"C:\Users\Marc\AppData\Local\Temp\opencode\pr-check")


def clip(s: str, n: int = 220) -> str:
    return s if len(s) <= n else s[:n] + "…"


def main() -> None:
    for pr in sorted(int(p.stem.split("-")[0]) for p in OUT_DIR.glob("*-german.json")):
        germ = json.loads((OUT_DIR / f"{pr}-german.json").read_text(encoding="utf-8"))
        fr = (OUT_DIR / f"{pr}-fr.txt").read_text(encoding="utf-8").split("\n")
        de = (OUT_DIR / f"{pr}-de.txt").read_text(encoding="utf-8").split("\n")
        if not germ:
            continue
        blocks = []
        for h in germ:
            i = h["i"]
            prev_fr = next((fr[j] for j in range(i - 1, -1, -1) if fr[j].strip()), "")
            next_fr = next((fr[j] for j in range(i + 1, len(fr)) if fr[j].strip()), "")
            # German counterpart (same position in the DE file, fallback: search)
            de_para = de[i] if i < len(de) and de[i].strip() else ""
            if not de_para:
                match = next((x for x in de if x.strip() and x.strip()[:40] == h["text"].strip()[:40]), "")
                de_para = match
            blocks.append(
                f"### paragraph index {i}\n"
                f"[FR-context before]: {clip(prev_fr)}\n"
                f"[GERMAN paragraph to translate]: {h['text']}\n"
                f"[German original (reference)]: {de_para}\n"
                f"[FR-context after]: {clip(next_fr)}\n"
            )
        (OUT_DIR / f"{pr}-work.txt").write_text("\n".join(blocks), encoding="utf-8")
        print(f"PR {pr}: {len(germ)} paragraphs -> {pr}-work.txt")


if __name__ == "__main__":
    main()