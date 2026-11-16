"""Read-only: why does Gamma /events answer 406? Tries request variants and prints status + body."""
import datetime as dt, json, time, urllib.error, urllib.parse, urllib.request

G = "https://gamma-api.polymarket.com"
now = time.time()
fmt = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
a, b = fmt(now + 3600), fmt(now + 4 * 3600)
UA_OURS = "trading-bot-shadow/0.1 (read-only)"
UA_BROWSER = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def q(d):
    return urllib.parse.urlencode(d)


variants = [
    ("current", f"/events?{q({'active':'true','closed':'false','limit':100,'offset':0,'end_date_min':a,'end_date_max':b})}", UA_OURS, "application/json"),
    ("current, browser UA", f"/events?{q({'active':'true','closed':'false','limit':100,'offset':0,'end_date_min':a,'end_date_max':b})}", UA_BROWSER, "application/json"),
    ("current, Accept */*", f"/events?{q({'active':'true','closed':'false','limit':100,'offset':0,'end_date_min':a,'end_date_max':b})}", UA_OURS, "*/*"),
    ("no offset", f"/events?{q({'active':'true','closed':'false','limit':100,'end_date_min':a,'end_date_max':b})}", UA_OURS, "application/json"),
    ("offset 100", f"/events?{q({'active':'true','closed':'false','limit':100,'offset':100,'end_date_min':a,'end_date_max':b})}", UA_OURS, "application/json"),
    ("limit 50", f"/events?{q({'active':'true','closed':'false','limit':50,'offset':0,'end_date_min':a,'end_date_max':b})}", UA_OURS, "application/json"),
    ("no dates", f"/events?{q({'active':'true','closed':'false','limit':5})}", UA_OURS, "application/json"),
    ("bare limit", "/events?limit=5", UA_OURS, "application/json"),
    ("markets with dates", f"/markets?{q({'active':'true','closed':'false','limit':5,'end_date_min':a,'end_date_max':b})}", UA_OURS, "application/json"),
    ("events/pagination", f"/events/pagination?{q({'active':'true','closed':'false','limit':5,'offset':0,'end_date_min':a,'end_date_max':b})}", UA_OURS, "application/json"),
    ("events/keyset", f"/events/keyset?{q({'active':'true','closed':'false','limit':5,'end_date_min':a,'end_date_max':b})}", UA_OURS, "application/json"),
    ("closed markets (settle path)", "/markets?closed=true&limit=2", UA_OURS, "application/json"),
]
for name, path, ua, accept in variants:
    req = urllib.request.Request(G + path, headers={"Accept": accept, "User-Agent": ua})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            try:
                j = json.loads(body)
                shape = f"list[{len(j)}]" if isinstance(j, list) else f"dict keys={sorted(j.keys())[:8]}"
            except Exception:
                shape = "not json"
            print(f"== {name}: HTTP {r.status} {shape} | {body[:200]!r}", flush=True)
    except urllib.error.HTTPError as e:
        hdrs = {k: v for k, v in e.headers.items() if k.lower() in ("content-type", "server", "x-cache", "cf-ray", "deprecation", "sunset", "link", "warning")}
        print(f"== {name}: HTTP {e.code} {e.reason} headers={hdrs} body={e.read()[:400]!r}", flush=True)
    except Exception as e:
        print(f"== {name}: ERROR {e!r}", flush=True)
    time.sleep(1)
