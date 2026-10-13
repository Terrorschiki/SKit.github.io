# -*- coding: utf-8 -*-
"""Determine whether Terrorschiki is a User or an Organization, and what that
means for the Pages URL."""
import json, subprocess, sys, urllib.error, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
NAME = "Terrorschiki"

p = subprocess.run(["git", "credential", "fill"],
                   input="protocol=https\nhost=github.com\n\n",
                   capture_output=True, text=True)
TOKEN = dict(l.split("=", 1) for l in p.stdout.splitlines() if "=" in l)["password"]


def api(path, auth=True):
    h = {"User-Agent": "dsh", "Accept": "application/vnd.github+json"}
    if auth:
        h["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request("https://api.github.com" + path, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, None


print("=== 1. /users/%s  (个人账号端点) ===" % NAME)
s, u = api(f"/users/{NAME}")
print("status:", s)
if s == 200:
    print("  login      :", u.get("login"))
    print("  type       :", u.get("type"), " <-- User / Organization / Bot")
    print("  name       :", u.get("name"))
    print("  company    :", u.get("company"))
    print("  blog       :", u.get("blog"))
    print("  public_repos:", u.get("public_repos"))
    print("  created_at :", u.get("created_at"))

print("\n=== 2. /orgs/%s  (组织端点) ===" % NAME)
s2, o = api(f"/orgs/{NAME}")
print("status:", s2, "(404 = 不是组织)")
if s2 == 200:
    print("  login:", o.get("login"), "| type:", o.get("type"))

print("\n=== 3. /users/%s/orgs  (该账号所属的组织) ===" % NAME)
s3, orgs = api(f"/users/{NAME}/orgs")
print("status:", s3, "| count:", len(orgs) if isinstance(orgs, list) else orgs)
for g in (orgs or []):
    print("   member of org:", g.get("login"))

print("\n=== 4. 我自己的身份 /user ===")
s4, me = api("/user")
print("  login:", me.get("login"), "| type:", me.get("type"), "| name:", me.get("name"))

print("\n=== 5. 仓库归属 /repos/%s/SKit.github.io ===" % NAME)
s5, repo = api(f"/repos/{NAME}/SKit.github.io")
if s5 == 200:
    owner = repo.get("owner", {})
    print("  full_name      :", repo.get("full_name"))
    print("  owner.login    :", owner.get("login"))
    print("  owner.type     :", owner.get("type"), " <-- 决定仓库归属方")
    print("  owner.site_admin:", owner.get("site_admin"))
    print("  permissions    :", repo.get("permissions"))
    print("  visibility     :", repo.get("visibility"))

print("\n=== 6. 结论 ===")
owner_type = (repo or {}).get("owner", {}).get("type") if s5 == 200 else None
if owner_type == "Organization":
    print("  仓库属于【组织】Terrorschiki")
    print("  -> 项目站地址规则与个人账号相同: https://terrorschiki.github.io/SKit.github.io/")
    print("  -> 只有当仓库名恰好是 Terrorschiki.github.io 时才会占用根域名")
elif owner_type == "User":
    print("  仓库属于【个人账号】Terrorschiki（type=User）")
    print("  -> 项目站: https://terrorschiki.github.io/SKit.github.io/")
else:
    print("  无法判定:", s5, repo)
