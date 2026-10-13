# -*- coding: utf-8 -*-
"""Extract quotation rows + image anchors from the three XLSX workbooks."""
import io, json, os, re, sys, zipfile
import openpyxl
from openpyxl.utils import get_column_letter

sys.stdout.reconfigure(encoding="utf-8")

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILES = [
    ("L", "L柄小厨具(KITCHEN TOOLS)盛美报价单.xlsx"),
    ("P", "P柄小厨具(KITCHEN TOOLS)盛美报价单.xlsx"),
    ("S", "硅胶&尼龙厨具(Silica gel)盛美报价单.xlsx"),
]
OUT = os.path.join(os.path.dirname(__file__), "raw")
os.makedirs(OUT, exist_ok=True)


def anchor_map(xlsx):
    """Map xl/media file -> (from_col, from_row, to_col, to_row) from drawing1.xml."""
    z = zipfile.ZipFile(xlsx)
    rels = z.read("xl/drawings/_rels/drawing1.xml.rels").decode("utf-8")
    rel = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
    draw = z.read("xl/drawings/drawing1.xml").decode("utf-8")
    out = []
    for m in re.finditer(r"<xdr:(oneCellAnchor|twoCellAnchor)\b(.*?)</xdr:\1>", draw, re.S):
        body = m.group(2)
        rid = re.search(r'r:embed="([^"]+)"', body)
        if not rid:
            continue
        frm = re.search(
            r"<xdr:from>\s*<xdr:col>(\d+)</xdr:col>.*?<xdr:row>(\d+)</xdr:row>", body, re.S
        )
        to = re.search(
            r"<xdr:to>\s*<xdr:col>(\d+)</xdr:col>.*?<xdr:row>(\d+)</xdr:row>", body, re.S
        )
        target = rel.get(rid.group(1))
        out.append(
            {
                "media": os.path.basename(target) if target else None,
                "col": int(frm.group(1)) + 1 if frm else None,
                "row": int(frm.group(2)) + 1 if frm else None,
                "to_col": int(to.group(1)) + 1 if to else None,
                "to_row": int(to.group(2)) + 1 if to else None,
            }
        )
    return out


def clean(v):
    if v is None:
        return ""
    if isinstance(v, float) and v == int(v):
        return int(v)
    s = str(v).replace("_x000D_", "").strip()
    return re.sub(r"\s*\n\s*", "\n", s)


for key, fname in FILES:
    path = os.path.join(SRC, fname)
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active

    rows = []
    for r in range(1, ws.max_row + 1):
        row = [clean(ws.cell(r, c).value) for c in range(1, ws.max_column + 1)]
        if any(str(x) != "" for x in row):
            rows.append({"r": r, "cells": row})

    data = {
        "key": key,
        "file": fname,
        "sheet": ws.title,
        "max_row": ws.max_row,
        "max_col": ws.max_column,
        "merged": [str(x) for x in ws.merged_cells.ranges],
        "col_widths": {
            k: (v.width if v.width else None) for k, v in ws.column_dimensions.items()
        },
        "row_heights": {
            str(k): (v.height if v.height else None) for k, v in ws.row_dimensions.items()
        },
        "rows": rows,
        "images": anchor_map(path),
    }
    with io.open(os.path.join(OUT, f"{key}.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)

    print(f"[{key}] {fname}")
    print(f"    sheet={ws.title} rows={ws.max_row} cols={ws.max_column} imgs={len(data['images'])}")
    print(f"    row3 headers: {rows[2]['cells'][:11] if len(rows) > 2 else None}")
    print(f"    last rows:")
    for r in rows[-4:]:
        print(f"      r{r['r']}: {r['cells'][:11]}")
    anchors = sorted([i for i in data["images"] if i["col"] and i["row"]], key=lambda x: (x["row"], x["col"]))
    print(f"    first 3 anchors: {anchors[:3]}")
    print(f"    anchor cols used: {sorted(set(i['col'] for i in data['images']))}")
    print()
