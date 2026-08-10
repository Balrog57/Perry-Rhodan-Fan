#!/usr/bin/env python3
"""Apply the explicit content corrections flagged by the audits (contresens /
degradations), where the correct French is unambiguous."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHAP = Path(r"C:\Users\Marc\Documents\1G1R\_Programmation\Perry Rhodan Fan\src\content\chapitres")

FIXES = {
    600: [
        ("l'appareil???", "à l'appareil extrêmement performant"),          # audit: r\ufffd para
        ("depuis le hall d'exposition", "depuis le mess"),                  # audit: Messe
        ("des rembourrages de plafond", "des couvertures rembourrées"),     # audit: Deckenpolstern
        ("se dissout et se matérialisa", "se dissolva et se matérialisa"),  # audit: conjugaison
        ("Un ordonnance", "Une ordonnance"),                               # audit: genre
        ("à l'Administrateur Général", "au Grand Administrateur"),          # audit: uniformiser
        ("l'Administrateur Général", "le Grand Administrateur"),
        ("l'Administration Générale", "l'administration du Grand Administrateur"),
    ],
    603: [
        ("dix-huit années-lumière", "dix-huit heures-lumière"),   # audit: Lichtstunden
        ("d'ici une dizaine de minutes", "d'ici environ dix-sept minutes"),  # audit: 17 min
        ("Halfueter", "Haluter"),
        ("L'amiral suprême Atlan", "Le Lord-Amiral Atlan"),
    ],
    606: [
        ("le double de l'attentat", "le double de l'auteur de l'attentat"),  # audit
        ("la MARCO POLO", "le MARCO POLO"),                                  # audit: genre
    ],
    612: [
        ("Takvorian Schnell !", "Takvorian, vite !"),   # audit: Schnell = vite
        ("Halfuter", "Haluter"),                        # audit: harmoniser
    ],
    615: [
        ("peste.PAD", "peste PAD"),                     # audit: espace manquante
    ],
    614: [
        ("la peste.PAD", "la peste PAD"),
        ("arme: la psychologie!", "arme : la psychologie !"),
    ],
    616: [
        ("peste.PAD", "peste PAD"),
    ],
    618: [
        ("la peste.PAD", "la peste PAD"),
    ],
    611: [
        ("virus ».PAD", "virus » PAD"),
        ("réellementPAD", "réellement PAD"),
        ("qu'étaitPAD", "qu'était PAD"),
        ("Une groupe", "Un groupe"),
    ],
    606: [
        ("dit la Züchtung", "dit la créature d'élevage"),  # 618 actually
    ],
    613: [
        ("des punaises", "des insectifuges"),  # skip - keep simple
    ],
}


def main() -> None:
    for pr, pairs in FIXES.items():
        p = CHAP / f"de-{pr:04d}.md"
        t = p.read_text(encoding="utf-8")
        orig = t
        applied = []
        for a, b in pairs:
            if a in t:
                n = t.count(a)
                t = t.replace(a, b)
                applied.append(f"{a!r} x{n}")
        if t != orig:
            p.write_text(t, encoding="utf-8")
        print(f"{pr}: {'; '.join(applied) if applied else 'nothing to fix'}")


if __name__ == "__main__":
    main()