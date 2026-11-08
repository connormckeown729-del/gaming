#!/usr/bin/env python3
"""Pulls your stats from each game's API and writes stats.json. Keys come from environment variables (GitHub Secrets)."""
import json, os, re, time, urllib.request, urllib.parse
from datetime import datetime, timezone

cfg = json.load(open("config.json"))
UA = "personal-stats-site (github pages)"
DEFAULT_DECK = ["Archer Queen", "Royal Hogs", "Skeletons", "Cannon", "Earthquake", "Fire Spirit", "The Log", "Royal Delivery"]
RARITY = {16: "Common", 14: "Rare", 11: "Epic", 8: "Legendary", 6: "Champion"}

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

def hours_row(key, est=None, lab="estimate"):
    """Time played: self-reported number from config.json if set, otherwise an estimate if one is given."""
    m = (cfg.get("play_hours") or {}).get(key)
    if isinstance(m, (int, float)) and m > 0:
        return [("Time played (self-reported)", f"{m:,.0f} h")]
    if est:
        return [(f"Time played ({lab})", f"~{est:,.0f} h")]
    return []

def ilevel(c):
    """The API reports old per-rarity levels; in-game level = level + (16 - maxLevel)."""
    lv, mx = c.get("level"), c.get("maxLevel")
    return lv + (16 - mx) if isinstance(lv, int) and isinstance(mx, int) else lv

def norm(s):
    return re.sub(r"^the\s+", "", str(s).strip().lower())

def names(lst):
    return ", ".join(str(x.get("name", "")).title() for x in (lst or [])) or "-"

def brawl_table(bs):
    rows_ = [[str(b.get("name", "")).title(), b.get("trophies", 0), b.get("highestTrophies", 0), b.get("rank"), b.get("power"),
              names(b.get("gadgets")), names(b.get("starPowers")), names(b.get("gears")), names(b.get("hyperCharges"))] for b in bs]
    return {"title": f"All brawlers ({len(rows_)})",
            "columns": ["Brawler", "Trophies", "Best", "Rank", "Power", "Gadgets", "Star Powers", "Gears", "Hypercharges"], "rows": rows_}

def brawl(t, token):
    d = get(f"https://bsproxy.royaleapi.dev/v1/players/{tag(t)}", token)
    bs = sorted(d.get("brawlers", []), key=lambda b: -b.get("trophies", 0))
    vic = sum(d.get(k) or 0 for k in ("3vs3Victories", "soloVictories", "duoVictories"))
    est = vic * 2 * 2.5 / 60 if vic else None
    out = {"title": "Brawl Stars", "metric": "Trophies", "value": d["trophies"], "name": d.get("name", ""),
           "sub": f"Best: {d['highestTrophies']:,}" if "highestTrophies" in d else "",
           "details": rows(*hours_row("brawl", est, "rough estimate"), ("Level", d.get("expLevel")), ("Prestige", d.get("totalPrestigeLevel")),
                           ("3v3 wins", d.get("3vs3Victories")), ("Solo wins", d.get("soloVictories")),
                           ("Duo wins", d.get("duoVictories")), ("Brawlers unlocked", len(bs) or None),
                           ("Club", dig(d, "club", "name"))),
           "top_title": "Top brawlers",
           "top": [f"{str(b.get('name', '')).title()} · {b.get('trophies', 0):,} trophies · rank {b.get('rank', '?')} · power {b.get('power', '?')}" for b in bs[:5]]}
    try:
        out["table"] = brawl_table(bs)
    except Exception as e:
        print("brawl table skipped:", type(e).__name__)
    return out

def royale(t, token):
    d = get(f"https://proxy.royaleapi.dev/v1/players/{tag(t)}", token)
    w, l, bc = d.get("wins"), d.get("losses"), d.get("battleCount")
    out = {"title": "Clash Royale", "metric": "Trophies", "value": d["trophies"], "name": d.get("name", ""),
           "sub": f"Best: {d['bestTrophies']:,}" if "bestTrophies" in d else "", "details": [], "top_title": "Your deck", "top": []}
    avg = None
    try:
        lookup = {norm(c.get("name", "")): c for c in d.get("cards", [])}
        elixir = []
        for name in (cfg.get("clash_deck") or DEFAULT_DECK):
            c = lookup.get(norm(name))
            if not c:
                out["top"].append(f"{name} · not found in your collection")
                continue
            if isinstance(c.get("elixirCost"), (int, float)):
                elixir.append(c["elixirCost"])
            rar = str(c.get("rarity") or RARITY.get(c.get("maxLevel"), "")).title()
            out["top"].append(" · ".join(x for x in [c.get("name", name), f"level {ilevel(c)}", rar, f"{c['elixirCost']} elixir" if c.get("elixirCost") is not None else ""] if x))
        avg = round(sum(elixir) / len(elixir), 1) if elixir else None
    except Exception as e:
        print("deck skipped:", type(e).__name__)
    est = bc * 3 / 60 if isinstance(bc, int) else None
    out["details"] = rows(*hours_row("clash", est), ("Level", d.get("expLevel")), ("Wins", w), ("Losses", l), ("Win rate", pct(w, l)),
                          ("Battles", bc), ("Avg deck elixir", avg), ("Clan", dig(d, "clan", "name")))
    return out

def clans(t, token):
    d = get(f"https://cocproxy.royaleapi.dev/v1/players/{tag(t)}", token)
    return {"title": "Clash of Clans", "metric": "Trophies", "value": d["trophies"], "name": d.get("name", ""),
            "sub": f"Best: {d['bestTrophies']:,}" if "bestTrophies" in d else "",
            "details": rows(*hours_row("clash"), ("Level", d.get("expLevel")), ("Town Hall", d.get("townHallLevel")), ("War stars", d.get("warStars")),
                            ("Attack wins", d.get("attackWins")), ("Defense wins", d.get("defenseWins")),
                            ("Donations", d.get("donations")), ("Clan", dig(d, "clan", "name")))}

def tetrio(user):
    base = "https://ch.tetr.io/api/users/" + urllib.parse.quote(user.strip().lower())
    hrs = None
    try:
        hrs = (get(base).get("data") or {}).get("gametime")
    except Exception as e:
        print("tetrio profile skipped:", type(e).__name__)
    tpl = [("Time played", f"{hrs / 3600:,.0f} h")] if isinstance(hrs, (int, float)) and hrs > 0 else []
    time.sleep(1)
    d = get(base + "/summaries/league").get("data") or {}
    tr = d.get("tr")
    if tr is None or tr < 0:
        return {"title": "TETR.IO", "metric": "Tetra Rating", "value": None, "name": user, "sub": "Unranked (needs 10 league games)", "details": rows(*tpl)}
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
    return {"title": "TETR.IO", "metric": "Tetra Rating", "value": round(tr), "name": user,
            "sub": f"Rank {rank}" if rank and rank != "Z" else "",
            "details": rows(*tpl, ("Best rank", str(d.get("bestrank", "")).upper() or None),
                            ("GXE", f"{d['gxe']:.1f}%" if isinstance(d.get("gxe"), (int, float)) else None),
                            ("Glicko", round(d["glicko"]) if isinstance(d.get("glicko"), (int, float)) else None),
                            ("APM", d.get("apm")), ("PPS", d.get("pps")), ("VS", d.get("vs")),
                            ("League games", gp), ("League wins", gw), ("League win rate", pct(gw, (gp - gw) if isinstance(gp, int) and isinstance(gw, int) else None)),
                            ("Global standing", d.get("standing")), *extra)}

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
        print(f"{key} failed: {type(e).__name__}: {e}")
        games[key] = dict(old.get(key) or {"title": key, "metric": "", "value": None, "name": "", "sub": "", "details": []}, stale=True)

json.dump({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "games": games}, open("stats.json", "w"), indent=2)
print("stats.json written")
