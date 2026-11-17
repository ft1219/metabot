"""Read-only: when Fall 2026 FutureEval questions open, per week and month,
which ones are scheduled next, and how many of them the bot forecast.
Few, slow requests. Prints no secrets."""
import json, os, time, urllib.error, urllib.parse, urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone

TOKEN = os.environ["METACULUS_TOKEN"]
BASE = "https://www.metaculus.com/api"
TOURNAMENT = 33121
PAGE = 100


def get(url):
    for _ in range(4):
        time.sleep(6)
        req = urllib.request.Request(
            url, headers={"Accept": "application/json", "Authorization": f"Token {TOKEN}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(60)
                continue
            return e.code, e.read()[:200].decode(errors="replace")
        except Exception as e:
            return None, repr(e)[:200]
    return 429, "still rate limited"


def when(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def fetch(params, label, max_pages=10):
    posts, offset = [], 0
    for _ in range(max_pages):
        q = dict(params, limit=PAGE, offset=offset)
        status, body = get(f"{BASE}/posts/?{urllib.parse.urlencode(q, doseq=True)}")
        if status != 200 or not isinstance(body, dict):
            print(f"== {label}: HTTP {status} {str(body)[:150]}", flush=True)
            break
        results = body.get("results") or []
        posts.extend(results)
        if len(results) < PAGE:
            break
        offset += PAGE
    print(f"== {label}: {len(posts)} post(s)", flush=True)
    return posts


now = datetime.now(timezone.utc)
print(f"now {now:%Y-%m-%d %H:%M} UTC", flush=True)

seen = {}
for st in ["upcoming", "open", "closed", "resolved"]:
    for p in fetch({"tournaments": TOURNAMENT, "statuses": st, "order_by": "open_time"}, f"status={st}"):
        seen[p["id"]] = p
for p in fetch({"tournaments": TOURNAMENT, "order_by": "open_time"}, "no status filter"):
    seen.setdefault(p["id"], p)
print(f"== distinct posts: {len(seen)}", flush=True)

rows = []
for p in seen.values():
    q = p.get("question") or {}
    ot = when(q.get("open_time") or p.get("open_time"))
    ct = when(q.get("scheduled_close_time") or p.get("scheduled_close_time"))
    rows.append((ot, ct, p["id"], p.get("status") or q.get("status"), q.get("type")))
rows = [r for r in rows if r[0]]
rows.sort()
if rows:
    print(f"first open {rows[0][0]:%Y-%m-%d %H:%M}, last open {rows[-1][0]:%Y-%m-%d %H:%M}", flush=True)

by_month, by_week, by_day, hours_open, types = Counter(), Counter(), Counter(), Counter(), Counter()
for ot, ct, pid, st, typ in rows:
    by_month[f"{ot:%Y-%m}"] += 1
    monday = (ot - timedelta(days=ot.weekday())).date()
    by_week[str(monday)] += 1
    by_day[str(ot.date())] += 1
    types[typ] += 1
    if ct:
        hours_open[round((ct - ot).total_seconds() / 3600, 1)] += 1
print("== opened per month:", dict(sorted(by_month.items())), flush=True)
print("== opened per week (Monday):", dict(sorted(by_week.items())), flush=True)
print("== opened per day:", dict(sorted(by_day.items())), flush=True)
print("== hours open:", dict(sorted(hours_open.items())), flush=True)
print("== question types:", dict(types), flush=True)
print("== open hour (UTC) counts:", dict(sorted(Counter(r[0].hour for r in rows).items())), flush=True)

future = [r for r in rows if r[0] > now]
print(f"== scheduled to open after now: {len(future)}", flush=True)
for ot, ct, pid, st, typ in future[:40]:
    print(f"   {ot:%Y-%m-%d %H:%M} UTC -> closes {ct:%Y-%m-%d %H:%M} | {pid} {st} {typ}", flush=True)
if future:
    fm = Counter(f"{r[0]:%Y-%m}" for r in future)
    print("   future per month:", dict(sorted(fm.items())), flush=True)

status, me = get(BASE + "/users/me")
if status == 200 and isinstance(me, dict):
    mine = fetch({"tournaments": TOURNAMENT, "forecaster_id": me["id"], "order_by": "open_time"}, "forecast by the bot")
    mm = Counter()
    for p in mine:
        q = p.get("question") or {}
        ot = when(q.get("open_time") or p.get("open_time"))
        if ot:
            mm[f"{ot:%Y-%m}"] += 1
    print("== bot forecasts per month (by open time):", dict(sorted(mm.items())), flush=True)
else:
    print(f"== users/me: HTTP {status}", flush=True)
