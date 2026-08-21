#!/usr/bin/env python3
"""Audit local DE/FR chapters one by one and publish only complete French HTML."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path(r"C:\Users\Marc\Downloads\Perry Rhodan Sammelband")
REFUSAL = re.compile(
    r"texte (?:fourni|que vous m'avez fourni) est déjà en français|"
    r"veuillez (?:me )?(?:fournir|transmettre) le texte|"
    r"il n[’']y a (?:donc )?rien à traduire|"
    r"je ne peux pas (?:traduire|effectuer)",
    re.I,
)
GERMAN_STRONG = re.compile(
    r"\b(hatte|wurde|sagte|fragte|antwortete|musste|mußte|konnte|sollte|"
    r"bleibt|vollendet|geschah|ging|wußte|wusste|befand|erschien|"
    r"daraufhin|plötzlich|schließlich|jedoch|währenddessen)\b",
    re.I,
)
GERMAN_WORD = re.compile(
    r"\b(der|die|das|den|dem|ein|eine|einer|eines|einem|einen|und|oder|"
    r"aber|nicht|noch|auch|wird|werden|war|waren|ist|sind|mit|für|fuer|"
    r"auf|durch|zwischen|während|waehrend|dass|daß|wenn|weil|sie|wir|ich)\b",
    re.I,
)


def load_translation_checks(source: Path):
    spec = importlib.util.spec_from_file_location("translation_checks", source / "translate.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def has_german(text: str) -> bool:
    return bool(GERMAN_STRONG.search(text)) or len(GERMAN_WORD.findall(text)) >= 2


def has_untranslated_span(source: str, target: str) -> bool:
    src = re.findall(r"[A-Za-zÀ-ÿÄÖÜäöüß]+", source.lower())
    dst = re.findall(r"[A-Za-zÀ-ÿÄÖÜäöüß]+", target.lower())
    if len(src) < 3 or len(dst) < 3:
        return source.strip() == target.strip() and has_german(source)
    grams = {tuple(src[i:i + 3]) for i in range(len(src) - 2)}
    return any(
        tuple(dst[i:i + 3]) in grams and has_german(" ".join(dst[i:i + 3]))
        for i in range(len(dst) - 2)
    )


def audit(folder: Path, checks) -> dict:
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    num = int(meta.get("num") or folder.name[:4])
    de_path, fr_path = folder / "de.html", folder / "fr.html"
    errors: list[str] = []
    if meta.get("status") != "ok" or meta.get("repair"):
        errors.append("meta-not-ok")
    if not de_path.exists() or not fr_path.exists():
        errors.append("missing-html")
        return {"num": num, "folder": folder.name, "ok": False, "errors": errors}

    de = BeautifulSoup(de_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    fr = BeautifulSoup(fr_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    de_tags = [tag.name for tag in (de.body or de).find_all(True)]
    fr_tags = [tag.name for tag in (fr.body or fr).find_all(True)]
    if de_tags != fr_tags:
        errors.append(f"html-structure:{len(de_tags)}/{len(fr_tags)}")

    de_pieces = [str(p[1]) if p[0] == "text" else p[1].get(p[2], "") for p in checks.collect_html_pieces(de)]
    fr_pieces = [str(p[1]) if p[0] == "text" else p[1].get(p[2], "") for p in checks.collect_html_pieces(fr)]
    if len(de_pieces) != len(fr_pieces):
        errors.append(f"segment-count:{len(de_pieces)}/{len(fr_pieces)}")
    bad = [
        i + 1 for i, pair in enumerate(zip(de_pieces, fr_pieces))
        if not checks.quality_ok(*pair) or has_german(pair[1]) or has_untranslated_span(*pair)
    ]
    if bad:
        errors.append(f"bad-segments:{len(bad)}")

    fr_text = fr.get_text(" ", strip=True)
    de_text = de.get_text(" ", strip=True)
    ratio = len(fr_text) / max(1, len(de_text))
    if not 0.6 <= ratio <= 1.6:
        errors.append(f"length-ratio:{ratio:.3f}")
    german = [i + 1 for i, text in enumerate(fr_pieces) if checks.looks_german(text) or has_german(text)]
    if german:
        errors.append(f"german-segments:{len(german)}")
    if REFUSAL.search(fr_text):
        errors.append("model-refusal")

    return {
        "num": num,
        "folder": folder.name,
        "ok": not errors,
        "errors": errors,
        "de_segments": len(de_pieces),
        "fr_segments": len(fr_pieces),
        "de_chars": len(de_text),
        "fr_chars": len(fr_text),
        "ratio": round(ratio, 4),
        "fr_path": str(fr_path),
    }


def update_frontmatter(text: str, title_fr: str) -> str:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not match:
        raise ValueError("frontmatter missing")
    header = match.group(1)
    title_line = f"titleFr: {json.dumps(title_fr, ensure_ascii=False)}"
    header = re.sub(r"^titleFr:.*$", lambda _: title_line, header, flags=re.M)
    if "titleFr:" not in header:
        header += "\n" + title_line
    header = re.sub(r"^statut:.*$", "statut: traduit", header, flags=re.M)
    return f"---\n{header}\n---\n"


def apply_chapter(record: dict) -> Path:
    num = record["num"]
    target = ROOT / "src" / "content" / "chapitres" / f"de-{num:04d}.md"
    old = target.read_text(encoding="utf-8")
    fr = BeautifulSoup(Path(record["fr_path"]).read_text(encoding="utf-8", errors="replace"), "html.parser")
    title = (fr.title.get_text(" ", strip=True) if fr.title else "").strip()
    title = re.sub(rf"^Perry Rhodan\s+{num}\s*[-–—:]\s*", "", title, flags=re.I) or f"Perry Rhodan {num}"
    body = "".join(str(node) for node in (fr.body or fr).contents).strip()
    target.write_text(update_frontmatter(old, title) + "\n\n" + body + "\n", encoding="utf-8")
    return target


def audit_site(source: Path, checks) -> list[dict]:
    folders = {int(p.name[:4]): p for p in (source / "Chapitres").iterdir() if p.name[:4].isdigit()}
    records = []
    for path in sorted((ROOT / "src" / "content" / "chapitres").glob("de-*.md")):
        raw = path.read_text(encoding="utf-8")
        if not re.search(r"^statut:\s*traduit\s*$", raw, re.M):
            continue
        num = int(path.stem.removeprefix("de-"))
        body = re.split(r"\r?\n---\r?\n", raw, maxsplit=1)[-1]
        soup = BeautifulSoup(body, "html.parser")
        blocks = [tag.get_text(" ", strip=True) for tag in soup.find_all(["p", "h1", "h2", "h3", "li"])]
        if not blocks:
            blocks = [line.strip(" #\t") for line in body.splitlines() if line.strip(" #\t")]
        text = " ".join(blocks)
        errors = []
        german = [i + 1 for i, block in enumerate(blocks) if checks.looks_german(block) or has_german(block)]
        if german:
            errors.append(f"german-blocks:{len(german)}")
        if REFUSAL.search(text):
            errors.append("model-refusal")
        folder = folders.get(num)
        ratio = None
        if folder and (folder / "de.html").exists():
            de_text = BeautifulSoup(
                (folder / "de.html").read_text(encoding="utf-8", errors="replace"), "html.parser"
            ).get_text(" ", strip=True)
            ratio = len(text) / max(1, len(de_text))
            if not 0.6 <= ratio <= 1.6:
                errors.append(f"length-ratio:{ratio:.3f}")
        records.append({
            "num": num, "path": str(path), "ok": not errors, "errors": errors,
            "chars": len(text), "ratio": round(ratio, 4) if ratio is not None else None,
        })
    return records


def quarantine_site(record: dict) -> None:
    path = Path(record["path"])
    raw = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", raw, re.S)
    if not match:
        raise ValueError(f"frontmatter missing: {path}")
    header = re.sub(r"^statut:.*$", "statut: wip", match.group(1), flags=re.M)
    path.write_text(f"---\n{header}\n---\n\nWIP\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--mark-repair", action="store_true")
    parser.add_argument("--quarantine-site", action="store_true")
    args = parser.parse_args()
    checks = load_translation_checks(args.source)
    folders = sorted(
        (p for p in (args.source / "Chapitres").iterdir() if (p / "fr.html").exists()),
        key=lambda p: int(p.name[:4]),
    )
    records = [audit(folder, checks) for folder in folders]
    report = args.source / "_work" / "chapter-publication-audit.json"
    report.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    valid = [r for r in records if r["ok"]]
    failed = [r for r in records if not r["ok"]]
    print(f"AUDIT total={len(records)} valid={len(valid)} rejected={len(failed)}")
    for record in failed:
        print(f"REJECT {record['num']:04d} {', '.join(record['errors'])}")
    if args.mark_repair:
        for record in failed:
            path = args.source / "Chapitres" / record["folder"] / "meta.json"
            meta = json.loads(path.read_text(encoding="utf-8"))
            meta.update(status="alerte", repair=True, reasons=record["errors"])
            path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"MARKED_REPAIR {len(failed)} chapters")
    if args.apply:
        changed = [apply_chapter(record) for record in valid]
        print(f"APPLIED {len(changed)} chapters")
    site_records = audit_site(args.source, checks)
    site_report = args.source / "_work" / "site-publication-audit.json"
    site_report.write_text(json.dumps(site_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    site_failed = [r for r in site_records if not r["ok"]]
    print(f"SITE_AUDIT total={len(site_records)} valid={len(site_records) - len(site_failed)} rejected={len(site_failed)}")
    for record in site_failed:
        print(f"SITE_REJECT {record['num']:04d} {', '.join(record['errors'])}")
    if args.quarantine_site:
        for record in site_failed:
            quarantine_site(record)
        print(f"SITE_QUARANTINED {len(site_failed)} chapters")
    print(f"REPORT {report}")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
