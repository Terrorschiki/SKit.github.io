# SKit Kitchenware — Quotation Portal

A static, multilingual product-quotation website built from three supplier price lists
(Chinese/English Excel workbooks) and published on GitHub Pages.

**Live site:** https://terrorschiki.github.io/SKit.github.io/

## Repository and hosting

This repository belongs to the **`Terrorschiki` organization** (not a personal account),
which owns several repositories:

| Repository | Purpose |
| --- | --- |
| `Terrorschiki.github.io` | The organization landing page (Jekyll blog), served at the domain root |
| `SKit.github.io` | **This project** — served at `https://terrorschiki.github.io/SKit.github.io/` |
| `blog_template`, `RESUME_TEMPLATE`, `Terrorschiki` | Other templates and private work |

Two hosting consequences are worth remembering:

- **The URL path is the repository name.** GitHub Pages serves a project repository from
  its **repository root**, so this site's `index.html` must sit at the root — the
  `/SKit.github.io/` segment comes from the repository name, not from a folder. Only a
  repository literally named `Terrorschiki.github.io` serves the bare domain.
- **`/assets/...` at the domain root belongs to the blog**, not to this site. These assets
  live under `/SKit.github.io/assets/...`, so the two sites never collide. A probe of
  `https://terrorschiki.github.io/assets/css/style.css` returns the blog theme, not ours.

Deployment runs through GitHub Actions (`.github/workflows/pages.yml`), which must stay at
the repository root — GitHub ignores workflow files placed anywhere else.

---

## What is in this repository

| Path | Contents |
| --- | --- |
| `index.html` | Home page — programmes, featured items, company summary |
| `collections.html` | Overview of the three product programmes |
| `collections/*.html` | One catalogue page per programme, with search / filter / sort / pagination |
| `products/*.html` | 445 generated product detail pages (specs, price, related items) |
| `about.html`, `contact.html`, `downloads.html`, `404.html` | Supporting pages |
| `assets/css/style.css` | Complete design system (single stylesheet) |
| `assets/js/app.js` | i18n, currency, quotation builder, lightbox, header behaviour |
| `assets/js/catalog.js` | Catalogue browser (search, filters, sorting, paging) |
| `assets/js/product.js` | Product detail rendering and related items |
| `assets/data/catalog.json` | The full extracted catalogue (445 items) |
| `assets/data/i18n/*.json` | UI dictionaries: English, Spanish, French, Chinese |
| `assets/products/*.jpg` | 1,329 optimised product images (thumb / card / full + banners) |
| `downloads/` | The original supplier price lists (PDF + Excel) |
| `sitemap.xml`, `robots.txt`, `.nojekyll` | SEO and GitHub Pages configuration |
| `_build/` | The Python build scripts that generated everything above |

## The three quotations

Each supplier price list became its own programme:

| Source workbook | Programme | Code source | Name source | Items |
| --- | --- | --- | --- | --- |
| `L柄小厨具(KITCHEN TOOLS)盛美报价单` | L-Handle (wood) | embedded in the name cell (`L01`, `M-P68`, `1-P110`) | name cell, Chinese + English | 119 |
| `P柄小厨具(KITCHEN TOOLS)盛美报价单` | P-Handle (stainless steel) | same as above | name cell, Chinese + English | 119 |
| `硅胶&尼龙厨具(Silica gel)盛美报价单` | Silicone & Nylon | separate `货号` column | Chinese name column | 207 |

Field mapping used for all three: `品名 → name`, `包装方式 → packing`, `价格 → price (USD)`,
`装箱数 → qty per carton`, `尺寸 → size`, `毛重 → gross weight`, `材质 → material`,
`体积 → CBM`, `备注 → inner packing`, `颜色 → colour`.

## Languages and currency

The interface ships in **English, Spanish, French and Chinese** (`assets/data/i18n/`).
The visitor's browser language is detected and their choice is remembered in
`localStorage`; the default is English. Prices are listed in USD and can be
displayed in EUR or ZAR using the reference rates in `app.js` (`CURRENCIES`).

## Features

- Full-text search across item code, names, material, size, packing and colour
- Category chips, material filter and four sort orders; grid and list layouts
- Product pages with complete carton data, enlargeable photos and related items
- **Quotation builder** — add items from any page, set quantities, then copy the list,
  download it as CSV, or send it straight through the contact form (WhatsApp or e-mail)
- Responsive from 360 px phones to wide desktop; print stylesheet included
- Structured data (Organization / CollectionPage / Product) and a full sitemap

## Rebuilding the site

The build is plain Python 3 (openpyxl + Pillow) and writes only into `site/`.

```powershell
python _build/extract.py         # dump raw workbook cells and image anchors to _build/raw/
python _build/build_catalog.py   # build site/data/catalog.json and process every product image
python _build/build_pages.py     # generate all HTML pages, sitemap.xml and robots.txt
python _build/deploy.py          # copy site/ to dist/ and verify image/page coverage
```

`build_catalog.py` skips images that already exist; pass `--force` to regenerate them,
or `--limit=N` to process only the first N images per programme.
`deploy.py` also prunes product images that no catalogue entry references any more.

## Editing content

- **Prices, names, specs** — edit `assets/data/catalog.json` (or the `_build` scripts and rebuild).
- **Wording and translations** — edit `assets/data/i18n/en.json` (the base dictionary);
  every other language falls back to English for missing keys.
- **Colours, spacing, typography** — all design tokens live in the `:root` block of
  `assets/css/style.css`.
- **Contact details** — `PHONE1`, `PHONE2`, `FAX`, `WHATSAPP`, `EMAIL` at the top of
  `_build/build_pages.py`, then regenerate the pages.

> **Before going live, check the contact details.** The phone numbers, WeChat and fax
> number come from the supplier price lists and are correct. The e-mail address
> `sales@skit-kitchenware.com` is a placeholder used by the contact form and the footer —
> replace it with the real mailbox (or delete the `mailto:` links and keep the phone and
> WhatsApp buttons) and rebuild.

## Notes

- Prices are the supplier's list prices in USD, **excluding tax**, and are indicative
  only; they are confirmed in a written offer. The site states this in the footer,
  the quotation drawer and every product page.
- Three items in the L-handle price list (`L64`, `L66`, `L99`) have no photograph in
  the source workbook; those pages show a branded "photo on request" placeholder.
- Carton data (quantity, gross weight, CBM) is present for 442 of the 445 items; the
  three without it are the same items that have no photograph.
- The Excel workbooks embedded in `downloads/` are the original supplier files, kept
  for offline costing and forwarding to buyers on request.
