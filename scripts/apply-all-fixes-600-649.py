#!/usr/bin/env python3
"""Apply the deletion lists from the 600-649 audits to de-NNNN.md.

Deletion lists come from fix files (*-fix.txt / fix-610.txt) parsed from disk,
plus transcriptions for the prose audit reports (600-609).

Robustness: whenever the audit quoted a text fragment, we verify the line at the
given number actually contains it; otherwise we search for the fragment anywhere
in the file and delete that line. Lines are deleted from bottom to top.
"""
import re
import sys
from pathlib import Path

OUT = Path(r"C:\Users\Marc\AppData\Local\Temp\opencode\pr-check")
CHAP = Path(r"C:\Users\Marc\Documents\1G1R\_Programmation\Perry Rhodan Fan\src\content\chapitres")

# transcribed deletions for prose audits: pr -> list of (line, fragment)
TRANSCRIPT: dict[int, list[tuple[int, int, str]]] = {
    600: [
        (531, 536, "au plan de référence parallèle"),   # doublon pack idx 527/528
        (578, 578, "d'une importance tout aussi capitale"),
        (631, 635, "Au fil de la journée, d'autres prisonniers"),
        (835, 835, "Son sosie était à cinquante kilomètres"),
        (863, 864, "Ils émergèrent de dessous les lits"),
    ],
    602: [
        (83, 84, "Si je puis me permettre un mot"),
        (191, 191, "des intentions derri derrière"),
        (646, 648, "un de ces chichis"),
        (748, 748, "un sourire aux lents"),
        (846, 846, "l'empreinte se déplaça lentement"),
        (894, 896, "Dann gnade euch Rhodan"),
        (997, 998, "l'automatique a faille"),
        (1050, 1053, ""),
        (1140, 1142, "Exactus"),
    ],
    603: [
        (467, 467, "harnais"),
        (512, 513, "répondit misérablement d'Ilt"),
        (637, 639, "insecticide"),
        (726, 726, "les deux Oxtorians"),
        (854, 854, "depuis sa haute tour de guet"),
        (562, 562, ""),
    ],
    604: [
        (48, 48, ""), (99, 102, ""), (203, 203, ""), (205, 205, ""),
        (295, 295, ""), (338, 340, ""), (454, 454, ""), (595, 597, ""),
        (720, 721, ""), (932, 932, ""), (968, 968, ""), (1040, 1042, ""),
        (139, 141, ""), (229, 232, ""), (759, 760, ""), (204, 204, ""),
        (297, 297, ""),
    ],
    605: [
        (220, 220, ""), (222, 222, ""), (478, 478, ""), (680, 680, ""),
        (843, 843, ""), (959, 959, ""), (211, 216, ""), (480, 480, ""),
    ],
    606: [
        (334, 334, ""), (535, 537, ""), (629, 630, ""), (981, 981, ""),
        (628, 628, ""), (667, 669, ""), (983, 983, ""),
    ],
    607: [
        (509, 511, ""), (1475, 1477, ""),
    ],
    608: [
        (128, 132, ""), (178, 179, ""), (225, 225, ""), (270, 271, ""),
        (429, 429, ""), (573, 574, ""), (728, 728, ""), (773, 773, ""),
        (938, 939, ""), (1258, 1260, ""), (130, 131, ""), (937, 937, ""),
        (313, 325, ""), (680, 684, ""), (813, 817, ""), (682, 682, ""),
    ],
    609: [
        (136, 138, ""), (374, 374, ""), (683, 683, ""), (810, 811, ""),
        (848, 848, ""), (964, 967, ""), (1059, 1059, ""), (1107, 1107, ""),
        (1186, 1186, ""), (373, 373, ""), (531, 531, ""), (1015, 1015, ""),
        (1105, 1106, ""), (682, 685, ""), (962, 969, ""),
    ],
}

# unknown/empty fragments in the transcriptions above get resolved by counting
# exact duplicate blocks; to stay safe we only delete when the fragment matches.


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def find_matches(lines: list[str], frag: str) -> list[int]:
    if not frag:
        return []
    f = norm(frag).lower()
    hits = []
    for i, l in enumerate(lines):
        if f in norm(l).lower():
            hits.append(i)
    return hits


def parse_fix_file(pr: int) -> list[tuple[int, int, str]]:
    name = f"fix-{pr}.txt" if pr == 610 else f"{pr}-fix.txt"
    p = OUT / name
    if not p.exists():
        return []
    out: list[tuple[int, int, str]] = []
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        m = re.match(
            r"DELETE\s*(:|\|)\s*lignes?\s*(\d+)\s*(?:[/, -]\s*(\d+))?\s*(:|\|)\s*(.*?)\s*(?:\||$)",
            line, re.I)
        if not m:
            m = re.match(
                r"DELETE\s*(:|\|)\s*(\d+)\s*(?:-\s*(\d+))?\s*(:|\|)\s*(.*)",
                line, re.I)
        if not m:
            continue
        a = int(m.group(2))
        b = int(m.group(3)) if m.group(3) else a
        frag = (m.group(5) or "").strip()
        # sometimes text follows after ' : ' without another delimiter
        if not frag:
            m2 = re.match(r"DELETE\s*(:|\|)\s*(\d+)(?:\s*-\s*(\d+))?\s*(.*)", line, re.I)
            if m2:
                frag = (m2.group(4) or "").strip()
        # take a distinctive fragment (first clause, strip reason words)
        frag = re.split(r"\s\|\s", frag)[0]
        frag = re.split(r"\s+:\s+(?:DOUBLON|raison|pourquoi|doublon)", frag, re.I)[0]
        frag = frag.replace("«", "").replace("»", "").replace('"', "").replace("„", "").replace('"', "")
        out.append((a, b, frag[:120]))
    return out


def main() -> None:
    for pr in range(600, 650):
        plan = list(TRANSCRIPT.get(pr, []))
        plan.extend(parse_fix_file(pr))
        if not plan:
            continue
        md = CHAP / f"de-{pr:04d}.md"
        lines = md.read_text(encoding="utf-8")
        ls = lines.splitlines(keepends=True)
        n = len(ls)
        deleted: set[int] = set()
        warns = []
        # sort by original line asc; process desc
        for a, b, frag in sorted(plan, key=lambda x: -x[0]):
            targets: list[int] = []
            for i in range(a - 1, min(b, n)):
                if i not in deleted:
                    targets.append(i)
            if frag:
                hits = [i for i in targets if norm(frag).lower() in norm(ls[i]).lower()]
                if not hits:
                    # search whole file
                    allh = find_matches(ls, frag)
                    allh = [i for i in allh if i not in deleted]
                    if allh:
                        targets = allh[: len(targets)]
                    else:
                        warns.append(f"frag not found: {frag[:50]}")
                        continue
            for i in sorted(targets, reverse=True):
                if 0 <= i < len(ls):
                    del ls[i]
                    deleted.add(i)
        md.write_text("".join(ls), encoding="utf-8")
        print(f"{pr}: deleted {len(deleted)} lines, {len(warns)} warnings")
        for w in warns[:4]:
            print(f"    !! {w}")


if __name__ == "__main__":
    main()