"""Read-only: which providers served this OpenRouter account's requests, per model and day
(OpenRouter's /api/v1/activity: the last 30 completed UTC days). Prints request and token
counts only; no key, prompt or personal data is printed."""
import collections, json, os, urllib.error, urllib.request

key = os.environ["OPENROUTER_API_KEY"].strip()


def get(path):
    req = urllib.request.Request("https://openrouter.ai" + path, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


try:
    rows = get("/api/v1/activity").get("data", [])
except urllib.error.HTTPError as e:
    try:
        msg = json.loads(e.read()).get("error", {}).get("message", "")[:200]
    except Exception:
        msg = ""
    print(f"== /api/v1/activity: HTTP {e.code} {msg}", flush=True)
    raise SystemExit(0)

print(f"== {len(rows)} rows; fields: {sorted(rows[0].keys()) if rows else []}", flush=True)
by_prov, by_pm, gmi_days = collections.Counter(), collections.Counter(), collections.Counter()
for r in rows:
    prov = r.get("provider_name") or "?"
    model = r.get("model") or r.get("model_permaslug") or "?"
    n = int(r.get("requests") or 0)
    by_prov[prov] += n
    by_pm[(prov, model)] += n
    if "gmi" in prov.lower():
        gmi_days[(r.get("date") or "?")[:10], model] += n
dates = sorted({(r.get("date") or "")[:10] for r in rows})
print(f"== dates covered: {dates[:1]} .. {dates[-1:]}", flush=True)
print("== requests by provider:", flush=True)
for p, n in by_prov.most_common():
    print(f"   {n:6d}  {p}", flush=True)
print("== requests by provider and model:", flush=True)
for (p, m), n in sorted(by_pm.items(), key=lambda x: (-x[1])):
    print(f"   {n:6d}  {p:28s} {m}", flush=True)
print(f"== GMI requests by day and model (total {sum(gmi_days.values())}):", flush=True)
for (d, m), n in sorted(gmi_days.items()):
    print(f"   {d}  {n:5d}  {m}", flush=True)
