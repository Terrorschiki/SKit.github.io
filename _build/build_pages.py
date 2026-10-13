# -*- coding: utf-8 -*-
"""Generate every HTML page of the SKit quotation site from the extracted catalogue."""
import io, json, os, re, sys, html, datetime

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(SITE, "data")

with io.open(os.path.join(DATA, "catalog.json"), encoding="utf-8") as fh:
    CAT = json.load(fh)

PRODUCTS = CAT["products"]
BY_ID = {p["id"]: p for p in PRODUCTS}
SETS = {s["key"]: s for s in CAT["sets"]}

PHONE1, PHONE2 = "13600593111", "18958482067"
FAX = "0579-85181067"
WHATSAPP = "8613600593111"
EMAIL = "sales@skit-kitchenware.com"
TODAY = datetime.date.today().isoformat()
YEAR = datetime.date.today().year

SET_META = {
    "L": dict(
        slug="kitchen-tools-l-handle",
        title_i18n="col.L.title", desc_i18n="col.L.desc", brand_i18n="col.L.brand",
        tag="L-Handle · Wood",
        page_title="L-Handle Kitchen Tools (Wood Handle) — Wholesale Price List",
        meta_desc=("Wholesale L-handle kitchen tools: sapele and rubberwood handles with 420/430 "
                   "stainless steel heads. Fork, knife, turner, whisk, pizza cutter and more. "
                   "FOB prices, carton data and MOQ per item."),
    ),
    "P": dict(
        slug="kitchen-tools-p-handle",
        title_i18n="col.P.title", desc_i18n="col.P.desc", brand_i18n="col.P.brand",
        tag="P-Handle · Stainless Steel",
        page_title="P-Handle Kitchen Tools (Stainless Steel) — Wholesale Price List",
        meta_desc=("Wholesale P-handle stainless steel kitchen tools with 410/420SS heads. "
                   "Hygienic, dishwasher-safe utensils for professional kitchens, importers and "
                   "supermarket programmes. FOB prices and carton data included."),
    ),
    "S": dict(
        slug="silicone-nylon-kitchenware",
        title_i18n="col.S.title", desc_i18n="col.S.desc", brand_i18n="col.S.brand",
        tag="Silicone &amp; Nylon",
        page_title="Silicone &amp; Nylon Kitchenware — Wholesale Price List",
        meta_desc=("Wholesale silicone and nylon kitchen utensils with PP cores: non-stick safe "
                   "turners, spatulas, ladles, strainers and baking tools. Colour options, MOQ "
                   "and carton data per item."),
    ),
}

# English fallbacks rendered into the HTML (JS swaps them per language).
SPEC_LABELS = {
    "spec.itemNo": "Item no.",
    "spec.material": "Material",
    "spec.size": "Size (cm)",
    "spec.packing": "Packing",
    "spec.qty": "Qty per carton",
    "spec.gw": "G.W. / ctn",
    "spec.cbm": "CBM / ctn",
    "spec.colour": "Colour",
    "spec.note": "Inner packing",
}

ICONS = {
    "truck": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7h11v10H3zM14 10h4l3 3v4h-7z"/><circle cx="7" cy="17.5" r="1.6"/><circle cx="17" cy="17.5" r="1.6"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5c0 4.4-3 8.2-7 10-4-1.8-7-5.6-7-10V6z"/><path d="m9 12 2 2 4-4"/></svg>',
    "box": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="m3 7.5 9-4.5 9 4.5v9L12 21l-9-4.5z"/><path d="M3 7.5 12 12l9-4.5M12 12v9"/></svg>',
    "chat": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12a7.5 7.5 0 0 1-11 6.7L4 20l1.3-4A7.5 7.5 0 1 1 20 12z"/></svg>',
    "globe": '<svg class="globe" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 2.5 15.4 0 18M12 3c-2.5 2.6-2.5 15.4 0 18"/></svg>',
    "caret": '<svg class="caret" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2"><path d="m2 4 4 4 4-4"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h3.5l1.8 4.4-2.2 1.5a12 12 0 0 0 6 6l1.5-2.2L20 14.5V18a2 2 0 0 1-2.2 2A16.8 16.8 0 0 1 3 5.2 2 2 0 0 1 5 3z"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 7 8 6 8-6"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.6"/></svg>',
    "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5.5l3.5 2"/></svg>',
    "download": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11m0 0 4-4m-4 4-4-4M5 19h14"/></svg>',
    "cart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h2l2.3 11.4a1.8 1.8 0 0 0 1.8 1.4h7.6a1.8 1.8 0 0 0 1.8-1.4L20 7.5H6"/><circle cx="10" cy="20" r="1.3"/><circle cx="17.5" cy="20" r="1.3"/></svg>',
    "grid": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3.5" y="3.5" width="7" height="7" rx="1.4"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.4"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.4"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.4"/></svg>',
    "rows": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg>',
    "search": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m5 13 4 4L19 7"/></svg>',
    "whatsapp": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.5 15.2L2 22l4.9-1.4A10 10 0 1 0 12 2zm5.3 14.1c-.2.6-1.2 1.2-1.7 1.2-.4 0-1 .1-2.7-.6-2.2-.9-3.6-3.1-3.7-3.3-.1-.2-.9-1.2-.9-2.3s.6-1.6.8-1.8c.2-.2.4-.3.6-.3h.4c.1 0 .3-.1.5.4l.6 1.5c.1.1.1.3 0 .5l-.4.5c-.1.1-.2.3 0 .5.2.3.7 1.1 1.4 1.7.9.8 1.4 1 1.6 1.1.2.1.3.1.5-.1l.7-.8c.2-.2.3-.2.5-.1l1.5.7c.2.1.4.2.4.3.1.1.1.7-.1 1.4z"/></svg>',
}

# --------------------------------------------------------------------- shell
def head(title, desc, rel, canonical, extra_css="", og_img=None, og_type="website",
         jsonld=None, keywords="", scripts=()):
    css = f'<link rel="stylesheet" href="{rel}assets/css/style.css">'
    if extra_css:
        css += f'\n  <link rel="stylesheet" href="{rel}assets/css/{extra_css}">'
    ld = f'\n  <script type="application/ld+json">{jsonld}</script>' if jsonld else ""
    extra = "".join(f'\n  <script src="{rel}assets/js/{s}" defer></script>' for s in scripts)
    img = og_img or f"{rel}assets/img/og-cover.jpg"
    return f"""<!DOCTYPE html>
<html lang="en" data-base="{rel}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  {f'<meta name="keywords" content="{keywords}">' if keywords else ''}
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="SKit Kitchenware">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:image" content="{img}">
  <meta property="og:url" content="{canonical}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#0e1c2b">
  <link rel="icon" href="{rel}assets/img/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="{rel}assets/img/favicon.svg">
  {css}
  <script>window.SKIT_BASE = "{rel}";</script>
  <script>window.addEventListener('error',function(e){{var m='[SKit] '+(e.message||'')+' @ '+(e.filename||'')+':'+(e.lineno||'');if(window.console)console.error(m);}});</script>
  <script src="{rel}assets/js/app.js" defer></script>{extra}{ld}
</head>"""


def header(active, rel, body_attrs=""):
    def link(href, key, extra=""):
        cls = ' class="active"' if key == active else ""
        return f'<a href="{rel}{href}"{cls}{extra} data-i18n="{key}">{key}</a>'
    return f"""<body{(' ' + body_attrs) if body_attrs else ''}>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap-wide header-inner">
    <a class="brand" href="{rel}index.html" aria-label="SKit Kitchenware — home">
      <span class="brand-mark">S</span>
      <span class="brand-text">
        <span class="brand-name">SKit</span>
        <span class="brand-tag" data-i18n="meta.tagline">Kitchen tools manufacturer &amp; exporter</span>
      </span>
    </a>
    <nav class="nav" aria-label="Main">
      <a href="{rel}index.html"{' class="active"' if active == 'home' else ''} data-i18n="nav.home">Home</a>
      <a href="{rel}collections.html"{' class="active"' if active == 'catalog' else ''} data-i18n="nav.catalog">Products</a>
      <a href="{rel}about.html"{' class="active"' if active == 'about' else ''} data-i18n="nav.about">About us</a>
      <a href="{rel}downloads.html"{' class="active"' if active == 'downloads' else ''} data-i18n="nav.downloads">Downloads</a>
      <a href="{rel}contact.html"{' class="active"' if active == 'contact' else ''} data-i18n="nav.contact">Contact</a>
    </nav>
    <div class="header-tools">
      <div class="lang">
        <button class="lang-btn" type="button" data-lang-toggle aria-haspopup="true" aria-expanded="false" data-i18n-aria="nav.menu">
          {ICONS['globe']}<span data-lang-label>English</span>{ICONS['caret']}
        </button>
        <div class="lang-menu" role="menu">
          <button type="button" role="menuitem" data-lang="en"><span class="lang-flag">🇬🇧</span> English</button>
          <button type="button" role="menuitem" data-lang="es"><span class="lang-flag">🇪🇸</span> Español</button>
          <button type="button" role="menuitem" data-lang="fr"><span class="lang-flag">🇫🇷</span> Français</button>
          <button type="button" role="menuitem" data-lang="zh"><span class="lang-flag">🇨🇳</span> 中文</button>
        </div>
      </div>
      <a class="btn btn-ghost btn-sm" href="{rel}contact.html" data-i18n="nav.quote">Request a quotation</a>
      <button class="burger" type="button" data-burger aria-label="Menu" data-i18n-aria="nav.menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>"""


def drawer_and_fab(rel):
    return f"""<button class="fab" type="button" data-open-quote data-empty="1">
  <span class="fab-label" data-i18n="quote.title">Quotation</span>
  <span class="bubble">0</span>
</button>
<div class="drawer-scrim" data-close-quote></div>
<aside class="drawer" role="dialog" aria-modal="true" aria-label="Quotation">
  <div class="drawer-head">
    <div>
      <h3 data-i18n="quote.title">Quotation</h3>
      <div class="sub" data-i18n="quote.empty2">Add items from the catalogue to build a request.</div>
    </div>
    <button class="icon-btn" type="button" data-close-quote aria-label="Close">✕</button>
  </div>
  <div class="drawer-body"></div>
  <div class="drawer-foot" style="display:none"></div>
</aside>"""


def footer(rel):
    phone_items = "".join(
        f'<li><a href="tel:+86{p}">{p}</a></li>' for p in (PHONE1, PHONE2)
    )
    return f"""<footer class="site-footer">
  <div class="wrap-wide">
    <div class="footer-grid">
      <div>
        <div class="brand">
          <span class="brand-mark">S</span>
          <span class="brand-text"><span class="brand-name">SKit</span>
          <span class="brand-tag" data-i18n="meta.tagline">Kitchen tools manufacturer</span></span>
        </div>
        <p class="footer-about" data-i18n="footer.about">Kitchen tool manufacturer and exporter.</p>
      </div>
      <div>
        <h4 data-i18n="footer.explore">Explore</h4>
        <ul>
          <li><a href="{rel}index.html" data-i18n="nav.home">Home</a></li>
          <li><a href="{rel}collections.html" data-i18n="nav.catalog">Products</a></li>
          <li><a href="{rel}about.html" data-i18n="nav.about">About us</a></li>
          <li><a href="{rel}downloads.html" data-i18n="nav.downloads">Downloads</a></li>
          <li><a href="{rel}contact.html" data-i18n="nav.contact">Contact</a></li>
        </ul>
      </div>
      <div>
        <h4 data-i18n="footer.collections">Collections</h4>
        <ul>
          {''.join(f'<li><a href="{rel}collections/{SET_META[k]["slug"]}.html">{SET_META[k]["page_title"].split(" — ")[0]}</a></li>' for k in ("L", "P", "S"))}
        </ul>
      </div>
      <div>
        <h4 data-i18n="footer.contact">Get in touch</h4>
        <ul>
          {phone_items}
          <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
          <li data-i18n="footer.address">Yiwu, Zhejiang, China</li>
          <li>{ICONS['clock'].replace('<svg', '<svg style="width:14px;height:14px;display:inline;vertical-align:-2px;margin-right:6px;opacity:.6"')}<span data-i18n="contact.hoursV">Monday – Saturday, 08:30 – 18:00 (GMT+8)</span></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <div>© {YEAR} SKit Kitchenware · <span data-i18n="footer.rights">All rights reserved.</span></div>
      <div data-i18n="footer.disclaimer">Prices are indicative and exclude tax.</div>
    </div>
  </div>
</footer>
</body>
</html>"""


def write(rel_path, content):
    path = os.path.join(SITE, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def canonical(rel_path):
    p = rel_path.replace("index.html", "")
    return "https://terrorschiki.github.io/SKit.github.io/" + p


# ------------------------------------------------------- studio cover photos
# 网站封面图片/ -> assets/img/cover/pNN-{960,1440,1920,2560}.{jpg,webp}
#   p01 wood-grain L-handle set    p02 silicone + steel set   p03 silicone spatulas
#   p04 wood L-handle set          p05 silicone + steel set   p06 wood-handle silicone
#   p07 box graters                p08 stainless P-handle set p09 pizza & pastry tools
#   p10 turners and spatulas       p11 peelers and zesters    p12 whisks and strainers
COVER_BY_SET = {"L": "p04", "P": "p08", "S": "p06"}


def cover_picture(stem, rel, alt, cls="", sizes="100vw", eager=False,
                  width=1920, height=1080):
    """Responsive <picture> for a studio cover photo (WebP with JPEG fallback)."""
    srcset = ", ".join(f"{rel}assets/img/cover/{stem}-{w}.webp"
                       for w in (960, 1440, 1920, 2560))
    load = ' fetchpriority="high"' if eager else ' loading="lazy"'
    return (f'<picture>'
            f'<source type="image/webp" srcset="{srcset}" sizes="{sizes}">'
            f'<img class="{cls}" src="{rel}assets/img/cover/{stem}-1440.jpg" '
            f'alt="{html.escape(alt)}" width="{width}" height="{height}" '
            f'decoding="async"{load}>'
            f'</picture>')


# ------------------------------------------------------------ price helpers
def price_span(p, rel):
    return (f'<span data-price-usd="{p["price"]}">'
            f'{("$ %s" % p["price"]) if p["price"] != "" else "—"}</span>')


def lowest_price(setkey):
    vals = [float(p["price"]) for p in PRODUCTS
            if p["set"] == setkey and str(p["price"]).replace(".", "", 1).isdigit()]
    return min(vals) if vals else 0


# ------------------------------------------------------------------- HOME
def build_home():
    rel = ""
    featured = []
    for k in ("L", "P", "S"):
        pool = [p for p in PRODUCTS if p["set"] == k]
        picks = [p for p in pool if p["cat"] in ("turners", "strainers", "cutlery")][:6]
        if len(picks) < 6:
            picks += [p for p in pool if p not in picks][:6 - len(picks)]
        featured.extend(picks[:6])

    def card(p):
        name = p["name_en"] or p["name_zh"]
        return f"""<article class="prod-card">
  <div class="prod-media">
    <a href="products/{p['id']}.html" aria-label="{html.escape(name)}">
      <img src="assets/products/{p['id']}-thumb.jpg" alt="{html.escape(name)} — {html.escape(p['code'])}" loading="lazy" width="520" height="390">
    </a>
    <span class="prod-set">{SET_META[p['set']]['tag']}</span>
    <button class="prod-zoom" type="button" data-zoom="assets/products/{p['id']}-card.jpg" aria-label="Enlarge">+</button>
  </div>
  <div class="prod-body">
    <h3 class="prod-name"><a href="products/{p['id']}.html">{html.escape(name)}</a></h3>
    <div class="prod-sub">{html.escape(p['name_en'] if (p['name_en'] and p['name_en'] != name) else p['name_zh'])}</div>
    <div><span class="prod-code">{html.escape(p['code'])}</span></div>
    <div class="prod-specs">
      <div class="spec"><span data-i18n="spec.size">Size</span><span>{html.escape(p['size'])}</span></div>
      <div class="spec"><span data-i18n="spec.material">Material</span><span>{html.escape(p['material'])}</span></div>
    </div>
    <div class="prod-foot">
      <div class="price"><b>{price_span(p, '')}</b><small data-i18n="spec.perPiece">per piece</small></div>
      <button class="add-btn" type="button"
        data-add='{html.escape(json.dumps({"id": p["id"], "code": p["code"], "name_zh": p["name_zh"], "name_en": p["name_en"], "price": p["price"], "qty": p["qty"], "size": p["size"], "set": p["set"]}, ensure_ascii=False), quote=True)}'
        aria-label="Add to quotation">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
      </button>
    </div>
  </div>
</article>"""

    coll = ""
    for k in ("L", "P", "S"):
        m = SET_META[k]
        n = SETS[k]["count"]
        lo = lowest_price(k)
        coll += f"""<a class="coll-card" href="collections/{m['slug']}.html">
  <div class="coll-media">
    <img src="{SETS[k]['hero']}.jpg" alt="{html.escape(SETS[k]['title'])}" loading="lazy" width="1400" height="700">
    <span class="coll-tag">{m['tag']}</span>
  </div>
  <div class="coll-body">
    <h3 data-i18n="{m['title_i18n']}">Collection {k}</h3>
    <div class="sub" data-i18n="{m['brand_i18n']}">Handle</div>
    <div class="coll-meta">
      <span class="pill">{n} <span data-i18n="collections.items">items</span></span>
      <span class="pill accent" data-i18n="set.{k}.short">Set {k}</span>
    </div>
    <p style="font-size:13.6px;color:var(--ink-soft);margin:0 0 16px" data-i18n="{m['desc_i18n']}">Description</p>
    <div class="coll-foot">
      <div class="coll-price"><span data-i18n="collections.from">From</span><b>${lo:.2f}</b></div>
      <span class="btn btn-ghost btn-sm" data-i18n="collections.browse">View catalogue</span>
    </div>
  </div>
</a>"""

    total = len(PRODUCTS)
    cartons = sum(int(p["qty"]) for p in PRODUCTS if str(p["qty"]).isdigit())

    body = f"""{header('home', rel)}
<main id="main">
  <section class="hero">
    <div class="wrap-wide hero-grid">
      <div>
        <div class="eyebrow" data-i18n="collections.eyebrow">Product programmes</div>
        <h1 class="h-display h1" data-i18n="hero.title">Kitchen tools built for the world's kitchens</h1>
        <p class="lead" style="margin-top:18px" data-i18n="hero.sub">Three complete programmes…</p>
        <div class="hero-badges">
          <span class="badge">{ICONS['check']}<span data-i18n="hero.badge1">Factory direct pricing</span></span>
          <span class="badge">{ICONS['check']}<span data-i18n="hero.badge2">OEM &amp; ODM welcome</span></span>
          <span class="badge">{ICONS['check']}<span data-i18n="hero.badge3">Worldwide shipping</span></span>
        </div>
        <div class="hero-cta">
          <a class="btn btn-accent btn-lg" href="collections.html" data-i18n="hero.cta1">Browse the catalogue</a>
          <a class="btn btn-ghost btn-lg" href="contact.html" data-i18n="hero.cta2">Request a quotation</a>
        </div>
        <p class="hero-note" data-i18n="hero.note">Prices EXW/FOB Ningbo · VAT excluded</p>
        <div class="hero-stats">
          <div><div class="stat-n">{len(SETS)}</div><div class="stat-l" data-i18n="hero.stats.sets">Product programmes</div></div>
          <div><div class="stat-n">{total}</div><div class="stat-l" data-i18n="hero.stats.items">Quotable item lines</div></div>
          <div><div class="stat-n">{len(PRODUCTS) and '100%'}</div><div class="stat-l" data-i18n="hero.stats.ship">Carton data included</div></div>
        </div>
      </div>
      <div class="hero-visual">
        <div class="float-chip chip-a"><span class="dot"></span><span data-i18n="hero.badge1">Factory direct pricing</span></div>
        <div class="float-chip chip-b"><span class="dot"></span>{total} <span data-i18n="hero.products">item lines</span></div>
        <figure class="hero-photo">
          {cover_picture('p06', '', 'SKit wooden-handle kitchen tools with silicone heads on marble',
                         sizes="(max-width: 1080px) 92vw, 46vw", eager=True,
                         width=1920, height=1920)}
          <div class="hero-tiles">
            {''.join(f'<a href="collections/{SET_META[k]["slug"]}.html"><b>{SETS[k]["count"]}</b><span data-i18n="set.{k}.short">{k}</span></a>' for k in ("L", "P", "S"))}
          </div>
        </figure>
      </div>
    </div>
  </section>

  <section class="trust">
    <div class="wrap-wide">
      <div class="trust-inner">
        <div class="trust-item">{ICONS['truck']}<div><h4 data-i18n="trust.1.t">Direct from the factory</h4><p data-i18n="trust.1.d">Yiwu-based supplier.</p></div></div>
        <div class="trust-item">{ICONS['box']}<div><h4 data-i18n="trust.2.t">Container-loading data</h4><p data-i18n="trust.2.d">Carton quantity, G.W. and CBM.</p></div></div>
        <div class="trust-item">{ICONS['shield']}<div><h4 data-i18n="trust.3.t">Custom packaging</h4><p data-i18n="trust.3.d">Own-brand cards and gift boxes.</p></div></div>
        <div class="trust-item">{ICONS['chat']}<div><h4 data-i18n="trust.4.t">Reply within 24h</h4><p data-i18n="trust.4.d">Formal quotation and samples.</p></div></div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap-wide">
      <div class="sec-head">
        <div>
          <div class="eyebrow" data-i18n="collections.eyebrow">Product programmes</div>
          <h2 class="h-display h2" data-i18n="collections.title">Three collections, one supplier</h2>
          <p data-i18n="collections.sub">Each programme is item-coded, photographed and priced per piece.</p>
        </div>
        <a class="btn btn-ghost" href="collections.html" data-i18n="hero.cta1">Browse the catalogue</a>
      </div>
      <div class="coll-grid">{coll}</div>
    </div>
  </section>

  <section class="section" style="background:var(--paper-2);border-top:1px solid var(--line);border-bottom:1px solid var(--line)">
    <div class="wrap-wide">
      <div class="sec-head">
        <div>
          <div class="eyebrow" data-i18n="catalog.eyebrow">Catalogue</div>
          <h2 class="h-display h2" data-i18n="product.related">Selected items</h2>
          <p data-i18n="product.relatedSub">Popular lines from the three programmes.</p>
        </div>
        <a class="btn btn-ghost" href="collections.html"><span data-i18n="nav.catalog">Products</span> →</a>
      </div>
      <div class="prod-grid">{''.join(card(p) for p in featured)}</div>
    </div>
  </section>

  <section class="section">
    <div class="wrap-wide" style="display:grid;grid-template-columns:1.1fr .9fr;gap:52px;align-items:center">
      <div>
        <div class="eyebrow" data-i18n="about.eyebrow">About us</div>
        <h2 class="h-display h2" data-i18n="about.title">A kitchenware partner, not just a price list</h2>
        <p class="lead" style="margin-top:16px" data-i18n="about.p1">SKit Kitchenware is the export arm of a Yiwu-based kitchen tool supplier.</p>
        <p style="color:var(--ink-soft)" data-i18n="about.p2">We produce and source complete kitchen tool programmes.</p>
        <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:22px">
          <a class="btn btn-primary" href="about.html" data-i18n="nav.about">About us</a>
          <a class="btn btn-ghost" href="downloads.html" data-i18n="downloads.title">Price lists &amp; catalogues</a>
        </div>
      </div>
      <div style="display:grid;gap:14px">
        {''.join(f'''<div class="contact-card" style="display:flex;gap:14px;align-items:flex-start">
          <span class="ico" style="margin:0">{ICONS[ic]}</span>
          <div><h4 data-i18n="{tk}">T</h4><p data-i18n="{dk}">D</p></div></div>''' for ic, tk, dk in (
            ('box', 'about.v1.t', 'about.v1.d'),
            ('shield', 'about.v2.t', 'about.v2.d'),
            ('globe', 'about.v3.t', 'about.v3.d'),
            ('truck', 'about.v4.t', 'about.v4.d')))}
      </div>
    </div>
  </section>

  <section class="section" style="background:var(--paper-2);border-top:1px solid var(--line)">
    <div class="wrap-wide">
      <div class="sec-head">
        <div>
          <div class="eyebrow" data-i18n="about.eyebrow">About us</div>
          <h2 class="h-display h2" data-i18n="gallery.title">Shot in our studio</h2>
          <p data-i18n="gallery.sub">Every programme is photographed before it ships, so you know exactly what arrives in the carton.</p>
        </div>
        <a class="btn btn-ghost" href="collections.html"><span data-i18n="nav.catalog">Products</span> →</a>
      </div>
      <div class="shot-grid">
        <figure class="shot shot-wide">
          {cover_picture('p01', '', 'Wood-grain handle kitchen tool set', cls='', sizes='(max-width: 620px) 46vw, (max-width: 1080px) 30vw, 46vw', width=1920, height=960)}
          <figcaption data-i18n="gallery.c1">Wood-grain handle programme</figcaption>
        </figure>
        <figure class="shot">
          {cover_picture('p03', '', 'Coloured silicone spatulas and brushes', sizes='(max-width: 1080px) 30vw, 23vw')}
          <figcaption data-i18n="gallery.c2">Silicone colour range</figcaption>
        </figure>
        <figure class="shot">
          {cover_picture('p08', '', 'Stainless steel kitchen tool set', sizes='(max-width: 1080px) 30vw, 23vw')}
          <figcaption data-i18n="gallery.c3">Stainless steel programme</figcaption>
        </figure>
        <figure class="shot">
          {cover_picture('p09', '', 'Pizza cutters and pastry tools', sizes='(max-width: 1080px) 30vw, 23vw')}
          <figcaption data-i18n="gallery.c4">Pizza &amp; pastry tools</figcaption>
        </figure>
        <figure class="shot">
          {cover_picture('p10', '', 'Stainless steel turners and spatulas', sizes='(max-width: 1080px) 30vw, 23vw')}
          <figcaption data-i18n="gallery.c5">Turners &amp; spatulas</figcaption>
        </figure>
        <figure class="shot">
          {cover_picture('p11', '', 'Stainless steel peelers and zesters', sizes='(max-width: 1080px) 30vw, 23vw')}
          <figcaption data-i18n="gallery.c6">Peelers &amp; zesters</figcaption>
        </figure>
      </div>
    </div>
  </section>

  <section class="photo-band">
    {cover_picture('p04', '', 'SKit wooden-handle kitchen tools on a marble worktop', cls='photo-band-bg', sizes='100vw', width=1920, height=1080)}
    <div class="wrap-wide">
      <div class="photo-inner">
        <div class="eyebrow" data-i18n="band.eyebrow">OEM &amp; private label</div>
        <h2 class="h-display h2" data-i18n="band.title">Your brand, our factory floor</h2>
        <p style="margin:16px 0 26px;font-size:16.5px" data-i18n="band.sub">Own-brand hang cards, colour boxes, gift sets and barcodes — produced to your artwork and market regulations, from one carton per item.</p>
        <div style="display:flex;gap:12px;flex-wrap:wrap">
          <a class="btn btn-accent btn-lg" href="contact.html" data-i18n="nav.quote">Request a quotation</a>
          <a class="btn btn-lg" style="background:rgba(255,255,255,.14);color:#fff" href="collections.html" data-i18n="hero.cta1">Browse the catalogue</a>
        </div>
      </div>
    </div>
  </section>

  <section class="section" style="background:var(--ink);color:#fff">
    <div class="wrap" style="text-align:center;max-width:760px">
      <h2 class="h-display h2" style="color:#fff" data-i18n="contact.title">Let's build your next order</h2>
      <p style="color:#9fb0c2;margin:16px 0 26px;font-size:17px" data-i18n="contact.sub">Send us your item list, target market and packing requirements.</p>
      <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
        <a class="btn btn-accent btn-lg" href="contact.html" data-i18n="nav.quote">Request a quotation</a>
        <a class="btn btn-lg" style="background:rgba(255,255,255,.12);color:#fff" href="https://wa.me/{WHATSAPP}" target="_blank" rel="noopener">{ICONS['whatsapp']}<span>WhatsApp</span></a>
      </div>
    </div>
  </section>
</main>
{drawer_and_fab(rel)}
{footer(rel)}"""

    desc = ("SKit Kitchenware — manufacturer and exporter of kitchen tools: L-handle wooden "
            "cutlery, P-handle stainless steel utensils and silicone &amp; nylon kitchenware. "
            "Browse 440+ item lines with FOB prices, carton data and MOQ.")
    jsonld = {
        "@context": "https://schema.org", "@type": "Organization",
        "name": "SKit Kitchenware", "url": "https://terrorschiki.github.io/SKit.github.io/",
        "description": "Kitchen tool manufacturer and exporter: wooden-handle cutlery, stainless steel utensils, silicone and nylon kitchenware.",
        "address": {"@type": "PostalAddress", "addressLocality": "Yiwu", "addressRegion": "Zhejiang", "addressCountry": "CN"},
        "contactPoint": [{"@type": "ContactPoint", "telephone": "+86" + PHONE1, "contactType": "sales",
                          "availableLanguage": ["en", "zh", "es", "fr"]}],
    }
    write("index.html", head("SKit Kitchenware — Wholesale Kitchen Tools Price List &amp; Catalogue",
                            desc, rel, canonical("index.html"),
                            jsonld=json.dumps(jsonld, ensure_ascii=False),
                            keywords="kitchen tools wholesale, kitchenware exporter, wooden handle cutlery, stainless steel utensils, silicone kitchen utensils, FOB price list") + body)


# ------------------------------------------------------------- COLLECTIONS
def build_collections_overview():
    rel = ""
    cards = ""
    for k in ("L", "P", "S"):
        m, n, lo = SET_META[k], SETS[k]["count"], lowest_price(k)
        cards += f"""<article class="coll-card">
  <div class="coll-media">
    <img src="{SETS[k]['hero']}.jpg" alt="{html.escape(SETS[k]['title'])}" loading="lazy" width="1400" height="700">
    <span class="coll-tag">{m['tag']}</span>
  </div>
  <div class="coll-body">
    <h3 data-i18n="{m['title_i18n']}">Collection {k}</h3>
    <div class="sub" data-i18n="{m['brand_i18n']}">Handle</div>
    <p style="font-size:13.6px;color:var(--ink-soft);margin:0 0 16px" data-i18n="{m['desc_i18n']}">Description</p>
    <div class="coll-meta"><span class="pill">{n} <span data-i18n="collections.items">items</span></span>
      <span class="pill accent"><span data-i18n="collections.from">From</span> ${lo:.2f}</span></div>
    <div class="coll-foot">
      <a class="btn btn-primary btn-sm" href="collections/{m['slug']}.html" data-i18n="collections.browse">View catalogue</a>
      <a class="btn btn-quiet btn-sm" href="downloads.html" data-i18n="nav.downloads">Downloads</a>
    </div>
  </div>
</article>"""

    body = f"""{header('catalog', rel)}
<main id="main">
  <section class="page-head">
    <div class="wrap-wide">
      <nav class="breadcrumb" aria-label="Breadcrumb"><a href="index.html" data-i18n="nav.home">Home</a><span class="sep">/</span><span data-i18n="nav.catalog">Products</span></nav>
      <div class="page-head-row">
        <div>
          <h1 class="h-display h1" data-i18n="collections.title">Three collections, one supplier</h1>
          <p class="sub" data-i18n="collections.sub">Each programme is item-coded, photographed and priced per piece.</p>
        </div>
        <div class="head-pills">
          <span class="badge">{ICONS['check']}{len(PRODUCTS)} <span data-i18n="hero.products">item lines</span></span>
          <span class="badge">{ICONS['check']}<span data-i18n="hero.badge1">Factory direct pricing</span></span>
        </div>
      </div>
    </div>
  </section>
  <section class="section">
    <div class="wrap-wide"><div class="coll-grid">{cards}</div></div>
  </section>
  <section class="photo-band">
    {cover_picture('p12', '', 'SKit stainless steel whisks, strainers and kitchen tools', cls='photo-band-bg', sizes='100vw', width=1920, height=1080)}
    <div class="wrap-wide">
      <div class="photo-inner">
        <div class="eyebrow" data-i18n="catalog.eyebrow">Catalogue</div>
        <h2 class="h-display h2" data-i18n="overview.bandTitle">Not sure where to start?</h2>
        <p style="margin:16px 0 26px;font-size:16.5px" data-i18n="overview.bandSub">Send us your market, target retail price and packing idea — we will shortlist the items that fit and return a costed offer with carton data.</p>
        <div style="display:flex;gap:12px;flex-wrap:wrap">
          <a class="btn btn-accent btn-lg" href="contact.html" data-i18n="nav.quote">Request a quotation</a>
          <a class="btn btn-lg" style="background:rgba(255,255,255,.14);color:#fff" href="downloads.html" data-i18n="downloads.title">Price lists &amp; catalogues</a>
        </div>
      </div>
    </div>
  </section>
</main>
{drawer_and_fab(rel)}
{footer(rel)}"""
    desc = ("Browse all three SKit kitchen tool programmes: L-handle wooden cutlery, "
            "P-handle stainless steel utensils and silicone &amp; nylon kitchenware with live prices.")
    write("collections.html", head("Product Collections — SKit Kitchenware Wholesale Catalogue",
                                   desc, rel, canonical("collections.html")) + body)


def build_collection(k):
    rel = "../"
    m, s = SET_META[k], SETS[k]
    n = s["count"]
    # most common material combinations, shown in English for international buyers
    from collections import Counter
    mat_counts = Counter((p.get("material_en") or p["material"])
                         for p in PRODUCTS if p["set"] == k and (p.get("material_en") or p["material"]))
    mat_line = " · ".join(x for x, _ in mat_counts.most_common(3))
    body = f"""{header('catalog', rel)}
<main id="main">
  <section class="page-head has-photo">
    {cover_picture(COVER_BY_SET[k], rel, s['title'] + ' — SKit kitchen tools', cls='photo-band-bg',
                   sizes='100vw', eager=True, width=1920, height=1080)}
    <div class="wrap-wide">
      <nav class="breadcrumb" aria-label="Breadcrumb">
        <a href="{rel}index.html" data-i18n="nav.home">Home</a><span class="sep">/</span>
        <a href="{rel}collections.html" data-i18n="nav.catalog">Products</a><span class="sep">/</span>
        <span data-i18n="{m['title_i18n']}">{html.escape(s['title'])}</span>
      </nav>
      <div class="page-head-row">
        <div>
          <h1 class="h-display h1" data-i18n="{m['title_i18n']}">{html.escape(s['title'])}</h1>
          <p class="sub" data-i18n="{m['desc_i18n']}">Description</p>
          <div class="head-pills">
            <span class="badge">{ICONS['check']}<b>{n}</b>&nbsp;<span data-i18n="collections.items">items</span></span>
            <span class="badge">{ICONS['box']}<span>{html.escape(mat_line)}</span></span>
            <span class="badge">{ICONS['truck']}<span data-i18n="hero.badge3">Worldwide shipping</span></span>
          </div>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap">
          <a class="btn btn-primary" href="{rel}contact.html" data-i18n="nav.quote">Request a quotation</a>
          <a class="btn btn-ghost" href="{rel}downloads.html">{ICONS['download']}<span data-i18n="nav.downloads">Downloads</span></a>
        </div>
      </div>
    </div>
  </section>

  <div class="toolbar">
    <div class="wrap-wide toolbar-inner">
      <div class="search-wrap">
        {ICONS['search']}
        <input type="search" id="searchInput" data-i18n-placeholder="catalog.searchShort" placeholder="Search item code or name…" aria-label="Search">
        <button class="search-clear" type="button" aria-label="Clear">✕</button>
      </div>
      <div class="select-wrap"><select class="sel" id="catFilter" aria-label="Category"></select></div>
      <div class="select-wrap"><select class="sel" id="matFilter" aria-label="Material"></select></div>
      <div class="select-wrap">
        <select class="sel" id="sortSelect" data-sort aria-label="Sort">
          <option value="code" data-i18n="catalog.sortCode">Sort: item number</option>
          <option value="price-asc" data-i18n="catalog.sortPriceAsc">Price: low to high</option>
          <option value="price-desc" data-i18n="catalog.sortPriceDesc">Price: high to low</option>
          <option value="name" data-i18n="catalog.sortName">Sort: name A–Z</option>
        </select>
      </div>
      <div class="toolbar-right">
        <span class="result-count" id="resultCount"></span>
        <div class="view-toggle">
          <button type="button" data-layout="grid" aria-pressed="true" aria-label="Grid view" data-i18n-aria="catalog.gridView">{ICONS['grid']}</button>
          <button type="button" data-layout="list" aria-pressed="false" aria-label="List view" data-i18n-aria="catalog.listView">{ICONS['rows']}</button>
        </div>
      </div>
    </div>
    <div class="wrap-wide"><div class="chips" id="catChips"></div></div>
  </div>

  <section class="catalog-body" id="catalog" data-set="{k}">
    <div class="wrap-wide">
      <div class="prod-grid" id="prodGrid"></div>
      <div class="pager" id="pager"></div>
    </div>
  </section>
</main>
{drawer_and_fab(rel)}
{footer(rel)}"""
    desc = m["meta_desc"]
    jsonld = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": m["page_title"].replace("&amp;", "&"),
        "description": re.sub(r"<[^>]+>", "", desc),
        "isPartOf": {"@type": "WebSite", "name": "SKit Kitchenware"},
        "mainEntity": {
            "@type": "ItemList", "numberOfItems": n,
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": p["name_en"] or p["name_zh"],
                 "url": f"https://terrorschiki.github.io/SKit.github.io/products/{p['id']}.html"}
                for i, p in enumerate([x for x in PRODUCTS if x["set"] == k][:60])
            ],
        },
    }
    path = f"collections/{m['slug']}.html"
    write(path, head(m["page_title"] + " | SKit Kitchenware", desc, rel, canonical(path),
                     jsonld=json.dumps(jsonld, ensure_ascii=False),
                     scripts=("catalog.js",)) + body)


# ------------------------------------------------------------------ PRODUCT
def build_product(p):
    rel = "../"
    k = p["set"]
    m = SET_META[k]
    name = p["name_en"] or p["name_zh"]
    alt_name = p["name_zh"] if p["name_en"] else ""
    specs = [
        ("spec.itemNo", p["code"]),
        ("spec.material", p.get("material_en") or p["material"]),
        ("spec.size", p["size"]),
        ("spec.packing", p["packing"]),
        ("spec.qty", p["qty"]),
        ("spec.gw", p["gw"]),
        ("spec.cbm", str(p["cbm"])),
        ("spec.colour", p["colour"]),
        ("spec.note", p["note"]),
    ]
    spec_rows = "".join(
        f'<tr><th data-i18n="{key}">{SPEC_LABELS.get(key, "")}</th>'
        f'<td>{html.escape(str(val))}</td></tr>'
        for key, val in specs if str(val).strip()
    )
    payload = html.escape(json.dumps({
        "id": p["id"], "code": p["code"], "name_zh": p["name_zh"], "name_en": p["name_en"],
        "price": p["price"], "qty": p["qty"], "size": p["size"], "set": p["set"]},
        ensure_ascii=False), quote=True)

    price_disp = f'${p["price"]}' if p["price"] != "" else "—"
    body = f"""{header('catalog', rel, f'data-product="{p["id"]}" data-set="{k}"')}
<main id="main">
  <div class="wrap-wide" style="padding-top:22px">
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <a href="{rel}index.html" data-i18n="nav.home">Home</a><span class="sep">/</span>
      <a href="{rel}collections.html" data-i18n="nav.catalog">Products</a><span class="sep">/</span>
      <a href="{m['slug']}.html" data-i18n="{m['title_i18n']}">Collection</a><span class="sep">/</span>
      <span>{html.escape(p['code'])}</span>
    </nav>
  </div>
  <section class="pdp">
    <div class="wrap-wide pdp-grid">
      <div>
        <figure class="pdp-media" style="margin:0">
          <div class="pdp-media-main">
            <img src="{rel}assets/products/{p['id']}-card.jpg" alt="{html.escape(name)} — {html.escape(p['code'])} — SKit kitchen tool"
                 data-zoom="{rel}assets/products/{p['id']}-full.jpg" width="900" height="675">
          </div>
          <figcaption class="pdp-hint" data-i18n="product.zoom">Click to enlarge</figcaption>
        </figure>
      </div>
      <div>
        <div class="eyebrow" data-i18n="{m['title_i18n']}">Collection</div>
        <h1 class="h-display h1 pdp-title" style="font-size:clamp(26px,3vw,38px)" data-pdp-name>{html.escape(name)}</h1>
        <div class="pdp-code">{html.escape(p['code'])}</div>
        <div class="pdp-en" id="pdpSub">{html.escape(alt_name)}</div>
        <p class="pdp-desc" data-i18n="{m['desc_i18n']}">Description</p>

        <div class="price-box">
          <div class="big" data-price-usd="{p['price']}" data-i18n-title="hero.note">{price_disp}</div>
          <div class="unit" id="pdpUnit"><span data-i18n="product.priceNote">Unit price, per piece</span> · <span data-i18n="spec.moq">MOQ</span> {html.escape(str(p['qty']))} <span data-i18n="spec.pcs">pcs</span></div>
          <div class="terms" data-i18n="product.priceTerms">Prices are quoted excluding tax.</div>
        </div>

        <h3 class="h3" style="margin-bottom:12px" data-i18n="product.specs">Specification</h3>
        <table class="spec-table" id="specTable">{spec_rows}</table>

        <div class="pdp-actions">
          <button class="btn btn-accent btn-lg" type="button" id="pdpAdd" data-add="{payload}" disabled>
            {ICONS['cart']}<span data-i18n="product.addQuote">Add to quotation</span>
          </button>
          <a class="btn btn-ghost btn-lg" href="{rel}contact.html">{ICONS['chat']}<span data-i18n="contact.title">Contact</span></a>
          <a class="btn btn-ghost btn-lg" href="{rel}assets/products/{p['id']}-full.jpg" download>{ICONS['download']}<span data-i18n="product.download">Download photo</span></a>
        </div>
        <p class="pdp-note" data-i18n="product.priceTerms">Terms</p>

        <div class="contact-card" style="margin-top:26px">
          <div class="ico">{ICONS['phone']}</div>
          <h4 data-i18n="product.askTitle">Need samples or a custom colour?</h4>
          <p data-i18n="product.askSub">We produce OEM and private-label orders from 1 carton per item.</p>
          <p style="margin-top:10px"><a href="tel:+86{PHONE1}"><b>+86 {PHONE1}</b></a> · <a href="https://wa.me/{WHATSAPP}" target="_blank" rel="noopener">WhatsApp</a></p>
        </div>
      </div>
    </div>
  </section>

  <section class="section" style="background:var(--paper-2);border-top:1px solid var(--line)">
    <div class="wrap-wide">
      <div class="sec-head" style="margin-bottom:26px">
        <div>
          <h2 class="h-display h3" data-i18n="product.related">Related items</h2>
          <p style="margin-top:6px" data-i18n="product.relatedSub">Frequently ordered together.</p>
        </div>
        <a class="btn btn-ghost btn-sm" href="{m['slug']}.html"><span data-i18n="product.backTo">Back to collection</span> →</a>
      </div>
      <div class="rel-grid" id="relatedGrid"></div>
    </div>
  </section>

  <section class="photo-band">
    {cover_picture(COVER_BY_SET[k], rel, SETS[k]['title'] + ' — SKit kitchen tools', cls='photo-band-bg',
                   sizes='100vw', width=1920, height=1080)}
    <div class="wrap-wide">
      <div class="photo-inner">
        <div class="eyebrow" data-i18n="band.eyebrow">OEM &amp; private label</div>
        <h2 class="h-display h2" data-i18n="product.askTitle">Need samples or a custom colour?</h2>
        <p style="margin:16px 0 26px;font-size:16.5px" data-i18n="product.askSub">We produce OEM and private-label orders from 1 carton per item.</p>
        <div style="display:flex;gap:12px;flex-wrap:wrap">
          <a class="btn btn-accent btn-lg" href="{rel}contact.html" data-i18n="product.askCta">Talk to our export team</a>
          <a class="btn btn-lg" style="background:rgba(255,255,255,.14);color:#fff" href="{m['slug']}.html" data-i18n="product.backTo">Back to collection</a>
        </div>
      </div>
    </div>
  </section>
</main>
{drawer_and_fab(rel)}
{footer(rel)}"""

    title = f"{name} ({p['code']}) — Wholesale Price | SKit Kitchenware"
    desc = (f"{name} {p['code']}: {p['material']}, size {p['size']} cm, {p['qty']} pcs per carton, "
            f"G.W. {p['gw']}, {p['cbm']} CBM. Unit price USD {p['price']}. Wholesale and OEM "
            f"orders from SKit Kitchenware.").replace("  ", " ")
    jsonld = {
        "@context": "https://schema.org", "@type": "Product",
        "name": name, "sku": p["code"], "category": p["cat_label"],
        "material": p["material"], "image": f"https://terrorschiki.github.io/SKit.github.io/assets/products/{p['id']}-card.jpg",
        "description": f"{name} {alt_name} — {p['material']}, {p['size']} cm.",
        "brand": {"@type": "Brand", "name": "SKit"},
        "offers": {"@type": "Offer", "priceCurrency": "USD", "price": str(p["price"]),
                   "availability": "https://schema.org/InStock",
                   "eligibleQuantity": {"@type": "QuantitativeValue", "value": p["qty"], "unitCode": "C62"},
                   "seller": {"@type": "Organization", "name": "SKit Kitchenware"}},
    }
    path = f"products/{p['id']}.html"
    write(path, head(html.escape(title), html.escape(desc), rel, canonical(path),
                     og_img=f"https://terrorschiki.github.io/SKit.github.io/assets/products/{p['id']}-card.jpg",
                     og_type="product", jsonld=json.dumps(jsonld, ensure_ascii=False),
                     keywords=f"{name}, {p['code']}, {p['material']}, wholesale kitchen tools, kitchenware exporter",
                     scripts=("product.js",)) + body)


# -------------------------------------------------------------------- ABOUT
def build_about():
    rel = ""
    body = f"""{header('about', rel)}
<main id="main">
  <section class="page-head has-photo">
    {cover_picture('p02', '', 'SKit silicone and stainless steel kitchen tools on marble', cls='photo-band-bg',
                   sizes='100vw', eager=True, width=1920, height=1080)}
    <div class="wrap-wide">
      <nav class="breadcrumb"><a href="index.html" data-i18n="nav.home">Home</a><span class="sep">/</span><span data-i18n="nav.about">About us</span></nav>
      <h1 class="h-display h1" data-i18n="about.title">A kitchenware partner, not just a price list</h1>
      <p class="sub" data-i18n="about.p1">SKit Kitchenware is the export arm of a Yiwu-based kitchen tool supplier.</p>
    </div>
  </section>

  <section class="section">
    <div class="wrap-wide" style="display:grid;grid-template-columns:1.05fr .95fr;gap:54px;align-items:start">
      <div>
        <p class="lead" data-i18n="about.p1">SKit Kitchenware is the export arm of a Yiwu-based kitchen tool supplier.</p>
        <p style="color:var(--ink-soft)" data-i18n="about.p2">We produce and source complete kitchen tool programmes.</p>
        <h2 class="h-display h2" style="margin:34px 0 18px" data-i18n="about.values">How we work</h2>
        <div style="display:grid;gap:14px">
          {''.join(f'''<div class="contact-card" style="display:flex;gap:14px;align-items:flex-start">
            <span class="ico" style="margin:0">{ICONS[ic]}</span>
            <div><h4 data-i18n="{tk}">T</h4><p data-i18n="{dk}">D</p></div></div>''' for ic, tk, dk in (
              ('box', 'about.v1.t', 'about.v1.d'), ('shield', 'about.v2.t', 'about.v2.d'),
              ('globe', 'about.v3.t', 'about.v3.d'), ('truck', 'about.v4.t', 'about.v4.d')))}
        </div>
      </div>
      <div>
        <figure class="hero-photo" style="box-shadow:var(--shadow-md);min-height:0">
          {cover_picture('p05', '', 'SKit silicone and stainless steel utensil set', sizes='(max-width: 1080px) 92vw, 45vw', width=1920, height=1920)}
        </figure>
        <div class="hero-stats" style="margin-top:26px;border-top:0;padding-top:0">
          <div><div class="stat-n">{len(PRODUCTS)}</div><div class="stat-l" data-i18n="hero.stats.items">Quotable item lines</div></div>
          <div><div class="stat-n">3</div><div class="stat-l" data-i18n="hero.stats.sets">Product programmes</div></div>
          <div><div class="stat-n">24h</div><div class="stat-l" data-i18n="trust.4.t">Reply within 24h</div></div>
        </div>
        <div class="dl-list" style="margin-top:26px">
          <div class="dl-item"><div class="dl-ico pdf">PDF</div><div class="dl-main">
            <h4 data-i18n="downloads.title">Price lists &amp; catalogues</h4>
            <p data-i18n="downloads.sub">Download the original supplier price lists.</p></div>
            <a class="btn btn-ghost btn-sm" href="downloads.html" data-i18n="downloads.open">Open</a></div>
        </div>
        <a class="btn btn-primary btn-lg btn-block" style="margin-top:20px" href="contact.html" data-i18n="about.cta">{'See what we can produce for you'}</a>
      </div>
    </div>
  </section>

  <section class="section" style="background:var(--paper-2);border-top:1px solid var(--line)">
    <div class="wrap-wide">
      <h2 class="h-display h2" style="margin-bottom:26px" data-i18n="about.facts">At a glance</h2>
      <div class="trust-inner" style="border:1px solid var(--line);border-radius:var(--radius);overflow:hidden">
        <div class="trust-item" style="background:#fff">{ICONS['pin']}<div><h4 data-i18n="footer.address">Yiwu, Zhejiang, China</h4><p>F3-16059</p></div></div>
        <div class="trust-item" style="background:#fff">{ICONS['phone']}<div><h4 data-i18n="contact.phone">Phone / WeChat</h4><p>+86 {PHONE1} · +86 {PHONE2}</p></div></div>
        <div class="trust-item" style="background:#fff">{ICONS['globe']}<div><h4 data-i18n="contact.market">Main markets</h4><p data-i18n="contact.marketV">Europe · Americas · Africa · Middle East · South-East Asia</p></div></div>
        <div class="trust-item" style="background:#fff">{ICONS['clock']}<div><h4 data-i18n="contact.hours">Working hours</h4><p data-i18n="contact.hoursV">Monday – Saturday, 08:30 – 18:00 (GMT+8)</p></div></div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap-wide">
      <div class="sec-head">
        <div>
          <div class="eyebrow" data-i18n="about.eyebrow">About us</div>
          <h2 class="h-display h2" data-i18n="gallery.title">Shot in our studio</h2>
          <p data-i18n="gallery.sub">Every programme is photographed before it ships, so you know exactly what arrives in the carton.</p>
        </div>
      </div>
      <div class="shot-grid">
        <figure class="shot">
          {cover_picture('p04', '', 'SKit wood-handle kitchen tool set', sizes='(max-width: 1080px) 30vw, 23vw')}
          <figcaption data-i18n="gallery.c1">Wood-grain handle programme</figcaption>
        </figure>
        <figure class="shot">
          {cover_picture('p06', '', 'SKit wood-handle silicone utensils', sizes='(max-width: 1080px) 30vw, 23vw')}
          <figcaption data-i18n="gallery.c7">Wood handle &amp; silicone</figcaption>
        </figure>
        <figure class="shot">
          {cover_picture('p03', '', 'Coloured silicone spatulas and brushes', sizes='(max-width: 1080px) 30vw, 23vw')}
          <figcaption data-i18n="gallery.c2">Silicone colour range</figcaption>
        </figure>
        <figure class="shot">
          {cover_picture('p07', '', 'Stainless steel box graters', sizes='(max-width: 1080px) 30vw, 23vw')}
          <figcaption data-i18n="gallery.c8">Graters &amp; slicers</figcaption>
        </figure>
        <figure class="shot">
          {cover_picture('p12', '', 'Stainless steel whisks and strainers', sizes='(max-width: 1080px) 30vw, 23vw')}
          <figcaption data-i18n="gallery.c9">Whisks &amp; strainers</figcaption>
        </figure>
        <figure class="shot">
          {cover_picture('p10', '', 'Stainless steel turners and spatulas', sizes='(max-width: 1080px) 30vw, 23vw')}
          <figcaption data-i18n="gallery.c5">Turners &amp; spatulas</figcaption>
        </figure>
        <figure class="shot">
          {cover_picture('p11', '', 'Stainless steel peelers and zesters', sizes='(max-width: 1080px) 30vw, 23vw')}
          <figcaption data-i18n="gallery.c6">Peelers &amp; zesters</figcaption>
        </figure>
        <figure class="shot">
          {cover_picture('p09', '', 'Pizza cutters and pastry tools', sizes='(max-width: 1080px) 30vw, 23vw')}
          <figcaption data-i18n="gallery.c4">Pizza &amp; pastry tools</figcaption>
        </figure>
      </div>
    </div>
  </section>

  <section class="photo-band">
    {cover_picture('p08', '', 'SKit stainless steel kitchen tool programme', cls='photo-band-bg', sizes='100vw', width=1920, height=1080)}
    <div class="wrap-wide">
      <div class="photo-inner">
        <div class="eyebrow" data-i18n="band.eyebrow">OEM &amp; private label</div>
        <h2 class="h-display h2" data-i18n="about.cta">See what we can produce for you</h2>
        <p style="margin:16px 0 26px;font-size:16.5px" data-i18n="about.p2">We produce and source complete kitchen tool programmes.</p>
        <div style="display:flex;gap:12px;flex-wrap:wrap">
          <a class="btn btn-accent btn-lg" href="contact.html" data-i18n="nav.quote">Request a quotation</a>
          <a class="btn btn-lg" style="background:rgba(255,255,255,.14);color:#fff" href="collections.html" data-i18n="hero.cta1">Browse the catalogue</a>
        </div>
      </div>
    </div>
  </section>
</main>
{drawer_and_fab(rel)}
{footer(rel)}"""
    desc = ("SKit Kitchenware — Yiwu-based manufacturer and exporter of kitchen tools. Wooden-handle "
            "cutlery, stainless steel utensils and silicone &amp; nylon kitchenware for importers, "
            "wholesalers and supermarket programmes worldwide.")
    write("about.html", head("About us — SKit Kitchenware Manufacturer &amp; Exporter",
                             desc, rel, canonical("about.html")) + body)


# ------------------------------------------------------------------ CONTACT
def build_contact():
    rel = ""
    body = f"""{header('contact', rel)}
<main id="main">
  <section class="page-head">
    <div class="wrap-wide">
      <nav class="breadcrumb"><a href="index.html" data-i18n="nav.home">Home</a><span class="sep">/</span><span data-i18n="nav.contact">Contact</span></nav>
      <h1 class="h-display h1" data-i18n="contact.title">Let's build your next order</h1>
      <p class="sub" data-i18n="contact.sub">Send us your item list, target market and packing requirements.</p>
    </div>
  </section>

  <section class="section">
    <div class="wrap-wide" style="display:grid;grid-template-columns:1.15fr .85fr;gap:52px;align-items:start">
      <div id="quote">
        <h2 class="h-display h3" style="margin-bottom:8px" data-i18n="nav.quote">Request a quotation</h2>
        <p style="color:var(--ink-soft);font-size:14px;margin-bottom:22px" data-i18n="contact.formNote">This form opens your email client with the message ready to send.</p>
        <form id="contactForm" novalidate>
          <div class="form-grid">
            <div class="field"><label for="cf-name" data-i18n="contact.name">Your name</label><input id="cf-name" name="name" required autocomplete="name"></div>
            <div class="field"><label for="cf-company" data-i18n="contact.company">Company</label><input id="cf-company" name="company" autocomplete="organization"></div>
            <div class="field"><label for="cf-email" data-i18n="contact.email">Email</label><input id="cf-email" name="email" type="email" required autocomplete="email"></div>
            <div class="field"><label for="cf-country" data-i18n="contact.country">Country / market</label><input id="cf-country" name="country" autocomplete="country-name"></div>
            <div class="field full"><label for="cf-message" data-i18n="contact.message">Your message or item list</label>
              <textarea id="cf-message" name="message" data-i18n-placeholder="contact.messagePh" placeholder="e.g. 2,000 pcs of L05, L07 and L12 with our own hang card, FOB Ningbo…"></textarea></div>
          </div>
          <div style="display:flex;gap:11px;flex-wrap:wrap;margin-top:20px">
            <button class="btn btn-accent btn-lg" type="submit">{ICONS['mail']}<span data-i18n="contact.send">Send via email</span></button>
            <button class="btn btn-ghost btn-lg" type="button" id="waBtn">{ICONS['whatsapp']}<span data-i18n="contact.sendWa">Send via WhatsApp</span></button>
            <button class="btn btn-ghost btn-lg" type="button" data-open-quote>{ICONS['cart']}<span data-i18n="quote.view">Review quotation</span></button>
          </div>
          <p style="font-size:12.5px;color:var(--muted);margin-top:14px" data-i18n="contact.quoteHint">Your item list from the quotation builder is inserted automatically.</p>
        </form>
      </div>

      <div>
        <h2 class="h-display h3" style="margin-bottom:18px" data-i18n="contact.direct">Direct contact</h2>
        <div class="contact-cards" style="grid-template-columns:1fr">
          <div class="contact-card">
            <div class="ico">{ICONS['phone']}</div>
            <h4 data-i18n="contact.phone">Phone / WeChat</h4>
            <p><a href="tel:+86{PHONE1}">+86 {PHONE1}</a><br><a href="tel:+86{PHONE2}">+86 {PHONE2}</a></p>
          </div>
          <div class="contact-card">
            <div class="ico">{ICONS['mail']}</div>
            <h4 data-i18n="contact.email">Email</h4>
            <p><a href="mailto:{EMAIL}">{EMAIL}</a></p>
          </div>
          <div class="contact-card">
            <div class="ico">{ICONS['clock']}</div>
            <h4 data-i18n="contact.hours">Working hours</h4>
            <p data-i18n="contact.hoursV">Monday – Saturday, 08:30 – 18:00 (GMT+8)</p>
            <p style="margin-top:6px;color:var(--muted);font-size:13px" data-i18n="contact.fax">Tel / Fax</p>
            <p>{FAX}</p>
          </div>
          <div class="contact-card">
            <div class="ico">{ICONS['globe']}</div>
            <h4 data-i18n="contact.market">Main markets</h4>
            <p data-i18n="contact.marketV">Europe · Americas · Africa · Middle East · South-East Asia</p>
          </div>
        </div>
        <a class="btn btn-accent btn-lg btn-block" style="margin-top:18px" href="https://wa.me/{WHATSAPP}" target="_blank" rel="noopener">{ICONS['whatsapp']}<span>WhatsApp +86 {PHONE1}</span></a>
      </div>
    </div>
  </section>
</main>
{drawer_and_fab(rel)}
{footer(rel)}
<script>
(function () {{
  var form = document.getElementById('contactForm');
  function compose() {{
    var q = (window.SKIT && SKIT.quote || []);
    var lines = [];
    q.forEach(function (i, n) {{
      lines.push((n + 1) + '. ' + (i.code ? i.code + ' — ' : '') + (i.en || i.zh) + '  × ' + i.qty);
    }});
    var body = document.getElementById('cf-message').value || '';
    if (lines.length) {{
      body += (body ? '\\n\\n' : '') + '--- Item list ---\\n' + lines.join('\\n');
    }}
    return body;
  }}
  form.addEventListener('submit', function (e) {{
    e.preventDefault();
    var name = document.getElementById('cf-name').value;
    var company = document.getElementById('cf-company').value;
    var country = document.getElementById('cf-country').value;
    var subject = 'Quotation request' + (company ? ' — ' + company : '') + (country ? ' (' + country + ')' : '');
    var body = 'Name: ' + name + '\\nCompany: ' + company + '\\nCountry: ' + country +
               '\\nEmail: ' + document.getElementById('cf-email').value + '\\n\\n' + compose();
    window.location.href = 'mailto:{EMAIL}?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
  }});
  document.getElementById('waBtn').addEventListener('click', function () {{
    var body = compose() || 'Hello SKit, I would like a quotation.';
    window.open('https://wa.me/{WHATSAPP}?text=' + encodeURIComponent(body), '_blank');
  }});
}})();
</script>"""
    desc = ("Contact SKit Kitchenware for wholesale kitchen tool quotations. Phone +86 "
            f"{PHONE1}, WhatsApp, email {EMAIL}. Reply within one working day.")
    write("contact.html", head("Contact &amp; Quotation Request — SKit Kitchenware",
                               desc, rel, canonical("contact.html")) + body)


# ---------------------------------------------------------------- DOWNLOADS
def human(n):
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0


def build_downloads():
    rel = ""
    rows = ""
    for k in ("L", "P", "S"):
        m, s = SET_META[k], SETS[k]
        base = os.path.splitext(os.path.basename(s["file"]))[0]
        pdf_name = s["pdf"]
        xls_name = s["file"]
        pdf_path = os.path.join(SITE, "downloads", pdf_name)
        xls_path = os.path.join(SITE, "downloads", xls_name)
        pdf_size = human(os.path.getsize(pdf_path)) if os.path.exists(pdf_path) else "—"
        xls_size = human(os.path.getsize(xls_path)) if os.path.exists(xls_path) else "—"
        rows += f"""<div class="dl-item" style="align-items:flex-start;flex-wrap:wrap">
  <div class="dl-ico" style="background:var(--paper-3);color:var(--ink)">{k}</div>
  <div class="dl-main" style="min-width:230px">
    <h4 data-i18n="{m['title_i18n']}">{html.escape(s['title'])}</h4>
    <p><span data-i18n="{m['brand_i18n']}">Handle</span> · {s['count']} <span data-i18n="collections.items">items</span></p>
  </div>
  <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">
    <a class="btn btn-ghost btn-sm" href="downloads/{pdf_name}" download>
      <span class="dl-ico pdf" style="width:34px;height:34px;border-radius:8px;font-size:10px">PDF</span>
      <span data-i18n="downloads.pdf">PDF price list</span>
      <span style="color:var(--muted);font-weight:500">{pdf_size}</span>
    </a>
    <a class="btn btn-ghost btn-sm" href="downloads/{xls_name}" download>
      <span class="dl-ico xls" style="width:34px;height:34px;border-radius:8px;font-size:10px">XLS</span>
      <span data-i18n="downloads.xlsx">Excel price list</span>
      <span style="color:var(--muted);font-weight:500">{xls_size}</span>
    </a>
    <a class="btn btn-primary btn-sm" href="collections/{m['slug']}.html" data-i18n="collections.browse">View catalogue</a>
  </div>
</div>"""

    body = f"""{header('downloads', rel)}
<main id="main">
  <section class="page-head">
    <div class="wrap-wide">
      <nav class="breadcrumb"><a href="index.html" data-i18n="nav.home">Home</a><span class="sep">/</span><span data-i18n="nav.downloads">Downloads</span></nav>
      <h1 class="h-display h1" data-i18n="downloads.title">Price lists &amp; catalogues</h1>
      <p class="sub" data-i18n="downloads.sub">Download the original supplier price lists for offline review, costing or forwarding.</p>
    </div>
  </section>
  <section class="section">
    <div class="wrap-wide">
      <div class="dl-list">{rows}</div>
      <p style="font-size:13px;color:var(--muted);margin-top:20px" data-i18n="downloads.note">The Excel files include the full product photography embedded in each line.</p>
    </div>
  </section>
</main>
{drawer_and_fab(rel)}
{footer(rel)}"""
    desc = ("Download the SKit Kitchenware price lists: L-handle, P-handle and silicone &amp; nylon "
            "kitchen tools in PDF and Excel format with full carton and packing data.")
    write("downloads.html", head("Price Lists &amp; Catalogues (PDF / Excel) — SKit Kitchenware",
                                 desc, rel, canonical("downloads.html")) + body)


# ------------------------------------------------------- 404 / sitemap / misc
def build_misc():
    rel = "/"
    body = f"""{header('', rel)}
<main id="main">
  <section class="section" style="text-align:center;padding:110px 0">
    <div class="wrap" style="max-width:560px">
      <div class="eyebrow">404</div>
      <h1 class="h-display h1">This page has moved on</h1>
      <p class="lead" style="margin:14px auto 26px">The page you were looking for is not here. Browse the catalogue instead — 440+ kitchen tool lines with live prices.</p>
      <div style="display:flex;gap:11px;justify-content:center;flex-wrap:wrap">
        <a class="btn btn-accent btn-lg" href="{rel}collections.html" data-i18n="hero.cta1">Browse the catalogue</a>
        <a class="btn btn-ghost btn-lg" href="{rel}index.html" data-i18n="nav.home">Home</a>
      </div>
    </div>
  </section>
</main>
{drawer_and_fab(rel)}
{footer(rel)}"""
    write("404.html", head("Page not found — SKit Kitchenware", "Page not found.", rel,
                           "https://terrorschiki.github.io/SKit.github.io/404.html") + body)

    urls = ["", "collections.html", "about.html", "contact.html", "downloads.html"]
    urls += [f"collections/{SET_META[k]['slug']}.html" for k in ("L", "P", "S")]
    urls += [f"products/{p['id']}.html" for p in PRODUCTS]
    base = "https://terrorschiki.github.io/SKit.github.io/"
    today = datetime.date.today().isoformat()
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        pr = "1.0" if u == "" else ("0.9" if u in ("collections.html", "contact.html") else "0.7")
        xml.append(f"  <url><loc>{base}{u}</loc><lastmod>{today}</lastmod>"
                   f"<changefreq>weekly</changefreq><priority>{pr}</priority></url>")
    xml.append("</urlset>")
    write("sitemap.xml", "\n".join(xml))
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {base}sitemap.xml\n")
    write(".nojekyll", "")


# ------------------------------------------------------------------ favicon
def build_favicon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="15" fill="#0e1c2b"/>
  <path d="M20 22h24M20 32h16M20 42h10" stroke="#b4552a" stroke-width="5" stroke-linecap="round"/>
</svg>"""
    os.makedirs(os.path.join(SITE, "assets", "img"), exist_ok=True)
    with io.open(os.path.join(SITE, "assets", "img", "favicon.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg)


def build_og_cover():
    """Simple branded OG cover built from a hero photo + ink band."""
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return
    src = os.path.join(SITE, SETS["S"]["hero"] + ".jpg")
    out = os.path.join(SITE, "assets", "img", "og-cover.jpg")
    if not os.path.exists(src):
        return
    W, H = 1200, 630
    im = Image.open(src).convert("RGB")
    im.thumbnail((W, H), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), "#f8f9fb")
    canvas.paste(im, ((W - im.size[0]) // 2, (H - im.size[1]) // 2))
    d = ImageDraw.Draw(canvas, "RGBA")
    d.rectangle([0, 0, W, 96], fill=(14, 28, 43, 255))
    d.rectangle([0, H - 56, W, H], fill=(14, 28, 43, 255))
    try:
        canvas.save(out, "JPEG", quality=86, optimize=True)
    except Exception:
        pass


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    os.makedirs(os.path.join(SITE, "downloads"), exist_ok=True)
    # copy source price lists for the download page
    import shutil
    for k in ("L", "P", "S"):
        for f in (SETS[k]["file"], SETS[k]["pdf"]):
            src = os.path.join(ROOT, f)
            dst = os.path.join(SITE, "downloads", f)
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)
                print("copied", f)

    build_home()
    build_collections_overview()
    for k in ("L", "P", "S"):
        build_collection(k)
    build_about()
    build_contact()
    build_downloads()
    build_misc()
    build_favicon()
    build_og_cover()

    n = 0
    for p in PRODUCTS:
        build_product(p)
        n += 1
        if n % 100 == 0:
            print(f"  product pages {n}/{len(PRODUCTS)}")
    print(f"generated: home, collections x3, about, contact, downloads, 404, sitemap, robots + {n} product pages")
