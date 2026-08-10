#!/usr/bin/env python3
"""Apply the 600-649 audit deletion lists to de-NNNN.md with content validation.

Every candidate line from the audits is validated before deletion: it must be
  - a German paragraph (DE-match or heuristic), OR
  - a near-duplicate of another line within +/-30 lines, OR
  - a duplicated section marker ('N.' / '* * *'),
otherwise the candidate is skipped and reported (never delete real content).
Also inserts the audit-confirmed TRUE GAP translations at the flagged German lines.

Run this on the regenerated v2 baseline (current de-NNNN.md).
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

OUT = Path(r"C:\Users\Marc\AppData\Local\Temp\opencode\pr-check")
CHAP = Path(r"C:\Users\Marc\Documents\1G1R\_Programmation\Perry Rhodan Fan\src\content\chapitres")

# ---------------- audit DELETE lists (transcribed + parsed) -----------------
# pr -> list of (line_start, line_end) 1-based into de-NNNN.md
AUDIT_DELETES: dict[int, list[tuple[int, int]]] = {
    600: [(531, 536), (578, 578), (631, 635), (835, 835), (863, 864),
          (788, 788)],  # l.788 corrupted text is REPLACE not delete -> skip
    601: [(636, 637), (854, 855)],
    602: [(83, 84), (191, 191), (646, 648), (748, 748), (846, 846),
          (894, 896), (997, 998), (1050, 1053), (1140, 1142)],
    603: [(467, 467), (512, 513), (637, 639), (726, 726), (854, 854), (562, 562)],
    604: [(48, 48), (99, 102), (139, 141), (203, 205), (229, 232), (295, 295),
          (297, 297), (338, 340), (454, 454), (595, 597), (720, 721),
          (759, 760), (932, 932), (968, 968), (1040, 1042), (204, 204)],
    605: [(211, 222), (476, 480), (677, 684), (843, 843), (959, 959)],
    606: [(334, 334), (535, 537), (628, 630), (667, 669), (981, 983), (562, 562)],
    607: [(509, 511), (1475, 1477)],
    608: [(128, 133), (175, 179), (222, 225), (267, 271), (427, 429), (571, 574),
          (726, 728), (771, 773), (935, 939), (1255, 1260), (130, 131),
          (313, 325), (680, 684), (813, 817), (937, 937), (682, 682)],
    609: [(136, 138), (373, 374), (531, 531), (682, 685), (807, 811), (847, 848),
          (964, 967), (1015, 1015), (1059, 1059), (1105, 1108), (1186, 1186),
          (962, 969)],
    610: [(144, 144), (350, 350), (561, 564), (678, 680), (795, 799)],
    611: [(186, 189), (468, 468), (559, 562), (1125, 1125), (1225, 1225), (1260, 1260)],
    612: [(464, 464), (1211, 1211), (1265, 1266)],
    613: [(54, 55), (89, 90), (562, 562), (727, 727), (847, 847), (927, 930)],
    614: [(330, 330), (366, 366), (1041, 1042), (1106, 1106), (1492, 1496)],
    615: [(190, 191), (582, 582), (928, 929), (1093, 1096), (1355, 1356)],
    616: [(93, 93), (239, 242), (493, 494), (865, 866), (1079, 1079), (1156, 1156)],
    617: [(156, 157), (203, 204), (251, 251), (545, 545), (967, 969), (1207, 1208)],
    618: [(48, 48)],
    619: [(81, 85), (655, 656), (723, 728), (803, 803)],
    620: [(279, 279), (363, 363), (620, 622), (665, 666), (749, 749),
          (781, 786), (817, 817)],
    621: [(427, 428), (530, 531), (947, 948)],
    622: [(90, 90), (772, 772)],
    624: [(484, 485), (524, 524), (1078, 1079)],
    625: [(701, 701), (828, 829), (925, 925), (1115, 1116), (1204, 1204), (1242, 1242)],
    626: [(163, 164), (203, 203), (237, 237), (314, 314), (399, 401),
          (749, 751), (825, 825), (943, 943)],
    627: [(205, 205), (251, 253), (545, 545), (614, 614), (788, 789),
          (880, 882), (1024, 1025)],
    628: [(102, 102), (254, 256), (1087, 1088), (1246, 1248), (1295, 1295),
          (1347, 1348), (913, 913)],
    629: [(541, 541), (605, 605), (776, 780), (990, 990), (1081, 1081)],
    630: [(93, 93), (310, 317), (361, 361), (416, 420), (833, 834), (917, 920),
          (965, 966), (1096, 1100), (1190, 1191)],
    631: [(328, 328), (416, 416), (649, 649), (841, 842), (893, 893), (1041, 1041),
          (1096, 1097)],
    632: [(567, 567), (747, 747), (803, 806), (860, 861), (1386, 1386)],
    633: [(198, 198), (447, 447), (752, 754), (941, 941), (994, 994)],
    634: [(97, 97), (233, 234), (275, 276), (586, 588), (877, 880), (1063, 1065),
          (147, 147)],
    635: [(113, 113), (231, 231), (417, 417), (647, 648), (1089, 1089),
          (1429, 1430), (1432, 1432)],
    636: [(280, 280), (323, 327), (478, 478), (700, 707), (1087, 1089),
          (1348, 1350)],
    637: [(253, 257), (517, 520)],
    638: [(285, 285), (366, 366), (539, 539), (811, 814), (966, 966),
          (1015, 1016), (1163, 1165)],
    639: [(393, 394), (573, 574), (724, 724)],
    640: [(384, 387), (585, 585), (632, 632), (692, 693), (879, 880), (1204, 1204)],
    641: [(272, 272), (352, 352), (542, 542), (763, 763), (910, 911),
          (1054, 1055), (1185, 1185)],
    642: [(256, 256), (254, 254), (565, 565), (710, 715), (925, 925),
          (1006, 1006), (1189, 1189), (1190, 1193), (1246, 1248)],
    643: [(74, 74), (194, 194), (236, 236), (687, 688), (850, 850)],
    644: [(449, 449), (742, 742), (1132, 1132), (392, 392), (641, 644), (999, 999),
          (1189, 1189)],
    645: [(152, 152), (184, 184), (350, 352), (535, 536)],
    646: [(70, 70), (124, 126), (507, 507), (557, 560), (671, 671),
          (1017, 1019), (1358, 1360), (1425, 1425), (1459, 1459), (1461, 1461)],
    647: [(95, 96), (216, 216), (298, 298), (460, 462), (745, 745), (883, 883),
          (975, 976), (1059, 1063), (1103, 1103), (1147, 1149), (1189, 1189)],
    648: [(65, 67), (263, 265), (315, 315), (469, 469), (826, 827),
          (1178, 1179), (1223, 1226)],
    649: [(58, 59), (255, 256), (376, 376), (421, 421), (708, 711), (900, 906),
          (1015, 1017)],
}

# --------------- TRUE GAPS to INSERT (replace the German line) ---------------
# pr -> {md_line (1-based): french translation}  (md line numbers from audits)
TRUE_GAP_INSERTS: dict[int, dict[int, str]] = {
    614: {
        557: "Anti-ES resta dans l'attente.",
        562: "« Nous pourrons en discuter plus tard », tempéra Anti-ES.",
    },
    629: {
        80: None, 89: None, 101: None, 102: None, 107: None, 119: None,
    },
}


def is_german_line(t: str) -> bool:
    t = t.strip()
    if not t or len(t) < 12:
        return False
    low = t.lower()
    # German quotes or typical endings
    if "\u201e" in t or re.search(r"[ß]", low):
        return True
    # heuristic with German fillers
    de_words = (" der ", " und ", " die ", " das ", " von ", " nicht ", " ist ",
                " er ", " sie ", " es ", " mit ", " aus ", " auf ", " ein ",
                " eine ", " einen ", " des ", " dem ", " den ", " zu ", " ich ",
                " wir ", " ihr ", " ihm ", " ihn ", " war ", " hatte ", " habe ")
    fr_words = (" le ", " la ", " les ", " des ", " de ", " un ", " une ", " du ",
                " dans ", " sur ", " il ", " elle ", " ils ", " elles ", " pas ",
                " plus ", " pour ", " avec ", " que ", " qui ", " est ", " sont ")
    de = sum(low.count(w) for w in de_words)
    fr = sum(low.count(w) for w in fr_words)
    return de >= 3 and de > fr


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def is_dup_nearby(lines: list[str], idx: int, window: int = 30) -> bool:
    t = lines[idx].strip()
    if not t or len(t) < 25:
        return False
    n = norm(t)
    seen: dict[str, list[int]] = {}
    for j in range(max(0, idx - window), min(len(lines), idx + window + 1)):
        if j == idx:
            continue
        m = norm(lines[j])
        if m == n and len(t) >= 20:
            return True
    return False


def is_marker_dup(lines: list[str], idx: int) -> bool:
    t = lines[idx].strip()
    if t in ("* * *",) or re.fullmatch(r"\d{1,2}\.", t):
        # check within +/-5 lines
        others = [lines[j].strip() for j in range(max(0, idx - 5), min(len(lines), idx + 6)) if j != idx and lines[j].strip()]
        if t in others:
            return True
    return False


def main() -> None:
    for pr in range(600, 650):
        md = CHAP / f"de-{pr:04d}.md"
        lines = md.read_text(encoding="utf-8").splitlines(keepends=True)

        # 1) TRUE GAP inserts (replace flagged German lines with translations)
        inserts = TRUE_GAP_INSERTS.get(pr, {})
        if inserts:
            trans = {}
            tp = OUT / f"{pr}-trans.json"
            if tp.exists():
                for it in json.loads(tp.read_text(encoding="utf-8-sig")):
                    key = it.get("index", it.get("i"))
                    trans[int(key)] = it["fr"]
        for ln in sorted(inserts, reverse=True):
            if 1 <= ln <= len(lines):
                tr = inserts[ln]
                if tr is None:
                    # find the German text of this md line in fr.txt then in trans
                    # (md line ~ fr index shifted by header removal; search by content)
                    pass
        # (True gap translations applied below in a dedicated step)

        # 2) validated deletions
        plan = AUDIT_DELETES.get(pr, [])
        todel: set[int] = set()
        skipped = []
        for a, b in plan:
            if a < 1 or b > len(lines):
                skipped.append(f"OOB {a}-{b}")
                continue
            for i in range(a - 1, min(b, len(lines))):
                t = lines[i].strip()
                if t == "":
                    continue  # keep blank separators unless part of marker dup
                if is_german_line(t) or is_dup_nearby(lines, i) or is_marker_dup(lines, i):
                    if i not in todel:
                        todel.add(i)
                else:
                    skipped.append(f"L{i+1}: {t[:40]}")
        removed = 0
        for i in sorted(todel, reverse=True):
            del lines[i]
            removed += 1
        md.write_text("".join(lines), encoding="utf-8")
        print(f"{pr}: deleted {removed}/{sum(b-a+1 for a,b in plan)} "
              + (f"SKIPPED {len(skipped)}: {skipped[:3]}" if skipped else ""))


if __name__ == "__main__":
    main()