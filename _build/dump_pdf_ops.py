# -*- coding: utf-8 -*-
"""Dump the vector operators of each page content stream in the trademark PDF."""
import collections, re, sys, zlib

sys.stdout.reconfigure(encoding="utf-8")

PDF = r"C:\Users\haji\Documents\xwechat_files\wxid_dcxdczw0a74e22_27e6\msg\file\2026-10\SKit商标.pdf"
raw = open(PDF, "rb").read()

# ---- enumerate every object and its stream -------------------------------
objs = {}
for m in re.finditer(rb"(\d+)\s+0\s+obj\b(.*?)(?=endobj)", raw, re.S):
    num = int(m.group(1))
    body = m.group(2)
    sm = re.search(rb"stream\r?\n", body)
    data = None
    if sm:
        start = sm.end()
        end = body.find(b"endstream", start)
        blob = body[start:end]
        if b"/FlateDecode" in body[: sm.start()]:
            try:
                data = zlib.decompress(blob)
            except Exception:
                data = None
        else:
            data = blob
    objs[num] = {"dict": body[: sm.start()] if sm else body, "stream": data}

print(f"objects: {len(objs)}")

# ---- which objects hold page content ------------------------------------
content_ids = []
for num, o in objs.items():
    if b"/Type /Page" in o["dict"] or b"/Type/Page" in o["dict"]:
        m = re.search(rb"/Contents\s+(\d+)\s+0\s+R", o["dict"])
        if m:
            content_ids.append(int(m.group(1)))
print("page content stream objects:", content_ids)

OP_RE = re.compile(rb"(?<![A-Za-z])([A-Za-z]{1,2}\*?|'|\")(?![A-Za-z])")
WATCH = {"m", "l", "c", "v", "y", "h", "re", "f", "f*", "F", "S", "s", "B", "B*", "b", "b*",
         "W", "W*", "n", "rg", "RG", "g", "G", "k", "K", "sc", "scn", "SC", "SCN", "cs", "CS",
         "gs", "cm", "q", "Q", "BT", "ET", "Tj", "TJ", "Tm", "Td", "TD", "Tf", "Do", "sh"}

for cid in content_ids:
    data = objs[cid]["stream"]
    if not data:
        print(f"\n[{cid}] no stream")
        continue
    ops = collections.Counter()
    for m in OP_RE.finditer(data):
        op = m.group(1).decode()
        if op in WATCH:
            ops[op] += 1
    print(f"\n[{cid}] {len(data)} bytes decompressed")
    print("   ops:", dict(sorted(ops.items(), key=lambda x: -x[1])))

    # colour operators tell us whether the mark is a bitmap-free vector logo
    print("   colours rg/RG:", re.findall(rb"([\d.]+ [\d.]+ [\d.]+ (?:rg|RG))", data)[:6])
    print("   colours k/K  :", re.findall(rb"([\d.]+ [\d.]+ [\d.]+ [\d.]+ (?:k|K))", data)[:6])
    print("   shading /sh  :", set(re.findall(rb"/(\w+)\s+sh", data)))
    print("   text ops     :", b"BT" in data, b"Tj" in data, b"TJ" in data)
    print("   fonts        :", set(re.findall(rb"/(F\d+)\s+[\d.]+\s+Tf", data)))
    print("   head 400     :", data[:400][:400])

    # bounding box of all path coordinates
    nums = [float(x) for x in re.findall(rb"-?\d+\.?\d*", data[:200000])][:4000]
    if nums:
        print(f"   numeric range: {min(nums):.1f} .. {max(nums):.1f}")
