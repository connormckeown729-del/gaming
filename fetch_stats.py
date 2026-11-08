#!/usr/bin/env python3
"""Pulls your stats from each game's API and writes stats.json. Keys come from environment variables (GitHub Secrets)."""
import json, os, urllib.request, urllib.parse
from datetime import datetime, timezone

cfg = json.load(open("config.json"))
UA = "personal-stats-site (github pages)"

def get(url, token=None):
    h = {"User-Agent": UA, "Accept": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=20) as r:
        return json.load(r)

def tag(t):
    return urllib.parse.quote("#" + t.strip().lstrip("#").upper())

def supercell(title, host, t, token, best_key):
    d = get(f"https://{host}/v1/players/{tag(t)}", token)
    return {"title": title, "metric": "Trophies", "value": d["trophies"], "name": d.get("name", ""),
            "sub": f"Best: {d[best_key]:,}" if best_key in d else ""}

def tetrio(user):
    r = get(f"https://ch.tetr.io/api/users/{urllib.parse.quote(user.strip().lower())}/summaries/league")
    d = r.get("data") or {}
    tr = d.get("tr", (d.get("league") or {}).get("tr"))
    if tr is None or tr < 0:
        return {"title": "TETR.IO", "metric": "Tetra Rating", "value": None, "name": user, "sub": "Unranked (needs 10 league games)"}
    rank = str(d.get("rank", "")).upper()
    gxe = d.get("gxe")
    sub = " · ".join(x for x in [f"Rank {rank}" if rank and rank != "Z" else "", f"GXE {gxe:.1f}%" if isinstance(gxe, (int, float)) and gxe >= 0 else ""] if x)
    return {"title": "TETR.IO", "metric": "Tetra Rating", "value": round(tr), "name": user, "sub": sub}

royale = cfg.get("clash_kind", "royale") != "clans"
jobs = {
    "brawl": lambda: supercell("Brawl Stars", "bsproxy.royaleapi.dev", cfg["brawl_stars_tag"], os.environ["BRAWLSTARS_TOKEN"], "highestTrophies"),
    "clash": lambda: supercell("Clash Royale" if royale else "Clash of Clans",
                               "proxy.royaleapi.dev" if royale else "cocproxy.royaleapi.dev",
                               cfg["clash_tag"], os.environ["CLASH_TOKEN"], "bestTrophies"),
    "tetrio": lambda: tetrio(cfg["tetrio_username"]),
}

old = {}
if cfg.get("site_url"):
    try:
        old = get(cfg["site_url"].rstrip("/") + "/stats.json").get("games", {})
    except Exception:
        pass

games = {}
for key, job in jobs.items():
    try:
        games[key] = job()
    except Exception as e:
        print(f"{key} failed: {type(e).__name__}")
        games[key] = dict(old.get(key) or {"title": key, "metric": "", "value": None, "name": "", "sub": ""}, stale=True)

json.dump({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "games": games}, open("stats.json", "w"), indent=2)
print("stats.json written")
