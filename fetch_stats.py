#!/usr/bin/env python3
"""Pulls your stats from each game's API and writes stats.json. Keys come from environment variables (GitHub Secrets)."""
import json, os, time, urllib.request, urllib.parse
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

def dig(d, *keys):
    for k in keys:
        d = d.get(k) if isinstance(d, dict) else None
    return d

def fmt(n):
    return f"{n:,}" if isinstance(n, int) else (f"{n:,.2f}" if isinstance(n, float) else str(n))

def rows(*pairs):
    return [[k, fmt(v)] for k, v in pairs if v not in (None, "", -1)]

def pct(a, b):
    return f"{100 * a / (a + b):.1f}%" if isinstance(a, int) and isinstance(b, int) and a + b else None

def brawl(t, token):
    d = get(f"https://bsproxy.royaleapi.dev/v1/players/{tag(t)}", token)
    bs = sorted(d.get("brawlers", []), key=lambda b: -b.get("trophies", 0))
    return {"title": "Brawl Stars", "metric": "Trophies", "value": d["trophies"], "name": d.get("name", ""),
            "sub": f"Best: {d['highestTrophies']:,}" if "highestTrophies" in d else "",
            "details": rows(("Level", d.get("expLevel")), ("Prestige", d.get("totalPrestigeLevel")),
                            ("3v3 wins", d.get("3vs3Victories")), ("Solo wins", d.get("soloVictories")),
                            ("Duo wins", d.get("duoVictories")), ("Brawlers unlocked", len(bs) or None),
                            ("Club", dig(d, "club", "name"))),
            "top_title": "Top brawlers",
            "top": [f"{str(b.get('name', '')).title()} · {b.get('trophies', 0):,} trophies · rank {b.get('rank', '?')} · power {b.get('power', '?')}" for b in bs[:5]]}

def royale(t, token):
    d = get(f"https://proxy.royaleapi.dev/v1/players/{tag(t)}", token)
    pol = d.get("currentPathOfLegendSeasonResult") or {}
    best = d.get("bestPathOfLegendSeasonResult") or {}
    return {"title": "Clash Royale", "metric": "Trophies", "value": d["trophies"], "name": d.get("name", ""),
            "sub": f"Best: {d['bestTrophies']:,}" if "bestTrophies" in d else "",
            "details": rows(("Level", d.get("expLevel")), ("Wins", d.get("wins")), ("Losses", d.get("losses")),
                            ("Win rate", pct(d.get("wins"), d.get("losses"))), ("Three-crown wins", d.get("threeCrownWins")),
                            ("Battles", d.get("battleCount")), ("Arena", dig(d, "arena", "name")),
                            ("Path of Legend league", pol.get("leagueNumber")), ("Path of Legend best league", best.get("leagueNumber")),
                            ("Donations", d.get("totalDonations")), ("Clan", dig(d, "clan", "name"))),
            "top_title": "Current deck",
            "top": [f"{c.get('name')} · level {c.get('level')}" for c in d.get("currentDeck", [])]}

def clans(t, token):
    d = get(f"https://cocproxy.royaleapi.dev/v1/players/{tag(t)}", token)
    return {"title": "Clash of Clans", "metric": "Trophies", "value": d["trophies"], "name": d.get("name", ""),
            "sub": f"Best: {d['bestTrophies']:,}" if "bestTrophies" in d else "",
            "details": rows(("Level", d.get("expLevel")), ("Town Hall", d.get("townHallLevel")), ("War stars", d.get("warStars")),
                            ("Attack wins", d.get("attackWins")), ("Defense wins", d.get("defenseWins")),
                            ("Donations", d.get("donations")), ("Clan", dig(d, "clan", "name")))}

def tetrio(user):
    base = "https://ch.tetr.io/api/users/" + urllib.parse.quote(user.strip().lower())
    d = get(base + "/summaries/league").get("data") or {}
    tr = d.get("tr")
    if tr is None or tr < 0:
        return {"title": "TETR.IO", "metric": "Tetra Rating", "value": None, "name": user, "sub": "Unranked (needs 10 league games)", "details": []}
    rank = str(d.get("rank", "")).upper()
    gp, gw = d.get("gamesplayed"), d.get("gameswon")
    extra = []
    for path, label, conv in [("/summaries/40l", "40 LINES best", lambda ms: f"{ms / 1000:.3f}s"), ("/summaries/blitz", "BLITZ best", lambda s: f"{s:,}")]:
        time.sleep(1)
        try:
            r = get(base + path).get("data") or {}
            v = dig(r, "record", "results", "stats", "finaltime" if "40l" in path else "score")
            if isinstance(v, (int, float)):
                extra.append((label, conv(v)))
        except Exception:
            pass
    time.sleep(1)
    try:
        u = get(base).get("data") or {}
        hrs = u.get("gametime")
        extra += [("XP", round(u["xp"]) if isinstance(u.get("xp"), (int, float)) else None),
                  ("Time played", f"{hrs / 3600:,.0f} h" if isinstance(hrs, (int, float)) and hrs > 0 else None)]
    except Exception:
        pass
    return {"title": "TETR.IO", "metric": "Tetra Rating", "value": round(tr), "name": user,
            "sub": f"Rank {rank}" if rank and rank != "Z" else "",
            "details": rows(("Best rank", str(d.get("bestrank", "")).upper() or None),
                            ("GXE", f"{d['gxe']:.1f}%" if isinstance(d.get("gxe"), (int, float)) else None),
                            ("Glicko", round(d["glicko"]) if isinstance(d.get("glicko"), (int, float)) else None),
                            ("APM", d.get("apm")), ("PPS", d.get("pps")), ("VS", d.get("vs")),
                            ("League games", gp), ("League wins", gw), ("League win rate", pct(gw, (gp - gw) if isinstance(gp, int) and isinstance(gw, int) else None)),
                            ("Global standing", d.get("standing"))) + rows(*extra)}

royale_mode = cfg.get("clash_kind", "royale") != "clans"
jobs = {
    "brawl": lambda: brawl(cfg["brawl_stars_tag"], os.environ["BRAWLSTARS_TOKEN"]),
    "clash": lambda: (royale if royale_mode else clans)(cfg["clash_tag"], os.environ["CLASH_TOKEN"]),
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
        games[key] = dict(old.get(key) or {"title": key, "metric": "", "value": None, "name": "", "sub": "", "details": []}, stale=True)

json.dump({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "games": games}, open("stats.json", "w"), indent=2)
print("stats.json written")
