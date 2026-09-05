#!/usr/bin/env python3
"""Audit local DE/FR chapters and publish 100% complete French texts to the site."""

from __future__ import annotations

import argparse
import io
import json
import re
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup, Comment, NavigableString


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path(r"C:\Users\Marc\Downloads\Perry Rhodan Sammelband")
COVERS_DIR = ROOT / "public" / "images" / "covers"
TOC_HREF = re.compile(r"\.(?:x?html?)(?:#|$)", re.I)
BOILERPLATE = re.compile(
    r"^(?:Nr\.?\s*\d+|Pabel-Moewig|Cover|Perry Rhodan\s+\d+)",
    re.I,
)
APPENDIX = re.compile(
    r"^(?:Impressum|Leserkontaktseite|Glossar|Stellaris\s+\d+|Vorwort|"
    r"PERRY RHODAN\s*[–—-]\s*la série|« Faire le tour)",
    re.I,
)
AUTHOR_NAME = re.compile(
    r"^[A-ZÀ-Ÿ][A-Za-zÀ-ÿÄÖÜäöüß.'\-]+(?: [A-ZÀ-Ÿ][A-Za-zÀ-ÿÄÖÜäöüß.'\-]+)+$"
)
CHAPTER_HEAD = re.compile(
    r"^(?:\d+\.\s+\S.{0,70}|Prolog(?:ue)?|Épilogue|Epilog|Les personnages principaux)\b",
    re.I,
)
REFUSAL = re.compile(
    r"texte (?:fourni|que vous m'avez fourni) est déjà en français|"
    r"veuillez (?:me )?(?:fournir|transmettre) le texte|"
    r"il n[’']y a (?:donc )?rien à traduire|"
    r"je ne peux pas (?:traduire|effectuer)",
    re.I,
)
XML_RESPONSE = re.compile(r"```xml|<(?:translation|response|answer|output)\b", re.I)
GERMAN_STRONG = re.compile(
    r"\b(hatte|wurde|sagte|fragte|antwortete|musste|mußte|konnte|sollte|"
    r"bleibt|vollendet|geschah|ging|wußte|wusste|befand|erschien|"
    r"daraufhin|plötzlich|schließlich|jedoch|währenddessen)\b",
    re.I,
)
GERMAN_WORD = re.compile(
    r"\b(der|die|das|den|dem|ein|eine|einer|eines|einem|einen|und|oder|"
    r"aber|nicht|noch|auch|wird|werden|war|waren|ist|sind|für|fuer|"
    r"auf|durch|zwischen|während|waehrend|dass|daß|wenn|weil|sie|wir|ich)\b",
    re.I,
)


class AuditChecks:
    """Self-contained audit helpers; never imports or executes the translator."""

    DE_MARKERS = re.compile(
        r"\b(und|oder|nicht|sich|wird|wurde|werden|sind|waren|aber|auch|noch|"
        r"nach|über|ueber|durch|zwischen|während|waehrend|können|koennen|"
        r"müssen|muessen|sollte|gewesen|schon|einer|einem|einen|eines|"
        r"dieses|diese|dieser|auf|haben|hatte|war|sagte|fragte|antwortete|"
        r"wollte|konnte|musste|ließ|lies|geschehen|dem|den|der|die|das|mit|"
        r"eine|ich|wir|ihr|ihre|mein|meine|mich|sie|wieder|einmal|zur|zum|"
        r"vom|beim|im|am|ins|ans|für|fuer|ohne|gegen|weil|dass|daß|wenn|"
        r"wie|nur|sehr|mehr|hier|dann|dort|unter|vor|aus)\b",
        re.I,
    )
    FR_MARKERS = re.compile(
        r"\b(le|la|les|des|de|du|un|une|et|est|sont|dans|pour|avec|que|qui|"
        r"pas|plus|mais|cette|ces|aux|sur|par|nous|vous|elle|ils|elles|été|"
        r"etre|être|aussi|comme|tout|tous|bien|encore|après|apres|avant|"
        r"sans|sous|entre|leur|leurs|dont|où|ou|ainsi|très|tres)\b",
        re.I,
    )

    @classmethod
    def looks_german(cls, text: str) -> bool:
        sample = (text or "").strip()[:4000]
        if len(sample) < 12:
            return False
        de = len(cls.DE_MARKERS.findall(sample))
        fr = len(cls.FR_MARKERS.findall(sample))
        if fr >= 3 and fr >= de:
            return False
        if de >= 2 and fr == 0:
            return True
        if de >= 3 and de > fr * 1.5:
            return True
        return len(sample) >= 40 and ((de >= 5 and de > fr * 1.2) or (de >= 8 and de > fr))

    @staticmethod
    def _skip_piece(text: str) -> bool:
        s = text.strip()
        if len(s) < 3:
            return True
        if re.fullmatch(r"[\d\s.,;:!?/%+\-–—•·'’\"«»()\[\]{}]+", s):
            return True
        return len(re.findall(r"[A-Za-zÀ-ÿÄÖÜäöüß]", s)) < 3

    @classmethod
    def collect_html_pieces(cls, soup: BeautifulSoup) -> list:
        pieces = []
        for node in soup.descendants:
            if isinstance(node, Comment):
                continue
            parent = getattr(node, "parent", None)
            if parent is None or (parent.name or "").lower() in {
                "script", "style", "code", "pre", "svg", "noscript", "textarea", "math", "annotation",
            }:
                continue
            if isinstance(node, NavigableString) and not cls._skip_piece(str(node)):
                pieces.append(("text", node))
        for tag in soup.find_all(True):
            if (tag.name or "").lower() in {
                "script", "style", "code", "pre", "svg", "noscript", "textarea", "math", "annotation",
            }:
                continue
            for attr in ("alt", "title", "aria-label"):
                val = tag.get(attr)
                if isinstance(val, str) and not cls._skip_piece(val):
                    pieces.append(("attr", tag, attr))
        return pieces

    @classmethod
    def quality_ok(cls, src: str, dst: str) -> bool:
        if not dst or not dst.strip():
            return False
        if cls._skip_piece(src):
            return True
        s, d = src.strip(), dst.strip()
        if d == s and (cls.looks_german(s) or len(s) >= 80):
            return False
        if cls.looks_german(d):
            return False
        if len(s) >= 80 and not 0.35 <= len(d) / max(1, len(s)) <= 3.2:
            return False
        return True


def has_german(text: str) -> bool:
    # Strong German verbs also appear inside alien names (e.g. Ging-Li-G'ahd).
    # Only treat them as errors on substantial pieces without clear French context.
    sample = (text or "").strip()[:4000]
    if len(sample) < 40 or not GERMAN_STRONG.search(sample):
        return False
    fr = len(AuditChecks.FR_MARKERS.findall(sample))
    return fr < 2


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
        return {
            "num": num,
            "folder": folder.name,
            "ok": False,
            "meta_ok": str(meta.get("status") or "") == "ok" and not meta.get("repair"),
            "original_title": str(meta.get("title") or folder.name.split(" - ", 1)[-1]),
            "errors": errors,
            "fr_path": str(fr_path),
        }

    de = BeautifulSoup(de_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    fr = BeautifulSoup(fr_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    de_tags = [tag.name for tag in (de.body or de).find_all(True)]
    fr_tags = [tag.name for tag in (fr.body or fr).find_all(True)]
    de_pieces = [str(p[1]) if p[0] == "text" else p[1].get(p[2], "") for p in checks.collect_html_pieces(de)]
    fr_pieces = [str(p[1]) if p[0] == "text" else p[1].get(p[2], "") for p in checks.collect_html_pieces(fr)]
    bad = []
    if len(de_pieces) == len(fr_pieces):
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
    if XML_RESPONSE.search(fr_path.read_text(encoding="utf-8", errors="replace")):
        errors.append("xml-response")

    return {
        "num": num,
        "folder": folder.name,
        "ok": not errors,
        "meta_ok": str(meta.get("status") or "") == "ok" and not meta.get("repair"),
        "original_title": str(meta.get("title") or folder.name.split(" - ", 1)[-1]),
        "errors": errors,
        "de_segments": len(de_pieces),
        "fr_segments": len(fr_pieces),
        "de_chars": len(de_text),
        "fr_chars": len(fr_text),
        "ratio": round(ratio, 4),
        "fr_path": str(fr_path),
    }


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def parse_simple_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---", text, re.S)
    if not match:
        return {}
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        data[key.strip()] = raw.strip().strip('"')
    return data


def cycle_number_for(num: int) -> int:
    for path in (ROOT / "src" / "content" / "cycles").glob("cycle-*.md"):
        data = parse_simple_frontmatter(path.read_text(encoding="utf-8"))
        try:
            start, end, cycle = int(data["bookStart"]), int(data["bookEnd"]), int(data["cycleNumber"])
        except (KeyError, ValueError):
            continue
        if start <= num <= end:
            return cycle
    return 0


def is_toc_block(tag) -> bool:
    links = tag.find_all("a", href=True)
    if not links:
        return False
    text = tag.get_text(" ", strip=True)
    return all(TOC_HREF.search(a.get("href") or "") for a in links) and len(text) < 120


TITLE_FR_FIXES = {
    1223: "L'héritage d'Ordoban",
    1224: "Retour dans le Rubis de Givre",
    1227: "L'heure de Lord Mhuthan",
    1229: "Roulette psionique",
    1231: "Opération Bouclier thermique",
    1234: "Radio pirate Achéron",
    1235: "L'éclair sur Éden",
    1237: "La rébellion des cybernètes",
    1238: "Au centre du cyber-pays",
    1251: "Stalker",
    1252: "Départ des Vironautes",
    1255: "Opération Écran de quarantaine",
    1258: "La fièvre des étoiles",
    1261: "Dévolution",
    1262: "L'école des héros",
}


def html_to_markdown(html: str, num: int, de_html: str = "") -> tuple[str, str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title_fr = (soup.title.get_text(" ", strip=True) if soup.title else "").strip()
    title_fr = re.sub(rf"^Perry Rhodan\s+{num}\s*[-–—:]\s*", "", title_fr, flags=re.I).strip()
    if num in TITLE_FR_FIXES:
        title_fr = TITLE_FR_FIXES[num]
    authors: list[str] = []
    lines: list[str] = []
    started = False
    saw_resume_heading = False
    after_series_intro = False

    # Extract author from DE or FR if available
    for raw_h in [de_html, html]:
        if not raw_h:
            continue
        s_h = BeautifulSoup(raw_h, "html.parser")
        for tag in s_h.find_all(["p", "h1", "h2", "h3"]):
            text_h = tag.get_text(" ", strip=True)
            m = re.search(
                r"^(?:von|de|par|by)\s+([A-ZÀ-Ÿ][A-Za-zÀ-ÿÄÖÜäöüß.'\-]+(?: [A-ZÀ-Ÿ][A-Za-zÀ-ÿÄÖÜäöüß.'\-]+)+)$",
                text_h,
                re.I,
            )
            if m:
                found_a = m.group(1).strip()
                if found_a not in authors:
                    authors.append(found_a)
                break
        if authors:
            break

    for tag in (soup.body or soup).find_all(["h1", "h2", "h3", "p"]):
        if tag.name == "p" and tag.find("p") is not None:
            continue
        if tag.name == "p" and set(tag.get("class") or []) & {"p2", "p3", "calibre_3"}:
            continue
        text = re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()
        if not text or text in {"*", "·"}:
            continue
        if is_toc_block(tag):
            continue
        if num == 3090 and not started:
            if re.match(r"^PERRY RHODAN\s*[–—-]\s*la série", text, re.I):
                after_series_intro = True
                continue
            if not after_series_intro or not (
                CHAPTER_HEAD.search(text)
                or re.match(r"^(?:Préambule|Avant-propos|Préface)\b", text, re.I)
            ):
                continue
        if started and APPENDIX.search(text):
            break
        if re.search(r"Pabel-Moewig", text, re.I):
            continue
        if not any(line.startswith("## ") for line in lines) and len(text) < 80:
            m_author = re.search(
                r"^(?:von|de|par|by\s+)?([A-ZÀ-Ÿ][A-Za-zÀ-ÿÄÖÜäöüß.'\-]+(?: [A-ZÀ-Ÿ][A-Za-zÀ-ÿÄÖÜäöüß.'\-]+)+)$",
                text,
            )
            if m_author and AUTHOR_NAME.search(m_author.group(1)):
                authors.append(m_author.group(1).strip())
                continue
        if not started:
            if BOILERPLATE.search(text) or len(text) < 8:
                continue
            if len(text) < 80 and not CHAPTER_HEAD.search(text) and tag.name == "p":
                m_author = re.search(
                    r"^(?:von|de|par|by\s+)?([A-ZÀ-Ÿ][A-Za-zÀ-ÿÄÖÜäöüß.'\-]+(?: [A-ZÀ-Ÿ][A-Za-zÀ-ÿÄÖÜäöüß.'\-]+)+)$",
                    text,
                )
                if m_author and AUTHOR_NAME.search(m_author.group(1)):
                    authors.append(m_author.group(1).strip())
                    continue
            started = True
        heading = tag.name in {"h1", "h2", "h3"} or (CHAPTER_HEAD.search(text) and len(text) < 90)
        if heading:
            clean = re.sub(rf"^Perry Rhodan\s+{num}\s*[-–—:]\s*", "", text, flags=re.I).strip()
            if not clean or BOILERPLATE.search(clean):
                continue
            lines.append("")
            lines.append(f"## {clean}")
            lines.append("")
            continue
        if not saw_resume_heading and len(text) > 180 and not any(
            line.startswith("## ") for line in lines
        ):
            lines.append("## Résumé des épisodes précédents")
            lines.append("")
            saw_resume_heading = True
        lines.append(text)
        lines.append("")
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    auteur = " et ".join(dict.fromkeys(authors))
    if not title_fr:
        title_fr = f"Perry Rhodan {num}"
    return body, title_fr, auteur


def extract_cover(num: int, source: Path) -> Path | None:
    dest = COVERS_DIR / f"de-{num:04d}.webp"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    # Check if cover already in Chapitres folder
    for folder in (source / "Chapitres").iterdir():
        if folder.is_dir() and folder.name.startswith(f"{num:04d}"):
            c_webp = folder / "cover.webp"
            if c_webp.exists() and c_webp.stat().st_size > 0:
                COVERS_DIR.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(c_webp.read_bytes())
                return dest
            c_jpg = folder / "cover.jpg"
            if c_jpg.exists() and c_jpg.stat().st_size > 0:
                try:
                    from PIL import Image
                    im = Image.open(c_jpg)
                    COVERS_DIR.mkdir(parents=True, exist_ok=True)
                    im.convert("RGB").save(dest, "WEBP", quality=90, method=6)
                    return dest
                except Exception:
                    pass
    epub_dir = source / "Perry Rhodan Sammelband"
    if not epub_dir.exists():
        return dest if dest.exists() else None
    epub = next(
        (p for p in epub_dir.glob("*.epub") if re.search(rf"Perry Rhodan\s+{num}\b", p.name)),
        None,
    )
    if epub is None:
        return None
    try:
        from PIL import Image
    except ImportError:
        return None
    with zipfile.ZipFile(epub) as zf:
        names = [
            n for n in zf.namelist()
            if re.search(r"(?:cover|titel|front)\.(?:jpe?g|png|webp)$", n, re.I)
            or re.search(r"/images?/.*\.(?:jpe?g|png|webp)$", n, re.I)
        ]
        if not names:
            names = [n for n in zf.namelist() if re.search(r"\.(?:jpe?g|png|webp)$", n, re.I)]
        best = None
        for name in names:
            try:
                data = zf.read(name)
                image = Image.open(io.BytesIO(data))
                image.load()
            except Exception:
                continue
            area = image.size[0] * image.size[1]
            if best is None or area > best[0]:
                best = (area, image)
        if best is None:
            return None
        COVERS_DIR.mkdir(parents=True, exist_ok=True)
        best[1].convert("RGB").save(dest, "WEBP", quality=90, method=6)
        return dest if dest.exists() else None


def update_frontmatter(
    text: str,
    *,
    title: str,
    title_fr: str,
    auteur: str,
    cover: str | None,
) -> str:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
    if not match:
        raise ValueError("frontmatter missing")
    header = match.group(1)
    replacements = {
        "title": yaml_quote(title),
        "titleFr": yaml_quote(title_fr),
        "originalTitle": yaml_quote(title),
        "statut": "traduit",
    }
    if auteur:
        replacements["auteur"] = yaml_quote(auteur)
    if cover:
        replacements["cover"] = yaml_quote(cover)
    for key, value in replacements.items():
        if re.search(rf"^{key}:", header, re.M):
            header = re.sub(rf"^{key}:.*$", f"{key}: {value}", header, flags=re.M)
        else:
            header += f"\n{key}: {value}"
    return f"---\n{header.strip()}\n---\n"


def new_chapter_markdown(
    num: int,
    *,
    title: str,
    title_fr: str,
    auteur: str,
    parution: str,
    cover: str | None,
    body: str,
) -> str:
    cycle = cycle_number_for(num)
    lines = [
        "---",
        f"title: {yaml_quote(title)}",
        f"titleFr: {yaml_quote(title_fr)}",
        f"cycleNumber: {cycle}",
        f"chapterNumber: {num}",
        "type: translation",
        f"originalTitle: {yaml_quote(title)}",
    ]
    if cover:
        lines.append(f"cover: {yaml_quote(cover)}")
    if auteur:
        lines.append(f"auteur: {yaml_quote(auteur)}")
    if parution:
        lines.append(f"parution: {yaml_quote(parution)}")
    lines.append("statut: traduit")
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body.strip() + "\n"


def apply_chapter(record: dict, source: Path) -> Path:
    num = record["num"]
    target = ROOT / "src" / "content" / "chapitres" / f"de-{num:04d}.md"
    html = Path(record["fr_path"]).read_text(encoding="utf-8", errors="replace")
    de_path = Path(record["fr_path"]).parent / "de.html"
    de_html = de_path.read_text(encoding="utf-8", errors="replace") if de_path.exists() else ""
    body, title_fr, auteur_html = html_to_markdown(html, num, de_html)
    if "Chaotarchen-Zyklus" in title_fr or title_fr.strip() == "Sternenruf":
        title_fr = "Appel des étoiles"
    if re.search(r"\b(Operation|Die |Der |Das )\b", title_fr) and num == 1462:
        title_fr = "Opération Monde de la Brute"
    title = str(record.get("original_title") or "").strip() or title_fr
    auteur = auteur_html
    parution = ""
    cover_path = extract_cover(num, source)
    cover = f"/images/covers/{cover_path.name}" if cover_path else None
    if target.exists():
        old = target.read_text(encoding="utf-8")
        existing = parse_simple_frontmatter(old)
        title = existing.get("title") or title
        if existing.get("title") and existing["title"] not in {"WIP", title_fr}:
            title = existing["title"]
        existing_auteur = existing.get("auteur") or ""
        if existing_auteur and AUTHOR_NAME.search(existing_auteur.split(" et ")[0]):
            auteur = existing_auteur
        elif auteur_html:
            auteur = auteur_html
        parution = existing.get("parution") or parution
        if not existing.get("cover") and cover:
            pass
        header = update_frontmatter(
            old, title=title, title_fr=title_fr, auteur=auteur, cover=cover
        )
        target.write_text(header + "\n" + body.strip() + "\n", encoding="utf-8")
    else:
        if num == 3054 and not parution:
            parution = "2020-02-28"
        target.write_text(
            new_chapter_markdown(
                num,
                title=title,
                title_fr=title_fr,
                auteur=auteur,
                parution=parution,
                cover=cover,
                body=body,
            ),
            encoding="utf-8",
        )
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
        # looks_german is useful for source/target segment validation, but its
        # short-text heuristic produces false positives on valid French prose.
        german = [i + 1 for i, block in enumerate(blocks) if has_german(block)]
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
    parser.add_argument("--ok-only", action="store_true")
    parser.add_argument("--mark-repair", action="store_true")
    parser.add_argument("--quarantine-site", action="store_true")
    args = parser.parse_args()
    checks = AuditChecks()
    folders = sorted(
        (p for p in (args.source / "Chapitres").iterdir() if (p / "fr.html").exists()),
        key=lambda p: int(p.name[:4]),
    )
    if args.ok_only:
        ready = []
        for folder in folders:
            meta_path = folder / "meta.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if str(meta.get("status") or "") == "ok" and not meta.get("repair"):
                ready.append(folder)
        folders = ready
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
        to_apply = valid
        changed = [apply_chapter(record, args.source) for record in to_apply]
        print(f"APPLIED {len(changed)} chapters")
        for path in changed:
            print(f"WROTE {path}")
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
    if args.ok_only and args.apply:
        return 0 if valid else 1
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
