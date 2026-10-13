# -*- coding: utf-8 -*-
"""Survey what is available for rendering a PDF to images."""
import glob, importlib, os, shutil, sys

sys.stdout.reconfigure(encoding="utf-8")

print("=== python modules ===")
for mod in ("fitz", "pypdfium2", "pdf2image", "pypdf", "PyPDF2", "PIL"):
    try:
        m = importlib.import_module(mod)
        print(f"  {mod:12s} OK    {getattr(m, '__version__', '?')}")
    except Exception as e:
        print(f"  {mod:12s} --    {type(e).__name__}")

print("\n=== PATH tools ===")
for t in ("pdftoppm", "pdftocairo", "gswin64c", "gswin32c", "magick", "mutool", "qpdf"):
    print(f"  {t:12s} {shutil.which(t) or '--'}")

print("\n=== LibreOffice (bundled) ===")
base = r"C:\Users\haji\AppData\Local\Programs\DeepSeek Harness\resources"
hits = glob.glob(os.path.join(base, "**", "soffice*"), recursive=True)
for h in hits[:10]:
    print(f"  {h}")

print("\n=== Chrome (can print PDF pages to image via headless) ===")
for c in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"):
    print(f"  {'OK ' if os.path.exists(c) else '-- '} {c}")
