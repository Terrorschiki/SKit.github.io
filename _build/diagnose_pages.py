# -*- coding: utf-8 -*-
"""Explain why the published Pages URL returns 404 for site paths."""
import json, subprocess, sys, urllib.error, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
REPO = "Terrorschiki/SKit.github.io"

p = subprocess.run(["git", "credential", "fill"],
                   input="protocol=https\nhost=github.com\n\n",
                   capture_output=True, text=True)
TOKEN = dict(l.split("=", 1) for l in p.stdout.splitlines() if "=" in l)["password"]


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


def head(url):
    req = urllib.request.Request(url, method="GET",
                                 headers={"User-Agent": "Mozilla/5.0",
                                          "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, len(r.read()), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, 0, dict(e.headers)
    except Exception as e:
        return str(e), 0, {}


s, pg = api(f"/repos/{REPO}/pages")
if isinstance(pg, dict):
    keys = ("html_url", "status", "cname", "build_type", "source", "https_enforced")
    print("pages config:", json.dumps({k: pg.get(k) for k in keys}, ensure_ascii=False, indent=2))
else:
    print("pages config: unavailable", s)

s, builds = api(f"/repos/{REPO}/pages/builds?per_page=5")
print("\nrecent builds:")
for b in (builds or []):
    print(f"  {b.get('status'):<10} {b.get('created_at')}  dur={b.get('duration')}  "
          f"commit={str(b.get('commit'))[:9]}  err={(b.get('error') or {}).get('message')}")

s, repo = api(f"/repos/{REPO}")
print("\nrepo:", {k: repo.get(k) for k in ("full_name", "private", "visibility",
                                           "default_branch", "has_pages", "size")})

print("\nlive probes (cache-busted):")
for url in (
    "https://terrorschiki.github.io/",
    "https://terrorschiki.github.io/SKit.github.io/",
    "https://terrorschiki.github.io/SKit.github.io/index.html",
    "https://terrorschiki.github.io/SKit.github.io/assets/css/style.css",
    "https://terrorschiki.github.io/SKit.github.io/robots.txt",
    "https://terrorschiki.github.io/SKit.github.io/collections.html",
):
    code, size, hdrs = head(url + ("&" if "?" in url else "?") + "cb=1")
    print(f"  {code}  {size:>8} bytes  x-github-request={hdrs.get('x-github-request-id','-')}  {url}")
