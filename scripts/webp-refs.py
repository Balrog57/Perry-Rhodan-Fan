import os
import re

base = r"C:\Users\Marc\Documents\1G1R\_Programmation\Perry Rhodan Fan\src\content"
pat = re.compile(r'(cover:\s*")([^"]+)\.(jpe?g)(")')

n = 0
for dirpath, _, files in os.walk(base):
    for f in files:
        if not f.endswith(".md"):
            continue
        p = os.path.join(dirpath, f)
        with open(p, encoding="utf-8", errors="replace") as fh:
            txt = fh.read()
        new = pat.sub(lambda m: m.group(1) + m.group(2) + ".webp" + m.group(4), txt)
        if new != txt:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(new)
            n += 1

print("md files updated:", n)