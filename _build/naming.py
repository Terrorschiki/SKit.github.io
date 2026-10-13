# -*- coding: utf-8 -*-
"""Item-code parsing and English naming for the SKit price lists."""
import re

# ---------------------------------------------------------------- code parsing
# Matches L01 / M-P01 / 1-P110 / P113 / 3305E / A12 / K-07 / M-P68
# An optional "1-"/"12-" prefix, then 1-2 letters, an optional hyphen, digits.
# (letters and the hyphen must not overlap, or backtracking breaks "M-P68".)
TOKEN_CODE_RE = re.compile(
    r"^(?:\d{1,2}-)?"          # optional numeric prefix, e.g. 1-P110
    r"[A-Za-z]{1,3}"           # L, P, MP, SK
    r"(?:-[A-Za-z]{1,2})?"     # optional second letter block, M-P68
    r"-?\d{1,4}"               # digits
    r"[A-Za-z]?$"              # optional trailing letter, 3305E
)
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
SIZE_TAIL_RE = re.compile(r"^[\d.]+\s*(?:CM|MM|ML|L|寸|INCH|IN)\.?$", re.I)
SIZE_IN_RE = re.compile(r"[（(](\d+(?:\.\d+)?\s*(?:CM|cm|MM|mm|寸))[）)]")
TRAIL_SIZE_RE = re.compile(r"(\d+(?:\.\d+)?\s*(?:CM|cm|MM|mm|寸))\s*$")


def clean_text(v):
    """Normalise a raw cell: drop _x000D_, collapse spaces, keep line breaks."""
    if v is None:
        return ""
    s = str(v).replace("_x000D_", "")
    s = s.replace("\u3000", " ").replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s*\n\s*", "\n", s)
    return s.strip()


def parse_multipart_name(raw, setkey):
    """Parse an L/P style name cell that may use / or newlines as separators.

    Examples
      '叉/L01\\nFork'                       -> ('L01', '叉', 'Fork', '')
      'P柄小号土豆压/M-P68（6cm)/Potato press' -> ('M-P68', 'P柄小号土豆压', 'Potato press', '6CM')
      '1-P110/中漏铲'                        -> ('1-P110', '中漏铲', '', '')
      'P117/线漏16CM'                        -> ('P117', '线漏', '', '16CM')
      'P柄叉/M-P01/Fork'                     -> ('M-P01', 'P柄叉', 'Fork', '')
    """
    txt = clean_text(raw)
    lines = [ln.strip() for ln in txt.split("\n") if ln.strip()]
    parts = []
    for ln in lines:
        parts.extend([p.strip() for p in ln.split("/") if p.strip()])

    code = ""
    zh_bits, en_bits, size_note = [], [], ""

    for tok in parts:
        # a size annotation in brackets: (8cm) （6cm）
        m = SIZE_IN_RE.search(tok)
        if m and not code:
            size_note = m.group(1).upper().replace(" ", "")
            tok = SIZE_IN_RE.sub("", tok).strip()
            if not tok:
                continue

        has_cjk = bool(CJK_RE.search(tok))
        if not has_cjk and TOKEN_CODE_RE.match(tok) and re.search(r"\d", tok):
            if not code:
                code = tok
            continue

        if has_cjk:
            if tok.endswith("）") or tok.endswith(")"):
                tok = tok.rstrip("）)").strip()
            zh_bits.append(tok)
        else:
            en_bits.append(tok)

    zh = "".join(zh_bits).strip()
    en = " / ".join([b for b in en_bits if b]).strip(" /")

    # a trailing size on the Chinese name: 线漏16CM -> 线漏 + 16CM
    if not size_note:
        m = TRAIL_SIZE_RE.search(zh)
        if m:
            size_note = m.group(1).upper().replace(" ", "")
            zh = zh[: m.start()].strip()

    return code, zh, en, size_note


# ------------------------------------------------------- hand-built EN names
# The silicone & nylon sheet lists Chinese names only; the head noun and the
# colour/handle prefix are translated here so every line has an English title.

HANDLES = [
    ("镀玫瑰金圆管柄", "Rose-gold tube handle"),
    ("镀金尼龙柄", "Gold-plated nylon handle"),
    ("镀金木纹柄", "Gold-plated wood-grain handle"),
    ("镀金弯管柄", "Gold-plated curved-tube handle"),
    ("镀金柄", "Gold-plated handle"),
    ("镀金圆管柄", "Gold-plated tube handle"),
    ("黑胡桃柄", "Black walnut handle"),
    ("沙比利木柄", "Sapele wood handle"),
    ("相思木柄", "Acacia wood handle"),
    ("榉木柄", "Beech wood handle"),
    ("半木柄", "Half-wood handle"),
    ("全木柄", "Full wood handle"),
    ("扁木柄", "Flat wood handle"),
    ("圆木柄", "Round wood handle"),
    ("扁管柄", "Flat tube handle"),
    ("弯管柄", "Curved tube handle"),
    ("圆管柄", "Round tube handle"),
    ("木纹柄", "Wood-grain handle"),
    ("橡塑柄", "Rubberised handle"),
    ("塑料柄", "Plastic handle"),
    ("灰柄", "Grey handle"),
]

MATERIALS = [("硅胶", "Silicone"), ("尼龙", "Nylon")]

# size / grade words that appear stuck to the item name
QUALIFIERS = [
    ("小号", "small"), ("中号", "medium"), ("大号", "large"),
    ("多用", "multi-purpose"), ("十二", "12-hole"), ("黑色", ""), ("白色", ""),
    ("小", "small"), ("中", "medium"), ("大", "large"),
]

HEADS = [
    ("意粉勺", "spaghetti server"),
    ("土豆压", "potato masher"),
    ("打蛋器", "whisk"),
    ("大圆漏", "round slotted spoon"),
    ("小刮铲", "small spatula turner"),
    ("大刮铲", "large spatula turner"),
    ("小刮刀", "small scraper"),
    ("大刮刀", "large scraper"),
    ("小抹刀", "small icing spatula"),
    ("中抹刀", "medium icing spatula"),
    ("大抹刀", "large icing spatula"),
    ("挖芯器", "apple corer"),
    ("刮铲", "spatula turner"),
    ("刮刀", "scraper"),
    ("抹刀", "icing spatula"),
    ("漏铲", "slotted turner"),
    ("密铲", "solid turner"),
    ("大铲", "large turner"),
    ("漏勺", "slotted spoon"),
    ("密勺", "solid spoon"),
    ("汤勺", "soup ladle"),
    ("网漏", "mesh strainer"),
    ("线漏", "wire strainer"),
    ("面粉筛", "flour sifter"),
    ("压蒜器", "garlic press"),
    ("削皮刀", "peeler"),
    ("水果刀", "fruit knife"),
    ("打蛋勺", "egg whisk"),
    ("肉锤", "meat tenderiser"),
    ("开瓶器", "bottle opener"),
    ("开罐器", "can opener"),
    ("披萨刀", "pizza cutter"),
    ("比萨刀", "pizza cutter"),
    ("蛋糕铲", "cake server"),
    ("烧烤夹", "BBQ tong"),
    ("食物夹", "kitchen tong"),
    ("砧板", "cutting board"),
    ("保鲜盒", "food container"),
    ("密封罐", "storage jar"),
    ("沥水篮", "colander"),
    ("淘米篮", "rice washing bowl"),
    ("调味盒", "spice box"),
    ("置物架", "kitchen rack"),
    ("挂钩", "hook"),
    ("隔热垫", "heat pad"),
    ("隔热手套", "oven mitt"),
    ("围裙", "apron"),
    ("抹布", "cleaning cloth"),
    ("厨具套装", "utensil set"),
    ("刨", "plane"),
    ("刀", "knife"),
    ("夹", "tongs"),
    ("铲", "turner"),
    ("勺", "spoon"),
    ("刷子", "pastry brush"),
    ("套装", "set"),
    ("7件套", "7-piece set"),
    ("12件套", "12-piece set"),
]


def english_name(zh, code="", size_note=""):
    """Build a readable English product name from a Chinese name.

    Result shape: "<Material> <head>, <handle>" — e.g.
      '榉木柄硅胶意粉勺' -> 'Silicone spaghetti server, beech wood handle'
    """
    s = clean_text(zh).replace("\n", "")
    if not s:
        return ""

    handle = ""
    for zh_h, en_h in HANDLES:
        if s.startswith(zh_h):
            handle = en_h
            s = s[len(zh_h):]
            break

    material = ""
    for zh_m, en_m in MATERIALS:
        if zh_m in s:
            material = en_m
            s = s.replace(zh_m, "", 1)
            break

    head = ""
    for zh_head, en_head in sorted(HEADS, key=lambda x: -len(x[0])):
        if zh_head in s:
            head = en_head
            s = s.replace(zh_head, "", 1)
            break

    leftover = re.sub(r"[\s\-/]+", " ", s).strip()

    core = " ".join([b for b in (material, head) if b]).strip()
    if not core:
        core = head or material or leftover or zh

    # translate leftover qualifiers (小 / 中 / 大 / 十二 …) and drop stray CJK
    if leftover:
        for zh_q, en_q in QUALIFIERS:
            leftover = leftover.replace(zh_q, (" " + en_q + " ") if en_q else " ")
        leftover = re.sub(r"[\s\-/]+", " ", leftover).strip()
        leftover = re.sub(r"[\u4e00-\u9fff]+", " ", leftover).strip()
        if leftover:
            core = f"{leftover} {core}"

    name = core[0].upper() + core[1:] if core else zh
    tail = []
    if handle:
        tail.append(handle)
    if size_note:
        tail.append(size_note)
    if tail:
        name = f"{name}, {', '.join(tail)}"
    return name.strip()


# ------------------------------------------------------------- material pairs
PACKING_EN = {
    "绑卡": "Carded", "彩盒": "Colour box", "清装": "Bulk", "吊卡": "Blister card",
    "白盒": "White box", "礼盒": "Gift box", "吸塑": "Blister", "散装": "Loose",
    "OPP袋": "OPP bag", "PP袋": "PP bag", "中盒": "inner box", "内盒": "inner box",
    "外箱": "outer carton", "套装": "set", "混装": "assorted", "卡纸": "hang card",
}

COLOUR_EN = {
    "黑色": "Black", "白色": "White", "灰色": "Grey", "绿色": "Green", "红色": "Red",
    "蓝色": "Blue", "银色": "Silver", "粉色": "Pink", "米色": "Beige", "棕色": "Brown",
    "原木色": "Natural wood", "黑": "Black", "白": "White", "灰": "Grey", "绿": "Green",
    "彩": "Assorted", "混色": "Assorted",
}


def _localize(value, table):
    s = clean_text(value)
    if not s:
        return ""
    out = []
    for part in re.split(r"\s*[/,、]\s*", s):
        part = part.strip()
        if not part:
            continue
        if part in table:
            out.append(table[part])
            continue
        cleaned = re.sub(r"[\u4e00-\u9fff]", "", part).strip()
        out.append(cleaned or part)
    return " / ".join(out)


def packing_en(value):
    """Translate a packing phrase, including composite notes such as
    '清装 · 24PCS/中盒' -> 'Bulk · 24PCS / inner box'."""
    s = clean_text(value)
    if not s:
        return ""
    s = re.sub(r"\s*\n\s*", " · ", s)
    for zh, en in sorted(PACKING_EN.items(), key=lambda x: -len(x[0])):
        s = s.replace(zh, en)
    # any remaining CJK is dropped rather than shown to a non-Chinese reader
    s = re.sub(r"[\u4e00-\u9fff]+", " ", s)
    s = re.sub(r"\s*/\s*", " / ", s)
    s = re.sub(r"\s*·\s*", " · ", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"^[\s·/]+|[\s·/]+$", "", s)
    return s.strip()


def colour_en(value):
    return _localize(value, COLOUR_EN)


def material_en(raw):
    """Human-readable English material string for the spec table."""
    s = clean_text(raw)
    if not s:
        return ""
    # longest Chinese term first so 橡胶木 / 黑胡桃 win over bare 木
    pairs = [
        ("沙比利木", "Sapele wood"), ("橡胶木", "Rubberwood"), ("橡木", "Oak wood"),
        ("榉木", "Beech"), ("相思木", "Acacia"), ("黑胡桃", "Black walnut"),
        ("不锈钢", "stainless steel"), ("铁电镀", "plated iron"), ("电镀", "plated"),
        ("硅胶", "Silicone"), ("尼龙", "Nylon"), ("塑料", "Plastic"), ("木", "wood"),
    ]
    # separate a glued grade BEFORE translating: 沙比利木430SS -> 沙比利木 430SS
    s = re.sub(r"(?<=[^\x00-\x7f])(?=\d{2,3})", " ", s)
    for zh, en in sorted(pairs, key=lambda x: -len(x[0])):
        s = s.replace(zh, en)
    # any 2-3 digit grade, optionally suffixed SS, becomes "<grade> stainless steel"
    s = re.sub(r"(?<![0-9.])(\d{2,3})\s*(?:SS\b|ss\b)?", r"\1 stainless steel", s)
    s = re.sub(r"\s*\+\s*", " + ", s)
    s = re.sub(r"\s{2,}", " ", s)

    # drop duplicated segments while keeping order (410 + 410 -> 410)
    parts, seen = [], set()
    for part in s.split(" + "):
        part = part.strip()
        if not part:
            continue
        key = part.lower()
        if key in seen:
            continue
        seen.add(key)
        parts.append(part)
    return " + ".join(parts).strip()


if __name__ == "__main__":
    tests = [
        "叉/L01\nFork",
        "P柄小号土豆压/M-P68（6cm)/Potato press",
        "1-P110/中漏铲",
        "P117/线漏16CM",
        "P柄叉/M-P01/Fork",
        "P柄黑色尼龙十二漏/M-P86/Nylon twelve leaks",
        "线漏(16CM)/L117\nWire leakage",
    ]
    for t in tests:
        print(repr(t), "->", parse_multipart_name(t, "P"))
    print()
    for zh in ["灰柄尼龙土豆压", "榉木柄硅胶意粉勺", "镀金尼龙柄硅胶\n刮铲",
               "圆木柄硅胶大抹刀", "半木柄硅胶7件套", "镀玫瑰金圆管柄硅胶刮刀",
               "黑胡桃柄硅胶刷子"]:
        print(zh.replace("\n", ""), "->", english_name(zh))
    print()
    for m in ["沙比利木+420SS", "410+430SS+420SS", "硅胶+PP", "尼龙+PP", "410+10SS", "沙比利木+201SS"]:
        print(m, "->", material_en(m))
