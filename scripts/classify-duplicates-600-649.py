#!/usr/bin/env python3
"""Determine for each translated German paragraph whether it is a DUPLICATE of an
existing French paragraph in the same chapter (then it should be deleted) or a
genuinely missing paragraph (then keep the new translation).

Uses French token similarity between the new translation and every French
paragraph of the chapter."""
import json
import re
import sys
from pathlib import Path

OUT_DIR = Path(r"C:\Users\Marc\AppData\Local\Temp\opencode\pr-check")


def fr_tokens(s: str) -> list[str]:
    s = s.lower().replace("—", " ").replace("–", " ")
    return re.findall(r"[a-z0-9]+", s)


def sim(a: str, b: str) -> float:
    ta, tb = fr_tokens(a), fr_tokens(b)
    if not ta or not tb:
        return 0.0
    cnt: dict[str, int] = {}
    for t in ta:
        cnt[t] = cnt.get(t, 0) + 1
    same = 0
    for t in tb:
        if cnt.get(t, 0) > 0:
            same += 1
            cnt[t] -= 1
    return same / max(len(ta), len(tb))


def main() -> None:
    TH = 0.80
    tot_dup = 0
    tot_keep = 0
    for pr in range(600, 650):
        tp = OUT_DIR / f"{pr}-trans.json"
        if not tp.exists():
            continue
        trans = json.loads(tp.read_text(encoding="utf-8-sig"))
        fr = (OUT_DIR / f"{pr}-fr.txt").read_text(encoding="utf-8").split("\n")
        german_idx = {int(t.get("index", t.get("i"))) for t in trans}
        # french paragraphs that are not the german ones
        french_paras = [(j, p) for j, p in enumerate(fr) if j not in german_idx and p.strip()]
        dup_idx, keep_idx = [], []
        for t in trans:
            i = int(t.get("index", t.get("i")))
            fr_text = t["fr"]
            best = 0.0
            best_j = -1
            for j, p in french_paras:
                s = sim(fr_text, p)
                if s > best:
                    best = s
                    best_j = j
            if best >= TH:
                dup_idx.append((i, best_j, round(best, 2)))
            else:
                keep_idx.append(i)
        if dup_idx:
            tot_dup += len(dup_idx)
        tot_keep += len(keep_idx)
        print(f"PR {pr}: german={len(trans)} dup(delete)={len(dup_idx)} keep={len(keep_idx)}"
              + (f"  e.g. {dup_idx[:4]}" if dup_idx else ""))
    print(f"TOTAL dup to delete: {tot_dup}, keep translations: {tot_keep}")


if __name__ == "__main__":
    main()