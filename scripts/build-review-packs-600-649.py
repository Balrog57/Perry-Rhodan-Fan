#!/usr/bin/env python3
"""Generate per-chapter review packs for the final full FR<->DE verification:
for each chapter, list the indices of the NEWLY ADDED translations (keeps) and
the German original at those indices, so a reviewer can verify fidelity.
Writes pr-check/NNNN-review.txt"""
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
    for pr in range(600, 650):
        tp = OUT_DIR / f"{pr}-trans.json"
        if not tp.exists():
            continue
        trans = json.loads(tp.read_text(encoding="utf-8-sig"))
        fr = (OUT_DIR / f"{pr}-fr.txt").read_text(encoding="utf-8").split("\n")
        german_idx = {int(t.get("index", t.get("i"))) for t in trans}
        trans_by_idx = {int(t.get("index", t.get("i"))): t["fr"] for t in trans}
        french_paras = [(j, p) for j, p in enumerate(fr) if j not in german_idx and p.strip()]
        keep = []
        for i in sorted(german_idx):
            best = max((sim(trans_by_idx[i], p) for _, p in french_paras), default=0.0)
            if best < TH:
                keep.append(i)
        lines = [f"# PR {pr}: {len(keep)} newly translated paragraphs to verify against German"]
        for i in keep:
            lines.append(f"## index {i}")
            lines.append(f"GERMAN: {fr[i]}")
            lines.append(f"FRENCH (added): {trans_by_idx[i]}")
            lines.append("")
        (OUT_DIR / f"{pr}-review.txt").write_text("\n".join(lines), encoding="utf-8")
        print(f"PR {pr}: review pack with {len(keep)} keeps")


if __name__ == "__main__":
    main()