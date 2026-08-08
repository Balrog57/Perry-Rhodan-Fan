import os
import sys
from PIL import Image

BASE = r"C:\Users\Marc\Documents\1G1R\_Programmation\Perry Rhodan Fan"
COVERS = os.path.join(BASE, "public", "images", "covers")

def convert(src, ext, save_kwargs):
    out = os.path.splitext(src)[0] + ".webp"
    img = Image.open(src)
    img.load()
    rgb = img.convert("RGB") if img.mode not in ("RGB", "RGBA", "LA", "P") else img
    rgb.save(out, "WEBP", **save_kwargs)
    ok = os.path.exists(out) and os.path.getsize(out) > 0
    if ok:
        os.remove(src)
    return ok, os.path.getsize(out) if ok else 0

total = 0
failed = []
for name in sorted(os.listdir(COVERS)):
    ext = os.path.splitext(name)[1].lower()
    if ext not in (".jpg", ".jpeg"):
        continue
    try:
        okc, sz = convert(os.path.join(COVERS, name), ext, {"quality": 80, "method": 4})
        if okc:
            total += 1
        else:
            failed.append(name)
    except Exception as e:
        failed.append(name + " :: " + str(e))

print("covers converted+deleted:", total, "failed:", len(failed))
for f in failed[:20]:
    print("  FAIL:", f)

# ship: keep alpha, pick best of lossless vs quality
ship = os.path.join(BASE, "public", "images", "spaceship.png")
try:
    img = Image.open(ship)
    tmp1 = os.path.join(os.path.dirname(ship), ".ship_ll.webp")
    tmp2 = os.path.join(os.path.dirname(ship), ".ship_q.webp")
    img.save(tmp1, "WEBP", lossless=True, method=4)
    img.save(tmp2, "WEBP", quality=92, method=4)
    s1 = os.path.getsize(tmp1)
    s2 = os.path.getsize(tmp2)
    best = tmp1 if s1 <= s2 else tmp2
    os.replace(best, os.path.join(os.path.dirname(ship), "spaceship.webp"))
    os.remove(tmp2 if best == tmp1 else tmp1)
    os.remove(ship)
    print("ship ->", os.path.getsize(os.path.join(os.path.dirname(ship), "spaceship.webp")), "bytes (lossless" ,
          ("win" if best == tmp1 else "q92 win"), s1, s2, ")")
except Exception as e:
    print("SHIP FAIL:", e)