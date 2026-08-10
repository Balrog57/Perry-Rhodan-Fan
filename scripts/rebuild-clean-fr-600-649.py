#!/usr/bin/env python3
"""FINAL REBUILD for de-NNNN.md (600-649).

Established by the 50 audits: the French EPUB text contains the complete French
translation; German paragraphs are duplicates (their French twin exists in the
file); the machine-added translations are also duplicates, EXCEPT the
audit-confirmed TRUE GAPS where the French was genuinely missing.

Rebuild = original French paragraphs (fr.txt) with:
  - German paragraphs removed (identified by >=0.70 token overlap with the
    German text file; the French names like Yüan/Ära/HÜ don't match German),
  - French near-duplicate paragraphs removed (keep first occurrence),
  - audit-confirmed TRUE GAP translations inserted at their original position.

TRUE_GAPS below = audit "KEEP / vraie lacune" verdicts, translations taken from
trans.json (audit-validated) or hardcoded where the audits proposed French.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

OUT_DIR = Path(r"C:\Users\Marc\AppData\Local\Temp\opencode\pr-check")
CHAP = Path(r"C:\Users\Marc\Documents\1G1R\_Programmation\Perry Rhodan Fan\src\content\chapitres")

# ---------------------------------------------------------------- TRUE GAPS
# fr.txt index -> translation source: None means "use trans.json entry"
TRUE_GAPS: dict[int, dict[int, str | None]] = {
    602: {686: None},
    607: {402: None, 1471: None},
    608: {412: None},
    609: {706: None},
    612: {377: None, 378: None, 419: None, 756: None, 987: None, 991: None},
    613: {383: None, 572: None},
    614: {
        560: "Anti-ES resta dans l'attente.",
        565: "« Nous pourrons en discuter plus tard », tempéra Anti-ES.",
    },
    615: {1314: None},
    629: {
        80: "« Il n'avait, du reste, guère besoin d'en dire plus. »",
        89: None, 102: None, 107: None, 119: None,
        101: "Rhodan comprit que Heltamosch était triste.",
    },
    632: {123: None, 192: None},
    636: {274: None, 799: None, 1348: None},
    639: {419: None},
    641: {
        786: None, 787: None, 788: None, 792: None, 793: None, 794: None,
        795: None, 796: None, 797: None, 798: None, 799: None, 800: None,
        801: None, 802: None, 804: None, 805: None, 806: None,
    },
    642: {379: None},
}


def toks(s: str) -> list[str]:
    return re.findall(r"[a-zäöüß0-9]+", s.lower())


def main() -> None:
    for pr in range(600, 650):
        fr = (OUT_DIR / f"{pr}-fr.txt").read_text(encoding="utf-8").split("\n")
        de_list = [d.strip() for d in (OUT_DIR / f"{pr}-de.txt").read_text(encoding="utf-8").split("\n") if d.strip()]
        de_hists = [Counter(toks(d)) for d in de_list]
        de_lens = [sum(h.values()) for h in de_hists]

        # trans.json (audit-validated translations)
        trans: dict[int, str] = {}
        tp = OUT_DIR / f"{pr}-trans.json"
        if tp.exists():
            for it in json.loads(tp.read_text(encoding="utf-8-sig")):
                idx = int(it.get("index", it.get("i")))
                trans[idx] = it["fr"]

        # German index set (>=0.70 overlap with some German paragraph)
        german: set[int] = set()
        for i, p in enumerate(fr):
            t = p.strip()
            if not t or len(t) < 14:
                continue
            hist = Counter(toks(t))
            ln = sum(hist.values())
            best = 0.0
            for j in range(len(de_hists)):
                lj = de_lens[j]
                if lj == 0 or min(ln, lj) / max(ln, lj) < 0.4:
                    continue
                s = sum((hist & de_hists[j]).values()) / max(ln, lj)
                if s > best:
                    best = s
                if best >= 0.98:
                    break
            if best >= 0.70:
                german.add(i)

        gaps = TRUE_GAPS.get(pr, {})
        # resolve translations
        gap_tr: dict[int, str] = {}
        for idx, tr in gaps.items():
            if tr is not None:
                gap_tr[idx] = tr
            elif idx in trans:
                gap_tr[idx] = trans[idx]
            else:
                print(f"  !! {pr} gap {idx}: no translation available")

        # Build final French list
        final: list[str] = []
        seen: list[str] = []
        n_de = n_dup = n_gap = 0
        for i, p in enumerate(fr):
            t = p.strip()
            if t == "":
                final.append(p)
                continue
            if i in german:
                if i in gap_tr:
                    final.append(gap_tr[i])
                    n_gap += 1
                else:
                    n_de += 1  # duplicate German -> removed (French twin exists)
                continue
            # French near-duplicate removal (exact normalized match, window 40)
            if t and len(t) > 25:
                n = re.sub(r"[^a-z0-9]", "", t.lower())
                dup = any(re.sub(r"[^a-z0-9]", "", s.lower()) == n for s in seen[-60:])
                if dup:
                    n_dup += 1
                    continue
            seen.append(p)
            final.append(p)

        # write md with proper paragraph spacing: separate every paragraph
        # (and every scene separator) with a blank line so the rendered text
        # does not merge into a single block.
        processed = []
        for x in final:
            if x.strip() == "":
                processed.append("")
            elif x.strip() == "*":
                processed.append("* * *")
            else:
                processed.append(x.strip())

        spaced = []
        for i, line in enumerate(processed):
            spaced.append(line)
            if i < len(processed) - 1 and line.strip() and processed[i + 1].strip():
                spaced.append("")

        body = "\n".join(spaced)
        # collapse 3+ consecutive blank lines into a single blank line
        body = re.sub(r"\n{3,}", "\n\n", body)
        md = CHAP / f"de-{pr:04d}.md"
        text = md.read_text(encoding="utf-8")
        m = re.match(r"(?s)^(---\r?\n.*?\r?\n---)\r?\n", text)
        fm = m.group(1).replace("\r\n", "\n").replace("\r", "\n")
        md.write_text(fm + "\n\n" + body + "\n", encoding="utf-8")
        print(f"{pr}: de_removed={n_de} fr_dups={n_dup} gaps={n_gap} body={len(body)}")


if __name__ == "__main__":
    main()