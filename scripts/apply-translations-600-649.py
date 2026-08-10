#!/usr/bin/env python3
"""Final application: rebuild the site chapter markdown (de-NNNN.md) so that
- duplicate German paragraphs (whose French twin already exists in the text) are DELETED,
- genuinely missing German paragraphs are REPLACED by the new French translations."""
import json
import re
import sys
from pathlib import Path

OUT_DIR = Path(r"C:\Users\Marc\AppData\Local\Temp\opencode\pr-check")
CHAP = Path(r"C:\Users\Marc\Documents\1G1R\_Programmation\Perry Rhodan Fan\src\content\chapitres")


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


def build_md_body(paras: list[str]) -> str:
    non_empty = 0
    start = 0
    for i, p in enumerate(paras):
        if p.strip() == "":
            continue
        non_empty += 1
        if non_empty == 3:
            start = i + 1
            break
    while start < len(paras) and paras[start].strip() == "":
        start += 1
    lines: list[str] = []
    for p in paras[start:]:
        t = p.strip()
        if t == "":
            lines.append("")
        elif t == "*":
            lines.append("* * *")
        else:
            lines.append(t)
    out: list[str] = []
    prev_blank = False
    for l in lines:
        if l == "":
            if not prev_blank:
                out.append("")
            prev_blank = True
        else:
            out.append(l)
            prev_blank = False
    return "\n".join(out)


def main() -> None:
    TH = 0.80
    for pr in range(600, 650):
        tp = OUT_DIR / f"{pr}-trans.json"
        if not tp.exists():
            print(f"{pr}: no trans file")
            continue
        trans = json.loads(tp.read_text(encoding="utf-8-sig"))
        fr = (OUT_DIR / f"{pr}-fr.txt").read_text(encoding="utf-8").split("\n")
        german_idx = {int(t.get("index", t.get("i"))) for t in trans}
        trans_by_idx = {int(t.get("index", t.get("i"))): t["fr"] for t in trans}
        french_paras = [(j, p) for j, p in enumerate(fr) if j not in german_idx and p.strip()]

        dup: set[int] = set()
        keep: set[int] = set()
        for i in german_idx:
            fr_text = trans_by_idx[i]
            best = max((sim(fr_text, p) for _, p in french_paras), default=0.0)
            (dup if best >= TH else keep).add(i)

        final: list[str] = []
        n_keep = n_del = 0
        for i, p in enumerate(fr):
            if i in dup:
                n_del += 1
                continue
            if i in keep:
                final.append(trans_by_idx[i])
                n_keep += 1
                continue
            final.append(p)

        body = build_md_body(final)
        md = CHAP / f"de-{pr:04d}.md"
        text = md.read_text(encoding="utf-8")
        m = re.match(r"(?s)^(---\r?\n.*?\r?\n---)\r?\n", text)
        fm = m.group(1).replace("\r\n", "\n").replace("\r", "\n")
        new = fm + "\n\n" + body + "\n"
        md.write_text(new, encoding="utf-8")
        print(f"{pr}: deletes={n_del} keeps={n_keep} body={len(body)} chars")


if __name__ == "__main__":
    main()