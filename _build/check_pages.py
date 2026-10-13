# -*- coding: utf-8 -*-
"""Poll the GitHub Pages build until it reports 'built', then probe the live URLs."""
import json, subprocess, sys, time, urllib.error, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
REPO = "Terrorschiki/SKit.github.io"
SITE = "https://terrorschiki.github.io/SKit.github.io"


def token():
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True)
    return dict(l.split("=", 1) for l in p.stdout.splitlines() if "=" in l)["password"]


TOKEN = token()


def api(path):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Authorization": "Bearer " + TOKEN, "User-Agent": "dsh",
                 "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        return e.code, None


def probe(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, len(r.read())
    except urllib.error.HTTPError as e:
        return e.code, 0
    except Exception as e:
        return str(e), 0


print("polling GitHub Pages build ...")
built = False
for i in range(1, 21):
    s, pg = api(f"/repos/{REPO}/pages")
    st = (pg or {}).get("status")
    s2, builds = api(f"/repos/{REPO}/pages/builds?per_page=1")
    b = builds[0] if isinstance(builds, list) and builds else {}
    err = (b.get("error") or {}).get("message")
    print(f"  [{i:2d}] pages={s} status={st!r} build={b.get('status')!r} dur={b.get('duration')} err={err}")
    if st == "built" or b.get("status") == "built":
        built = True
        break
    time.sleep(12)

print(f"\nbuild reported built: {built}")
print("probing live site ...")
for path in ("/", "/collections.html", "/collections/silicone-nylon-kitchenware.html",
             "/products/l-l01.html", "/data/catalog.json", "/assets/css/style.css",
             "/sitemap.xml", "/robots.txt"):
    code, size = probe(SITE + path)
    print(f"  {path:<48} {code}  {size} bytes")
