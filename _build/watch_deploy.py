# -*- coding: utf-8 -*-
"""Watch the Pages workflow and probe the live site until it serves content."""
import json, subprocess, sys, time, urllib.error, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
REPO = "Terrorschiki/SKit.github.io"
SITE = "https://terrorschiki.github.io/SKit.github.io"

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


def probe(url, want_substr=None):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                               "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            ok = want_substr is None or want_substr.encode() in body
            return r.status, len(body), ok
    except urllib.error.HTTPError as e:
        return e.code, 0, False
    except Exception as e:
        return str(e), 0, False


run_id = None
print("watching workflow 'Deploy static site to Pages' ...")
for i in range(1, 31):
    s, runs = api(f"/repos/{REPO}/actions/runs?per_page=5")
    wf = [r for r in (runs or {}).get("workflow_runs", []) if r["name"] == "Deploy static site to Pages"]
    if not wf:
        print(f"  [{i:2d}] workflow run not registered yet (status={s})")
        time.sleep(12)
        continue
    r0 = wf[0]
    run_id = r0["id"]
    print(f"  [{i:2d}] {r0['status']:<12} {str(r0.get('conclusion')):<9} sha={r0['head_sha'][:8]} "
          f"steps={r0.get('run_attempt')}")
    if r0["status"] == "completed":
        print(f"\nworkflow conclusion: {r0.get('conclusion')}")
        print(f"run url: {r0['html_url']}")
        if r0.get("conclusion") != "success":
            s2, jobs = api(f"/repos/{REPO}/actions/runs/{run_id}/jobs")
            for j in (jobs or {}).get("jobs", []):
                print(f"  job {j['name']}: {j.get('conclusion')}")
                for st in j.get("steps", []):
                    print(f"     {st['name'][:46]:<46} {st.get('conclusion')}")
        break
    time.sleep(12)

print("\nwaiting for the CDN to serve the new deployment ...")
paths = [("/", "SKit"), ("/collections.html", "Collections"),
         ("/collections/silicone-nylon-kitchenware.html", "Silicone"),
         ("/products/l-l01.html", "L01"),
         ("/data/catalog.json", "products"),
         ("/assets/css/style.css", "--copper"),
         ("/sitemap.xml", "urlset"), ("/robots.txt", "Sitemap")]
for attempt in range(1, 21):
    results = [(path, *probe(SITE + path, needle)) for path, needle in paths]
    good = sum(1 for _, code, _, ok in results if code == 200 and ok)
    print(f"  [{attempt:2d}] {good}/{len(paths)} paths serving expected content")
    if good == len(paths):
        print("\nLIVE SITE OK:")
        for path, code, size, ok in results:
            print(f"   {code}  {size:>7} bytes  {path}")
        break
    time.sleep(15)
else:
    print("\nstill not fully live; last probe:")
    for path, code, size, ok in results:
        print(f"   {code}  {size:>7} bytes  ok={ok}  {path}")
