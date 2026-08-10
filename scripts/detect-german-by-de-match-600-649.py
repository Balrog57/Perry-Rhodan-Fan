#!/usr/bin/env python3
"""Identify German paragraphs in the French EPUB by matching against the German
text file (token overlap). High overlap => the paragraph is a German duplicate.
Writes pr-check/NNNN-german-de-match.json = {index: best_overlap}"""
import re
import sys
from collections import Counter
from pathlib import Path

OUT = Path(r"C:\Users\Marc\AppData\Local\Temp\opencode\pr-check")


def toks(s: str) -> list[str]:
    return re.findall(r"[a-zäöüß0-9]+", s.lower())


def overlap(a_hist: dict, la: int, b_hist: dict, lb: int) -> float:
    inter = sum((a_hist & b_hist).values())
    return inter / max(la, lb)


def main() -> None:
    TH = 0.70
    for pr in range(600, 650):
        fr = (OUT / f"{pr}-fr.txt").read_text(encoding="utf-8").split("\n")
        de = [d.strip() for d in (OUT / f"{pr}-de.txt").read_text(encoding="utf-8").split("\n") if d.strip()]
        de_idx = []
        de_len = []
        for d in de:
            t = toks(d)
            de_idx.append(Counter(t))
            de_len.append(len(t))
        results = {}
        for i, p in enumerate(fr):
            t = p.strip()
            if not t or len(t) < 14:
                continue
            hist = Counter(toks(t))
            ln = sum(hist.values())
            best = 0.0
            # iterate in chunks to stay fast; candidate filtering by length ratio
            for j in range(len(de_idx)):
                lj = de_len[j]
                if lj == 0:
                    continue
                ratio = min(ln, lj) / max(ln, lj)
                if ratio < 0.4:
                    continue
                s = overlap(hist, ln, de_idx[j], lj)
                if s > best:
                    best = s
                if best >= 0.98:
                    break
            if best >= TH:
                results[i] = round(best, 2)
        (OUT / f"{pr}-german-de-match.json").write_text(
            "{" + ",".join(f'"{k}":{v}' for k, v in sorted(results.items())) + "}",
            encoding="utf-8")
        print(f"{pr}: german={len(results)}")


if __name__ == "__main__":
    main()