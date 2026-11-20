"""Read-only: what does Polymarket say about the lab's positions still open 3+ days after their market ended?
Public data only (no keys). Prints one line per market."""
import json, time, urllib.parse, urllib.request

G = "https://gamma-api.polymarket.com"
UA = "trading-bot-shadow/0.1 (read-only)"
STATE = "https://raw.githubusercontent.com/ft1219/metabot/polymarket-lab-data/state.json"


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


now = time.time()
state = get(STATE)
stale = [p for p in state["positions"] if now - p.get("ends_at", now) > 3 * 86400]
print(f"open positions {len(state['positions'])}, stale {len(stale)}", flush=True)
ids = sorted({leg["condition_id"] for p in stale for leg in p["legs"]})
seen = {}
for i in range(0, len(ids), 20):
    q = "&".join(f"condition_ids={c}" for c in ids[i:i + 20])
    for closed in ("", "&closed=true"):
        for r in get(f"{G}/markets?limit=50{closed}&{q}"):
            seen.setdefault(r.get("conditionId"), {}).update({"via_closed" if closed else "via_plain": True, **r})
KEYS = ["closed", "active", "archived", "acceptingOrders", "endDate", "closedTime", "umaResolutionStatus",
        "umaResolutionStatuses", "outcomePrices", "automaticallyResolved", "resolvedBy", "via_plain", "via_closed"]
for c in ids:
    m = seen.get(c)
    who = [f"{p['strategy']}" for p in stale for leg in p["legs"] if leg["condition_id"] == c]
    if not m:
        print(f"-- {c[:12]} NOT FOUND (held by {who})", flush=True)
        continue
    print(f"-- {(m.get('question') or '')[:90]} | held by {who}", flush=True)
    print("   " + json.dumps({k: m.get(k) for k in KEYS}), flush=True)
