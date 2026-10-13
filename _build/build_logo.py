# -*- coding: utf-8 -*-
"""Extract the SKit trademark from the registration PDF as web-ready logo assets.

The PDF draws the mark as vector paths, so we rasterise page 1 at the highest
resolution the renderer allows and rebuild a transparency channel from the
white page background, keeping the gold gradient and the anti-aliased edges.

Outputs (site/assets/img/brand/):
  skit-logo.png / .webp       transparent, dark artwork  (for light surfaces)
  skit-logo-white.png/.webp   knocked out to white       (for dark surfaces)
  skit-logo-512.png           512 px wide, for manifest/icons
  skit-favicon-*.png          favicon sizes
  skit-logo-on-dark.png       preview composed on ink, for eyeballing
"""
import os, shutil, subprocess, sys

from PIL import Image, ImageChops

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "site", "assets", "img", "brand")
WORK = os.path.join(HERE, "tm")

NODE = r"C:\Users\haji\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe"
CLI = (r"C:\Users\haji\AppData\Local\Programs\DeepSeek Harness\resources"
       r"\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js")
PDF = (r"C:\Users\haji\Documents\xwechat_files\wxid_dcxdczw0a74e22_27e6"
       r"\msg\file\2026-10\SKit商标.pdf")

INK = (14, 28, 43)


# The full A4 page hits the renderer's 16 Mpx tile limit, and the mark only
# occupies a small part of it. Cropping the page box to the mark first means
# the maximum permitted density (600 dpi) lands almost entirely on the artwork:
# ~162 x 85 pt of mark -> ~1355 x 707 px, ample for a 2x display at 200 px.
CROP_DPI = 150
TARGET_DPI = 600


def measure_mark():
    """Render small, trim to the artwork, and convert px -> PDF points."""
    out = os.path.join(WORK, f"probe{CROP_DPI}")
    png = os.path.join(out, "page-0001.png")
    if not os.path.exists(png):
        if os.path.isdir(out):
            shutil.rmtree(out)
        os.makedirs(WORK, exist_ok=True)
        subprocess.run([NODE, CLI, "render", "--input", PDF, "--output-dir", out,
                        "--pages", "1", "--dpi", str(CROP_DPI)],
                       capture_output=True, text=True)
    im = Image.open(png)
    scale = 72.0 / CROP_DPI                       # px -> PDF points
    box = content_box(im, pad=0)
    x0, y0, x1, y1 = [v * scale for v in box]
    # PDF user space has its origin at the bottom-left, images at top-left
    page_h = im.size[1] * scale
    top = page_h - y1
    bottom = page_h - y0
    pad = 10.0
    return (max(0.0, x0 - pad), max(0.0, top - pad),
            x1 + pad, min(page_h, bottom + pad)), im.size


def pdf_with_crop(box):
    """Write a copy of the PDF whose page box is cropped to `box`."""
    x0, y0, x1, y1 = box
    dst = os.path.join(WORK, "cropped.pdf")
    raw = open(PDF, "rb").read()
    old = b"/MediaBox [-0.0000 -0.0000 595.2756 841.8898]"
    if old not in raw:
        print("  ! MediaBox not found verbatim; using the full page")
        return PDF
    new = (f"/MediaBox [{x0:.4f} {y0:.4f} {x1:.4f} {y1:.4f}]"
           f"/CropBox [{x0:.4f} {y0:.4f} {x1:.4f} {y1:.4f}]").encode()
    open(dst, "wb").write(raw.replace(old, new, 1))
    return dst


def render():
    """Rasterise the cropped page at high resolution and return the PNG path."""
    box, probe_size = measure_mark()
    print(f"mark region on page: {box[2]-box[0]:.1f} x {box[3]-box[1]:.1f} pt "
          f"(probe {probe_size[0]}x{probe_size[1]} px @ {CROP_DPI} dpi)")

    source = pdf_with_crop(box)
    out = os.path.join(WORK, f"hi{TARGET_DPI}")
    png = os.path.join(out, "page-0001.png")
    if os.path.exists(png):
        print(f"render: reusing {os.path.relpath(png, ROOT)}")
        return png
    if os.path.isdir(out):
        shutil.rmtree(out)

    for dpi in (TARGET_DPI, 500, 400, 300):
        if os.path.isdir(out):
            shutil.rmtree(out)
        r = subprocess.run([NODE, CLI, "render", "--input", source,
                            "--output-dir", out, "--pages", "1", "--dpi", str(dpi)],
                           capture_output=True, text=True)
        if os.path.exists(png):
            im = Image.open(png)
            print(f"render: {im.size[0]}x{im.size[1]} px at {dpi} dpi")
            return png
        if "megapixel" not in r.stdout and "dpi must be" not in r.stdout:
            sys.exit(f"render failed at {dpi} dpi:\n{r.stdout}\n{r.stderr}")
    sys.exit("render failed at every resolution")


def content_box(im, pad=8):
    """Bounding box of the non-white artwork, with a little breathing room."""
    grey = im.convert("L")
    diff = ImageChops.difference(grey, Image.new("L", grey.size, 255))
    box = diff.getbbox()
    if not box:
        sys.exit("no content found on the page")
    x0, y0, x1, y1 = box
    return (max(0, x0 - pad), max(0, y0 - pad),
            min(im.size[0], x1 + pad), min(im.size[1], y1 + pad))


def trim(im, pad=8):
    """Crop to the non-white content box."""
    return im.crop(content_box(im, pad))


def to_alpha(im):
    """Turn artwork on a white page into RGBA with a soft alpha channel.

    The mark has a gold gradient and a dark wordmark, so a flat "white becomes
    transparent" key would eat the pale edge of the gradient. Instead the alpha
    is derived from how far each pixel is from the page white, which preserves
    the anti-aliasing and never shifts the hues. This transparent version is the
    one to use on BOTH light and dark surfaces.
    """
    rgb = im.convert("RGB")
    grey = rgb.convert("L")
    alpha = grey.point(lambda v: 0 if v >= 244 else min(255, int((244 - v) * 255 / 244)))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def knockout_white(im):
    """Solid white silhouette of the mark, for dark surfaces.

    The gold/brown artwork has poor contrast on the ink background, so the
    silhouette (alpha kept, colour replaced) is the correct treatment there.
    """
    white = Image.new("RGBA", im.size, (255, 255, 255, 255))
    white.putalpha(im.split()[-1])
    return white


def save_all(name, im):
    png = os.path.join(OUT_DIR, f"{name}.png")
    webp = os.path.join(OUT_DIR, f"{name}.webp")
    im.save(png, "PNG", optimize=True)
    im.save(webp, "WEBP", quality=92, method=5, lossless=False)
    return png, webp


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    png = render()
    page = Image.open(png)
    logo = trim(page)
    print(f"trimmed artwork: {logo.size[0]}x{logo.size[1]} px "
          f"(ratio {logo.size[0]/logo.size[1]:.2f})")

    alpha = to_alpha(logo)

    # main logo: keep the native render, it is already high resolution
    a = alpha
    if a.size[0] > 1600:
        h = int(round(a.size[1] * 1600 / a.size[0]))
        a = a.resize((1600, h), Image.LANCZOS)
        print(f"resized master to {a.size[0]}x{a.size[1]}")

    save_all("skit-logo", a)

    # white silhouette for dark surfaces (footer, photo bands, share cards)
    w = knockout_white(a)
    save_all("skit-logo-white", w)

    # square app icon / manifest
    side = max(a.size)
    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    canvas.paste(a, ((side - a.size[0]) // 2, (side - a.size[1]) // 2), a)
    icon = canvas.resize((512, 512), Image.LANCZOS)
    save_all("skit-logo-512", icon)

    # favicons: pad the mark so it is not clipped in a circle
    for size in (32, 180):
        pad = int(side * 0.14)
        sq = Image.new("RGBA", (side + pad * 2, side + pad * 2), (255, 255, 255, 0))
        sq.paste(a, (pad + (side - a.size[0]) // 2, pad + (side - a.size[1]) // 2), a)
        sq.resize((size, size), Image.LANCZOS).save(
            os.path.join(OUT_DIR, f"skit-favicon-{size}.png"), "PNG", optimize=True)

    # previews, to judge each variant on its real background
    prev = Image.new("RGB", (a.size[0] + 80, a.size[1] * 2 + 120), INK)
    prev.paste(w, (40, 40), w)                       # white silhouette on ink
    prev.paste(a, (40, a.size[1] + 80), a)           # colour artwork on ink
    prev.save(os.path.join(WORK, "preview-on-ink.png"), "PNG")

    print("\nwritten to site/assets/img/brand/:")
    for f in sorted(os.listdir(OUT_DIR)):
        p = os.path.join(OUT_DIR, f)
        print(f"  {f:28s} {os.path.getsize(p)/1024:8.1f} KB")


if __name__ == "__main__":
    main()
