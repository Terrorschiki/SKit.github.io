# -*- coding: utf-8 -*-
"""Assemble the publishable GitHub Pages tree in dist/."""
import io, os, re, shutil, sys, json

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
DIST = os.path.join(ROOT, "dist")

SKIP_DIRS = {"__pycache__"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}


def clean_prev():
    """Remove non-catalogue leftovers from a previous copy, keep product images."""
    for name in ("assets", "data", "collections", "products", "downloads"):
        p = os.path.join(SITE, name)
        if name == "assets":
            for sub in ("css", "js", "img", "data"):
                if os.path.isdir(os.path.join(p, sub)):
                    shutil.rmtree(os.path.join(p, sub))
        continue


def copy_tree(src, dst):
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel = os.path.relpath(root, src)
        target = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(target, exist_ok=True)
        for f in files:
            if f in SKIP_FILES:
                continue
            shutil.copy2(os.path.join(root, f), os.path.join(target, f))


def main():
    if not os.path.isdir(SITE):
        sys.exit("site/ not found — run the builders first")
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST, exist_ok=True)
    copy_tree(SITE, DIST)

    # GitHub Pages needs .nojekyll for paths that start with underscore and to
    # skip Jekyll processing entirely.
    with io.open(os.path.join(DIST, ".nojekyll"), "w") as fh:
        fh.write("")

    files = sum(len(f) for _, _, f in os.walk(DIST))
    size = sum(os.path.getsize(os.path.join(r, f))
               for r, _, fs in os.walk(DIST) for f in fs)
    print(f"dist: {files} files, {size/1048576:.1f} MB")

    # sanity: every catalogue product must have its images on disk
    cat = json.load(io.open(os.path.join(DIST, "data", "catalog.json"), encoding="utf-8"))
    missing = []
    for p in cat["products"]:
        for tag in ("thumb", "card", "full"):
            f = os.path.join(DIST, "assets", "products", f"{p['id']}-{tag}.jpg")
            if not os.path.exists(f):
                missing.append(f"{p['id']}-{tag}")
    print(f"products: {len(cat['products'])}  missing images: {len(missing)}")
    if missing:
        print("  first missing:", missing[:10])

    # sanity: every product page exists
    miss_pages = [p["id"] for p in cat["products"]
                  if not os.path.exists(os.path.join(DIST, "products", p["id"] + ".html"))]
    print(f"missing product pages: {len(miss_pages)}")
    if miss_pages:
        print("  first:", miss_pages[:10])
    for k in ("L", "P", "S"):
        print(f"  set {k}: {sum(1 for p in cat['products'] if p['set']==k)} items")


if __name__ == "__main__":
    main()
