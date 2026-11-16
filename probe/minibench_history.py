"""Read-only: our past MiniBench rounds (project ids from our forecasts) and their leaderboards."""
import json, os, time, urllib.error, urllib.request
from collections import Counter

TOKEN = os.environ["METACULUS_TOKEN"]
BASE = "https://www.metaculus.com/api"
DEADLINE = time.time() + 20 * 60


def get(path):
    for attempt in range(3):
        if time.time() > DEADLINE:
            return None, "out of time"
        time.sleep(6)
        req = urllib.request.Request(BASE + path, headers={"Accept": "application/json", "Authorization": f"Token {TOKEN}"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("   (429, waiting)", flush=True)
                time.sleep(60)
                continue
            return e.code, e.read()[:200].decode(errors="replace")
        except Exception as e:
            return None, repr(e)[:200]
    return 429, "still rate limited"


status, me = get("/users/me")
uid = me["id"]
projects = Counter()
names = {}
for st in ("resolved", "closed"):
    for page in range(6):
        status, body = get(f"/posts/?forecaster_id={uid}&statuses={st}&limit=100&offset={page*100}")
        if status != 200 or not isinstance(body, dict):
            print(f"posts {st} page {page}: HTTP {status} {str(body)[:120]}", flush=True)
            break
        res = body.get("results") or []
        for p in res:
            for key in ("tournament", "question_series"):
                for t in ((p.get("projects") or {}).get(key) or []):
                    if t.get("id") != 33121:
                        projects[t.get("id")] += 1
                        names[t.get("id")] = (t.get("slug"), t.get("name"), t.get("start_date"), t.get("close_date"), t.get("prize_pool"))
        if len(res) < 100:
            break
print("== our non-FutureEval projects:", flush=True)
for pid, n in sorted(projects.items()):
    print(f"   {pid}\tposts={n}\t{names.get(pid)}", flush=True)

for pid in sorted(projects):
    status, body = get(f"/leaderboards/project/{pid}/")
    if status != 200 or not isinstance(body, list):
        print(f"== LB {pid}: HTTP {status} {str(body)[:120]}", flush=True)
        continue
    for lb in body:
        ents = lb.get("entries") or []
        print(f"== LB project={pid} id={lb.get('id')} type={lb.get('score_type')} pool={lb.get('prize_pool')} finalized={lb.get('finalized')} "
              f"max_coverage={lb.get('max_coverage')} entries={len(ents)}", flush=True)
        paid = [e for e in ents if (e.get("prize") or 0) > 0]
        print(f"   paid={len(paid)} min_paid={min((e['prize'] for e in paid), default=None)} sum_paid={round(sum(e['prize'] for e in paid), 2)}", flush=True)
        for e in ents:
            u = e.get("user") or {}
            name = u.get("username") or e.get("aggregation_method") or ""
            if e.get("rank") and (e["rank"] <= 25 or u.get("id") == uid or name.startswith("metac-claude-sonnet") or name.startswith("metac-gpt-6-sol") or name.startswith("metac-deepseek")):
                print(f"MB\t{pid}\t{e.get('rank')}\t{round(e.get('score') or 0, 2)}\t{e.get('prize')}\t{e.get('contribution_count')}\t{'OURS' if u.get('id') == uid else ''}\t{name}", flush=True)
