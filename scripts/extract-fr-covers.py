import io
import os
import re
import sys
import zipfile

from PIL import Image

BASE = r"C:\Users\Marc\Documents\1G1R\_Programmation\Perry Rhodan Fan"
EPUB_DIR = r"C:\Users\Marc\Downloads\Perry Rhodan"
COVERS = os.path.join(BASE, "public", "images", "covers")


def find_cover_data(zf):
    """Return raw bytes of the EPUB cover image, or None."""
    opf_names = []
    try:
        container = zf.read("META-INF/container.xml").decode("utf-8", "replace")
        opf_names = re.findall(r'full-path="([^"]+)"', container)
    except KeyError:
        pass
    if not opf_names:
        opf_names = [n for n in zf.namelist() if n.lower().endswith(".opf")]

    for opf in opf_names:
        try:
            opf_data = zf.read(opf).decode("utf-8", "replace")
        except KeyError:
            continue
        base_dir = os.path.dirname(opf)

        manifest = {}
        for im in re.finditer(r"<item\b[^>]*>", opf_data):
            tag = im.group(0)
            idm = re.search(r'\bid=["\']([^"\']+)["\']', tag)
            href = re.search(r'\bhref=["\']([^"\']+)["\']', tag)
            if idm and href:
                manifest[idm.group(1)] = href.group(1)

        cover_id = None
        m = re.search(r'<meta\b[^>]*\bname=["\']cover["\'][^>]*>', opf_data)
        if m:
            cm = re.search(r'\bcontent=["\']([^"\']+)["\']', m.group(0))
            if cm:
                cover_id = cm.group(1)

        rel_path = None
        if cover_id:
            rel_path = manifest.get(cover_id)
        if not rel_path:
            for hid in ("cover-image", "cover_image", "cover-img", "cover"):
                if hid in manifest:
                    rel_path = manifest[hid]
                    break
        if not rel_path:
            for hid, href in manifest.items():
                if "cover" in hid.lower():
                    rel_path = href
                    break
        if not rel_path:
            continue

        full = rel_path.replace("\\", "/")
        if not os.path.isabs(full):
            full = os.path.normpath(os.path.join(base_dir, full)).replace("\\", "/")
        try:
            data = zf.read(full)
        except KeyError:
            continue
        if data[:2] == b"\xff\xd8" or data[:8] == b"\x89PNG\r\n\x1a\n" or data[:4] == b"RIFF":
            return data
    return None


def epubs_by_number():
    result = {}
    for name in os.listdir(EPUB_DIR):
        if not name.lower().endswith(".epub"):
            continue
        m = re.search(r"Perry Rhodan-(\d{1,3})-", name)
        if not m:
            continue
        n = int(m.group(1))
        result.setdefault(n, []).append(os.path.join(EPUB_DIR, name))
    return result


def existing_path(fr):
    webp = os.path.join(COVERS, f"fr-{fr:03d}.webp")
    if os.path.exists(webp):
        return webp
    for ext in (".jpg", ".png", ".jpeg"):
        p = os.path.join(COVERS, f"fr-{fr:03d}{ext}")
        if os.path.exists(p):
            return p
    return None


def main():
    dry = "--dry-run" in sys.argv
    by_num = epubs_by_number()
    print(f"EPUBs parsed: {sum(len(v) for v in by_num.values())} files for {len(by_num)} tome numbers")

    replaced = skipped_smaller = no_epub = no_cover = errors = 0
    details = []
    for fr in range(1, 380):
        existing = existing_path(fr)
        files = by_num.get(fr, [])
        if not files:
            no_epub += 1
            continue
        best = None  # (area, w, h, data, filename)
        for path in files:
            try:
                with zipfile.ZipFile(path) as zf:
                    data = extract_cover(zf)
            except (zipfile.BadZipFile, OSError):
                errors += 1
                details.append(f"fr-{fr:03d}: ZIP ERROR {os.path.basename(path)}")
                continue
            if not data:
                continue
            try:
                im = Image.open(io.BytesIO(data))
                im.load()
            except Exception:
                continue
            w, h = im.size
            if best is None or w * h > best[0]:
                best = (w * h, w, h, data, os.path.basename(path))
        if best is None:
            no_cover += 1
            details.append(f"fr-{fr:03d}: NO COVER IMAGE found in EPUBs")
            continue
        area, w, h, data, fname = best
        try:
            im = Image.open(io.BytesIO(data)).convert("RGB")
            im.load()
        except Exception as e:
            errors += 1
            details.append(f"fr-{fr:03d}: unreadable cover in {fname}: {e}")
            continue
        if existing:
            try:
                ow, oh = Image.open(existing).size
            except Exception:
                ow, oh = 0, 0
        else:
            ow, oh = 0, 0
        if ow * oh >= area:
            skipped_smaller += 1
            details.append(f"fr-{fr:03d}: SKIP {ow}x{oh} >= epub {w}x{h} ({fname})")
            continue
        new_path = os.path.join(COVERS, f"fr-{fr:03d}.webp")
        if dry:
            details.append(f"fr-{fr:03d}: WOULD REPLACE {ow}x{oh} -> {w}x{h} from {fname}")
            replaced += 1
            continue
        im.save(new_path, "WEBP", quality=92, method=6)
        if os.path.exists(new_path) and os.path.getsize(new_path) > 0:
            replaced += 1
            details.append(f"fr-{fr:03d}: REPLACE {ow}x{oh} -> {w}x{h} from {fname}")
        else:
            errors += 1
            details.append(f"fr-{fr:03d}: WRITE FAILED -> {w}x{h} from {fname}")

    print(f"\nreplaced: {replaced} | skipped (existing >= epub): {skipped_smaller} | no epub: {no_epub} | no cover: {no_cover} | errors: {errors}")
    for d in details:
        print(" ", d)


def extract_cover(zf):
    return find_cover_data(zf)


if __name__ == "__main__":
    main()