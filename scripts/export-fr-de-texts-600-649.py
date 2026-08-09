#!/usr/bin/env python3
"""Export FR and DE chapter texts (one paragraph per line) plus a paragraph
alignment report, for translation verification of PR 600-649."""
import io
import re
import sys
import zipfile
from pathlib import Path

OUT_DIR = Path(r"C:\Users\Marc\AppData\Local\Temp\opencode\pr-check")
DOWNLOADS = Path(r"C:\Users\Marc\Downloads\Perry Rhodan Sammelband")
FR_EPUB = next(DOWNLOADS.glob("*French*.epub"))
DE_EPUB = next((DOWNLOADS / "Perry Rhodan Sammelband").glob("*.epub"))

MAPPING = {
    600: "020", 601: "042", 602: "064", 603: "086", 604: "090", 605: "092",
    606: "094", 607: "096", 608: "098", 609: "001", 610: "002", 611: "004",
    612: "006", 613: "008", 614: "010", 615: "012", 616: "014", 617: "016",
    618: "018", 619: "022", 620: "024", 621: "026", 622: "028", 623: "030",
    624: "032", 625: "034", 626: "036", 627: "038", 628: "040", 629: "044",
    630: "046", 631: "048", 632: "050", 633: "052", 634: "054", 635: "056",
    636: "058", 637: "060", 638: "062", 639: "066", 640: "068", 641: "070",
    642: "072", 643: "074", 644: "076", 645: "078", 646: "080", 647: "082",
    648: "084", 649: "088",
}

PARA_RE = re.compile(r"<p/>|<p[^>]*>(.*?)</p>", re.S)


def paragraphs(xhtml: str) -> list[str]:
    body_m = re.search(r"<body[^>]*>(.*)</body>", xhtml, re.S)
    body = body_m.group(1) if body_m else xhtml
    out = []
    pos = 0
    while True:
        m = PARA_RE.search(body, pos)
        if not m:
            break
        pos = m.end()
        if m.group(0) == "<p/>":
            out.append("")
            continue
        inner = re.sub(r"<[^>]+>", "", m.group(1))
        inner = (inner.replace("&amp;", "&").replace("&lt;", "<")
                 .replace("&gt;", ">").replace("&quot;", '"')
                 .replace("&#39;", "'").replace("&apos;", "'")
                 .replace("&#160;", " ").replace("&nbsp;", " "))
        out.append(inner)
    return out


def tokens(s: str) -> list[str]:
    s = s.lower().replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss")
    return re.findall(r"[a-z0-9]+", s)


def similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    counts: dict[str, int] = {}
    for t in ta:
        counts[t] = counts.get(t, 0) + 1
    same = 0
    for t in tb:
        if counts.get(t, 0) > 0:
            same += 1
            counts[t] -= 1
    return same / max(len(ta), len(tb))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report: list[str] = ["PR\tDEparas\tFRparas\tflaggedDE\tmedian"]
    with zipfile.ZipFile(FR_EPUB) as zfr, zipfile.ZipFile(DE_EPUB) as zde:
        for issue in sorted(MAPPING):
            split = MAPPING[issue]
            fr_text = zfr.read(f"OEBPS/Text/index_split_{split}.xhtml").decode("utf-8")
            de_text = zde.read(f"OEBPS/Text/index_split_{split}.xhtml").decode("utf-8")
            fr_paras = paragraphs(fr_text)
            de_paras = paragraphs(de_text)

            (OUT_DIR / f"{issue}-fr.txt").write_text("\n".join(fr_paras), encoding="utf-8")
            (OUT_DIR / f"{issue}-de.txt").write_text("\n".join(de_paras), encoding="utf-8")

            # Sliding-window alignment: a DE paragraph can only match FR ones
            # within +/- WINDOW lines of its own position.
            WINDOW = 30
            flagged = 0
            sims = []
            align_lines = []
            for i, de in enumerate(de_paras):
                if not de.strip():
                    continue
                best = 0.0
                best_j = -1
                lo, hi = max(0, i - WINDOW), min(len(fr_paras), i + WINDOW + 1)
                for j in range(lo, hi):
                    s = similarity(de, fr_paras[j])
                    if s > best:
                        best = s
                        best_j = j
                sims.append(best)
                flag = "LOW" if best < 0.4 else ""
                if flag:
                    flagged += 1
                align_lines.append(f"{i}\t{best_j}\t{best:.2f}\t{flag}")

            sims_sorted = sorted(sims)
            median = round(sims_sorted[len(sims_sorted) // 2], 2)
            (OUT_DIR / f"{issue}-align.tsv").write_text(
                "\n".join(align_lines), encoding="utf-8")
            report.append(f"{issue}\t{len(de_paras)}\t{len(fr_paras)}\t{flagged}\t{median}")
            print(f"EXPORT {issue} DE={len(de_paras)} FR={len(fr_paras)} "
                  f"flaggedDE={flagged} median={median}", flush=True)

    (OUT_DIR / "report.tsv").write_text("\n".join(report), encoding="utf-8")
    print("DONE.")


if __name__ == "__main__":
    main()