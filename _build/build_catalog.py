# -*- coding: utf-8 -*-
"""Build the SKit quotation site: extract catalog data + process product images."""
import io, json, os, re, sys, zipfile, hashlib, shutil
from collections import Counter, deque

from PIL import Image
import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import naming  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(SITE, "data")
IMG_DIR = os.path.join(SITE, "assets", "products")

SETS = [
    dict(key="L", file="L柄小厨具(KITCHEN TOOLS)盛美报价单.xlsx", pdf="L柄小厨具(KITCHEN TOOLS)盛美报价单.pdf"),
    dict(key="P", file="P柄小厨具(KITCHEN TOOLS)盛美报价单.xlsx", pdf="P柄小厨具(KITCHEN TOOLS)盛美报价单.pdf"),
    dict(key="S", file="硅胶&尼龙厨具(Silica gel)盛美报价单.xlsx", pdf="硅胶&尼龙厨具(Silica gel)盛美报价单.pdf"),
]

SIZES = [("thumb", (520, 390)), ("card", (900, 675)), ("full", (1400, 1050))]


# ---------------------------------------------------------------- utilities
def clean(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return int(v) if v == int(v) else v
    s = str(v).replace("_x000D_", "")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s*\n\s*", "\n", s)
    return s.strip()


ANCHOR_RE = re.compile(r"<xdr:(oneCellAnchor|twoCellAnchor)\b(.*?)</xdr:\1>", re.S)


def anchor_map(xlsx):
    """Return [{media, row, col}] with 1-based sheet coordinates."""
    z = zipfile.ZipFile(xlsx)
    rels = z.read("xl/drawings/_rels/drawing1.xml.rels").decode("utf-8")
    rel = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
    draw = z.read("xl/drawings/drawing1.xml").decode("utf-8")
    out = []
    for m in ANCHOR_RE.finditer(draw):
        body = m.group(2)
        rid = re.search(r'r:embed="([^"]+)"', body)
        frm = re.search(
            r"<xdr:from>\s*<xdr:col>(\d+)</xdr:col>(?:(?!</xdr:from>).)*?<xdr:row>(\d+)</xdr:row>",
            body, re.S)
        if not rid or not frm:
            continue
        tgt = rel.get(rid.group(1))
        # targets are relative to xl/drawings/, e.g. "../media/image3.png"
        if not tgt or "media/" not in tgt:
            continue
        out.append({"media": "xl/media/" + os.path.basename(tgt),
                    "row": int(frm.group(2)) + 1, "col": int(frm.group(1)) + 1})
    return out


def norm_material(raw, setkey):
    """Return (zh, en) material pair."""
    s = raw.replace("SS", "Stainless Steel").replace("ss", "Stainless Steel")
    s = re.sub(r"(\d{3})(?:\s*\+\s*)?", lambda m: m.group(1) + " Stainless Steel", s)
    zh_map = {
        "沙比利木": "沙比利木", "橡胶木": "橡胶木", "木": "木", "硅胶": "硅胶",
        "尼龙": "尼龙", "塑料": "塑料", "不锈钢": "不锈钢",
    }
    if setkey == "S":
        return raw
    parts = [p.strip() for p in raw.replace("＋", "+").split("+") if p.strip()]
    return "+".join(parts)


# ------------------------------------------------------------- name parsing
CATS = [
    ("cutlery", "Cutlery & Table Tools", r"叉|刀|勺|spoon|fork|knife|chopstick"),
    ("turners", "Turners, Spatulas & Shovels", r"铲|刮|抹|spatula|turner|shovel|scraper|plane|刨|刮刀"),
    ("whisks", "Whisks & Mixers", r"打蛋|搅拌|whisk|mixer|egg beater"),
    ("openers", "Openers & Peelers", r"开瓶|开罐|削皮|刨皮|opener|peeler|corer"),
    ("graters", "Graters & Slicers", r"刨丝|切丝|擦|grat|slic|shred|mandoline|切菜"),
    ("strainers", "Strainers & Colanders", r"漏|滤|筛|strain|colander|sieve|skimmer|filter"),
    ("measuring", "Measuring & Scales", r"量|称|scale|measur|thermometer"),
    ("bakery", "Bakery & Pastry", r"蛋糕|烘焙|饼|bake|cake|pastry|rolling|dough|pizza|比萨"),
    ("serve", "Serving & BBQ", r"夹|盘|托盘|serve|tong|tray|ladle|bbq|grill"),
    ("storage", "Kitchen Storage & Prep", r"密封|储物|收纳|保鲜|storage|container|jar|organi|pot|锅|盆|篮|basket|架|rack|挂钩|hook|垫|mat|board|砧板"),
    ("utensils", "Kitchen Utensils", r"."),
]

CAT_LABELS_ZH = {
    "cutlery": "餐具 · 刀叉勺",
    "turners": "铲 · 刮刀 · 抹刀",
    "whisks": "打蛋器 · 搅拌",
    "openers": "开瓶器 · 削皮器",
    "graters": "刨丝 · 切片",
    "strainers": "漏勺 · 滤网",
    "measuring": "量具 · 秤",
    "bakery": "烘焙 · 比萨",
    "serve": "分餐 · 烧烤",
    "storage": "收纳 · 备餐",
    "utensils": "其他厨具",
}


def classify(zh, en):
    hay = f"{zh} {en}".lower()
    for key, label, pat in CATS:
        if re.search(pat, hay, re.I):
            return key, label
    return "utensils", "Kitchen Utensils"


def parse_LP(rawname, setkey):
    """Delegates to naming.parse_multipart_name (handles / and newline separators)."""
    return naming.parse_multipart_name(rawname, setkey)


def parse_S(code_cell, name_cell):
    """code '1101A', name '灰柄尼龙土豆压' / '硅胶刮刀（中）'"""
    code = naming.clean_text(code_cell)
    zh = naming.clean_text(name_cell)
    return code, zh


def slugify(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


# ---------------------------------------------------------- image processing
def load_media(path, media):
    z = zipfile.ZipFile(path)
    return z.read(media)


def content_bbox(im, tol=34):
    """Flood-fill from borders over light, low-saturation background pixels."""
    small = im.copy()
    small.thumbnail((700, 700), Image.LANCZOS)
    w, h = small.size
    px = small.load()

    def is_bg(x, y):
        r, g, b = px[x, y][:3]
        mx, mn = max(r, g, b), min(r, g, b)
        return mn >= 100 and (mx - mn) <= tol and mx >= 150

    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not seen[y * w + x] and is_bg(x, y):
                seen[y * w + x] = 1
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if not seen[y * w + x] and is_bg(x, y):
                seen[y * w + x] = 1
                q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and is_bg(nx, ny):
                seen[ny * w + nx] = 1
                q.append((nx, ny))
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        row = y * w
        for x in range(w):
            if not seen[row + x]:
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
    if maxx < 0:
        return None
    sx, sy = im.size[0] / w, im.size[1] / h
    return (minx * sx, miny * sy, (maxx + 1) * sx, (maxy + 1) * sy)


def make_canvas(raw, size, margin=36, bg=(255, 255, 255)):
    """Trim background, then fit onto a white square-ish canvas with margin."""
    im = Image.open(io.BytesIO(raw))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        flat = Image.new("RGB", im.size, bg)
        flat.paste(im, mask=im.split()[-1])
        im = flat
    else:
        im = im.convert("RGB")
    try:
        box = content_bbox(im)
    except Exception:
        box = None
    if box:
        bw, bh = box[2] - box[0], box[3] - box[1]
        if bw > 24 and bh > 24 and (bw * bh) > 0.02 * im.size[0] * im.size[1]:
            pad = 6
            box = (max(0, box[0] - pad), max(0, box[1] - pad),
                   min(im.size[0], box[2] + pad), min(im.size[1], box[3] + pad))
            im = im.crop(tuple(int(round(v)) for v in box))

    W, H = size
    avail_w, avail_h = W - margin * 2, H - margin * 2
    sw, sh = im.size
    scale = min(avail_w / sw, avail_h / sh)
    nw, nh = max(1, int(round(sw * scale))), max(1, int(round(sh * scale)))
    im = im.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), bg)
    canvas.paste(im, ((W - nw) // 2, (H - nh) // 2))
    return canvas


def save_jpg(im, path, quality=86):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "JPEG", quality=quality, optimize=True, progressive=True)


# ---------------------------------------------------------------- hero images
def hero_candidates(z, prods, want=3):
    """Choose the widest, highest-resolution photos for a collection banner.

    Returns (picks, raw_bytes) where picks is [(product, media), ...].
    """
    scored, raw = [], {}
    for rank, p in enumerate(prods):
        media = p.get("_media")
        if not media:
            continue
        try:
            data = raw.setdefault(media, z.read(media))
            im = Image.open(io.BytesIO(data))
            w, h = im.size
        except Exception:
            continue
        ratio = w / h if h else 0
        if ratio < 0.9:          # too portrait for a banner cell
            continue
        scored.append((w * h, rank, media, p))
    scored.sort(key=lambda t: -t[0])
    picks, used_cat = [], set()
    for area, rank, media, p in scored:
        if p["cat"] in used_cat:
            continue
        picks.append((p, media))
        used_cat.add(p["cat"])
        if len(picks) >= want:
            break
    if len(picks) < want:                      # relax the category rule
        for area, rank, media, p in scored:
            if all(media != m for _, m in picks):
                picks.append((p, media))
            if len(picks) >= want:
                break
    return picks[:want], raw


def make_hero(picks, raw, out_path):
    """Build a wide banner: one large photo plus two smaller ones, on white."""
    W, H = 1400, 700
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    if not picks:
        save_jpg(canvas, out_path, 88)
        return
    gap = 14

    def place(tile_w, tile_h, x, y, media):
        im = Image.open(io.BytesIO(raw[media])).convert("RGB")
        try:
            box = content_bbox(im)
        except Exception:
            box = None
        if box:
            im = im.crop(tuple(int(round(v)) for v in box))
        sw, sh = im.size
        scale = min(tile_w / sw, tile_h / sh) * 0.9
        nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
        im = im.resize((nw, nh), Image.LANCZOS)
        canvas.paste(im, (x + (tile_w - nw) // 2, y + (tile_h - nh) // 2))

    if len(picks) == 1:
        place(W, H, 0, 0, picks[0][1])
    else:
        big_w = int(W * 0.56)
        place(big_w, H, 0, 0, picks[0][1])
        rest = picks[1:]
        right_x = big_w + gap
        right_w = W - right_x
        cell_h = (H - gap * (len(rest) - 1)) // max(1, len(rest))
        y = 0
        for p, media in rest:
            place(right_w, cell_h, right_x, y, media)
            y += cell_h + gap
    save_jpg(canvas, out_path, 88)


# --------------------------------------------------------------------- build
def build(limit=None, force=False):
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)
    catalog = {"sets": [], "products": [], "generated": None}

    for cfg in SETS:
        key = cfg["key"]
        xlsx = os.path.join(ROOT, cfg["file"])
        wb = openpyxl.load_workbook(xlsx, data_only=True)
        ws = wb.active

        rows = {}
        for r in range(1, ws.max_row + 1):
            rows[r] = [clean(ws.cell(r, c).value) for c in range(1, ws.max_column + 1)]

        title = rows[1][0] if rows.get(1) else ""
        contact = rows[2][0] if rows.get(2) else ""
        header = rows.get(3, [])

        anchors = [a for a in anchor_map(xlsx) if a["col"] == 1]
        img_by_row = {}
        for a in anchors:
            img_by_row.setdefault(a["row"], a["media"])
        hero_media = img_by_row.get(1)

        prods = []
        for r in sorted(rows):
            if r <= 3:
                continue
            cells = rows[r]
            if len(cells) < 2 or not str(cells[1]).strip():
                continue
            if key == "S":
                code, zh = parse_S(str(cells[1]), str(cells[2]) if len(cells) > 2 else "")
                en = ""
                off = 3
                size_note = ""
            else:
                code, zh, en, size_note = parse_LP(str(cells[1]), key)
                off = 2
                if not zh and en:
                    zh = en
            packing = str(cells[off]) if len(cells) > off else ""
            price = cells[off + 1] if len(cells) > off + 1 else ""
            qty = cells[off + 2] if len(cells) > off + 2 else ""
            size = str(cells[off + 3]) if len(cells) > off + 3 else ""
            gw = str(cells[off + 4]) if len(cells) > off + 4 else ""
            material = str(cells[off + 5]) if len(cells) > off + 5 else ""
            cbm = cells[off + 6] if len(cells) > off + 6 else ""
            if key == "S":
                colour = str(cells[10]) if len(cells) > 10 else ""
                note = ""
            else:
                colour = ""
                note = str(cells[off + 7]) if len(cells) > off + 7 else ""
            note = str(note).replace("\n", " · ")
            packing_en = naming.packing_en(packing)
            colour_en = naming.colour_en(colour)
            note_en = naming.packing_en(note) if note else ""

            cat_key, cat_label = classify(zh, en)

            # every line needs an English title for non-Chinese visitors
            if not en:
                en = naming.english_name(zh, code, size_note)
            elif not code:
                # e.g. 'M-P68 / Potato press' — lift the embedded item code out
                m = re.match(r"^([A-Za-z0-9]{1,3}-?[A-Za-z]{1,3}-?\d{1,4}[A-Za-z]?)\s*/\s*(.+)$", en)
                if m:
                    code, en = m.group(1), m.group(2).strip()
                else:
                    en = en.split(" / ")[-1].strip()

            # 'P柄叉' -> 'Fork': the handle is already named by the collection
            zh = re.sub(r"^[A-Za-z]柄", "", zh).strip() or zh
            material = re.sub(r"\s*\+\s*", "+", material).strip()

            pid = f"{key.lower()}-{slugify(code) or ('r%d' % r)}"
            media = img_by_row.get(r)
            entry = {
                "id": pid,
                "set": key,
                "row": r,
                "code": code,
                "name_zh": zh,
                "name_en": en,
                "material_en": naming.material_en(material),
                "packing": packing,
                "packing_en": packing_en,
                "colour_en": colour_en,
                "price": price,
                "qty": str(qty),
                "size": size,
                "gw": gw,
                "material": material,
                "cbm": cbm,
                "colour": colour,
                "note": note,
                "note_en": note_en,
                "size_note": size_note,
                "cat": cat_key,
                "cat_label": cat_label,
                "cat_label_zh": CAT_LABELS_ZH.get(cat_key, cat_label),
                "img": f"assets/products/{pid}",
            }
            if media:
                entry["_media"] = media
            prods.append(entry)

        # set-level metadata
        setinfo = {
            "key": key,
            "file": cfg["file"],
            "pdf": cfg["pdf"],
            "title": title,
            "contact": contact,
            "headers": header[:11],
            "count": len(prods),
            "hero": f"assets/products/{key.lower()}-hero",
            "hero_media": hero_media,
        }
        catalog["sets"].append(setinfo)
        catalog["products"].extend(prods)
        print(f"[{key}] parsed {len(prods)} products | title={title} | hero={hero_media}")

        # ---- images
        z = zipfile.ZipFile(xlsx)
        dest = os.path.join(SITE, "assets", "products")
        todo = [p for p in prods if p.get("_media")]
        if limit:
            todo = todo[:limit]
        for i, p in enumerate(todo, 1):
            thumb = os.path.join(dest, p["id"] + "-thumb.jpg")
            if force or not os.path.exists(thumb):
                raw = z.read(p["_media"])
                for tag, size in SIZES:
                    im = make_canvas(raw, size)
                    save_jpg(im, os.path.join(dest, f"{p['id']}-{tag}.jpg"),
                             quality=90 if tag == "thumb" else 86)
            if i % 40 == 0 or i == len(todo):
                print(f"    images {i}/{len(todo)}")

        # ---- collection hero: pick a wide, high-resolution photo, then build a
        #      3-photo composition strip so the banner looks like a catalogue page
        hero_path = os.path.join(dest, f"{key.lower()}-hero.jpg")
        if force or not os.path.exists(hero_path):
            picks, raw = hero_candidates(z, prods)
            make_hero(picks, raw, hero_path)
            print(f"    hero <- {[(p['code'], m) for p, m in picks]}")

    for p in catalog["products"]:
        p.pop("_media", None)
    for s in catalog["sets"]:
        s.pop("hero_media", None)

    with io.open(os.path.join(DATA, "catalog.json"), "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, ensure_ascii=False, separators=(",", ":"))

    counts = Counter(p["set"] for p in catalog["products"])
    cats = Counter(p["cat"] for p in catalog["products"])
    print("\ntotals:", dict(counts), "sum", sum(counts.values()))
    print("cats:", dict(cats))
    print("catalog.json bytes:", os.path.getsize(os.path.join(DATA, "catalog.json")))


if __name__ == "__main__":
    lim = None
    force = "--force" in sys.argv
    for a in sys.argv[1:]:
        if a.startswith("--limit="):
            lim = int(a.split("=")[1])
    build(limit=lim, force=force)
