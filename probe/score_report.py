"""Read-only: prints the bot's leaderboard rows and resolved-question scores.
Makes few, slow requests because Metaculus rate-limits fast callers."""
import json, os, time, urllib.error, urllib.request

TOKEN = os.environ["METACULUS_TOKEN"]
BASE = "https://www.metaculus.com/api"
DEADLINE = time.time() + 12 * 60


def get(path):
    url = path if path.startswith("http") else BASE + path
    for attempt in range(3):
        if time.time() > DEADLINE:
            return None, "out of time"
        time.sleep(8)
        req = urllib.request.Request(url, headers={"Accept": "application/json", "Authorization": f"Token {TOKEN}"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"   (429 on {path}, waiting)", flush=True)
                time.sleep(60)
                continue
            return e.code, e.read()[:200].decode(errors="replace")
        except Exception as e:
            return None, repr(e)[:200]
    return 429, "still rate limited"


def row(e):
    u = e.get("user") or {}
    return (f"rank={e.get('rank')} score={round(e.get('score') or 0, 2)} take={round(e.get('take') or 0, 3)} "
            f"prize={e.get('prize')} questions={e.get('contribution_count')} coverage={e.get('coverage')} "
            f"user={u.get('username') or e.get('aggregation_method')}")


def leaderboard(pid, uid, uname):
    for path in (f"/leaderboards/project/{pid}/", f"/projects/{pid}/leaderboard/"):
        status, body = get(path)
        if status == 200 and isinstance(body, list):
            print(f"== {path}: a list of {len(body)} leaderboard(s); first item keys={sorted(body[0].keys()) if body else None}", flush=True)
            for lb in body:
                ents = lb.get("entries")
                print(f"   lb id={lb.get('id')} name={lb.get('name')!r} score_type={lb.get('score_type')!r} primary={lb.get('is_primary_leaderboard') or lb.get('primary')!r} "
                      f"finalized={lb.get('finalized')!r} prize_pool={lb.get('prize_pool')!r} entries={len(ents) if isinstance(ents, list) else ents!r}", flush=True)
            for lb in body:
                ents = lb.get("entries")
                if not isinstance(ents, list):
                    st2, lb = get(f"/leaderboards/{lb.get('id')}/")
                    print(f"   /leaderboards/{{id}}/ -> HTTP {st2} keys={sorted(lb.keys()) if isinstance(lb, dict) else str(lb)[:80]}", flush=True)
                    if not isinstance(lb, dict):
                        continue
                    ents = lb.get("entries") or []
                print(f"   --- leaderboard {lb.get('name')!r}: {len(ents)} entries", flush=True)
                for e in ents[:5]:
                    print("   top", row(e))
                for e in ents:
                    u = e.get("user") or {}
                    if u.get("id") == uid or u.get("username") == uname:
                        print("   >>> OURS", row(e), f"of {len(ents)}")
                for e in ents:
                    if ((e.get("user") or {}).get("username") or "").lower().startswith("metac-"):
                        print("   metac", row(e))
                for k in ("userEntry", "user_entry"):
                    if lb.get(k):
                        print("   user_entry", row(lb[k]))
            return
        if status != 200 or not isinstance(body, dict):
            print(f"== leaderboard {path}: HTTP {status} {str(body)[:100]}", flush=True)
            continue
        entries = body.get("entries") or []
        print(f"== leaderboard {path}: keys={sorted(body.keys())} entries={len(entries)} "
              f"score_type={body.get('score_type')!r} finalized={body.get('finalized')!r} prize_pool={body.get('prize_pool')!r}", flush=True)
        for e in entries[:5]:
            print("   top", row(e))
        for e in entries:
            u = e.get("user") or {}
            if u.get("id") == uid or u.get("username") == uname:
                print("   >>> OURS", row(e), f"of {len(entries)}")
        for e in entries:
            if ((e.get("user") or {}).get("username") or "").lower().startswith("metac-"):
                print("   metac", row(e))
        for k in ("userEntry", "user_entry"):
            if body.get(k):
                print("   user_entry", row(body[k]))
        print(flush=True)
        return


status, me = get("/users/me")
uid, uname = me.get("id"), me.get("username")
print(f"== me: id={uid} username={uname}", flush=True)

leaderboard(33121, uid, uname)

# Main tournament: our resolved questions, their scores and when we forecast them.
rows, url = [], f"/posts/?tournaments=33121&forecaster_id={uid}&statuses=resolved&limit=100"
while url:
    status, body = get(url)
    if status != 200 or not isinstance(body, dict):
        print("main-tournament posts:", status, str(body)[:150])
        break
    for post in body.get("results", []):
        for q in [post.get("question")] + [x for x in ((post.get("group_of_questions") or {}).get("questions") or [])]:
            if not q:
                continue
            mf = q.get("my_forecasts") or {}
            sd = mf.get("score_data") or {}
            hist = mf.get("history") or []
            first = min((h.get("start_time") for h in hist if h.get("start_time")), default=None)
            if not rows:
                print("   score_data keys:", sorted(sd.keys()), "| history keys:", sorted(hist[0].keys()) if hist else None, flush=True)
            rows.append((q.get("id"), first, q.get("resolution"), sd, (post.get("title") or "")[:50], q.get("actual_resolve_time") or q.get("resolution_set_time")))
    url = body.get("next")
print(f"== main-tournament resolved questions we forecast: {len(rows)}", flush=True)
for qid, first, res, sd, title, rt in sorted(rows, key=lambda r: str(r[1])):
    def g(k):
        v = sd.get(k)
        return None if v is None else round(v, 1)
    first_s = first if isinstance(first, str) else (__import__("datetime").datetime.utcfromtimestamp(first).strftime("%Y-%m-%dT%H:%MZ") if first else None)
    print(f"ROW\t{qid}\t{first_s}\t{res}\tspot_peer={g('spot_peer_score')}\tpeer={g('peer_score')}\tspot_base={g('spot_baseline_score')}\tbase={g('baseline_score')}\t{title}", flush=True)

# MiniBench: find its current project id from one of our MiniBench posts, then its scores and leaderboard.
status, body = get(f"/posts/?tournaments=minibench&forecaster_id={uid}&statuses=resolved&limit=50")
if status == 200:
    res = body.get("results", [])
    pids = set()
    print(f"== minibench posts we forecast: {len(res)} (count={body.get('count')}) next={body.get('next')!r}", flush=True)
    if res:
        print("   first post projects:", json.dumps(res[0].get("projects"))[:700], flush=True)
        from collections import Counter
        print("   statuses:", Counter(((p.get("question") or {}).get("status")) for p in res), flush=True)
    for post in res:
        for key in ("tournament", "question_series"):
            for t in ((post.get("projects") or {}).get(key) or []):
                pids.add((t.get("id"), t.get("slug")))
        q = post.get("question") or {}
        sd = ((q.get("my_forecasts") or {}).get("score_data")) or {}
        if q.get("status") == "resolved":
            print(f"   q{q.get('id')} res={q.get('resolution')} peer={round(sd.get('peer_score') or 0, 1)} "
                  f"baseline={round(sd.get('baseline_score') or 0, 1)} | {(post.get('title') or '')[:60]}")
    print("   projects:", pids, flush=True)
    for pid, _ in pids:
        leaderboard(pid, uid, uname)
else:
    print("minibench posts:", status, str(body)[:150])
