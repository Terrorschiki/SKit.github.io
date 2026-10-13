# -*- coding: utf-8 -*-
"""Process the studio cover photographs into responsive web backgrounds.

Source: 网站封面图片/*.jpg — 12600x12600 studio shots (one 6300x6300 CMYK)
with the SKit logo composited in a corner.

Output: site/assets/img/cover/p01..p12 at 960/1440/1920/2560 px wide in both
JPEG and WebP, which is everything the CSS art-direction needs.
"""
import io, os, sys, warnings

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "网站封面图片")
OUT = os.path.join(ROOT, "site", "assets", "img", "cover")

WIDTHS = (960, 1440, 1920, 2560)
JPEG_Q = 82
WEBP_Q = 78


def main():
    if not os.path.isdir(SRC):
        sys.exit(f"missing source folder: {SRC}")
    os.makedirs(OUT, exist_ok=True)

    files = sorted(f for f in os.listdir(SRC) if f.lower().endswith((".jpg", ".jpeg", ".png")))
    print(f"source images: {len(files)}")

    total = 0
    for i, name in enumerate(files, 1):
        stem = f"p{i:02d}"
        src_path = os.path.join(SRC, name)
        im = Image.open(src_path)

        # CMYK (print) sources must be converted to sRGB before resizing
        if im.mode != "RGB":
            im = im.convert("RGB")
        else:
            im = im.copy()

        made = []
        for w in WIDTHS:
            if w > im.size[0]:
                continue
            h = int(round(im.size[1] * w / im.size[0]))
            resized = im.resize((w, h), Image.LANCZOS)

            jpg = os.path.join(OUT, f"{stem}-{w}.jpg")
            resized.save(jpg, "JPEG", quality=JPEG_Q, optimize=True, progressive=True)

            webp = os.path.join(OUT, f"{stem}-{w}.webp")
            resized.save(webp, "WEBP", quality=WEBP_Q, method=5)

            made.append((w, os.path.getsize(jpg) + os.path.getsize(webp)))
        total += sum(s for _, s in made)
        sizes = " ".join(f"{w}px={s/1024:.0f}KB" for w, s in made)
        print(f"  {stem}  <- {name[:28]:<30} {im.size[0]}x{im.size[1]}  {sizes}")

    print(f"\nwritten to {os.path.relpath(OUT, ROOT)}")
    print(f"total {total/1048576:.1f} MB across {len(WIDTHS)} widths x 2 formats")


if __name__ == "__main__":
    main()
