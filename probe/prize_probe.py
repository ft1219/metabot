"""Read-only: prize split by rank, MiniBench prizes, and the question pipeline. Slow on purpose (rate limits)."""
import json, os, time, urllib.error, urllib.request
from collections import Counter

TOKEN = os.environ["METACULUS_TOKEN"]
BASE = "https://www.metaculus.com/api"
DEADLINE = time.time() + 16 * 60


def get(path):
    url = path if path.startswith("http") else BASE + path
    for attempt in range(3):
        if time.time() > DEADLINE:
            return None, "out of time"
        time.sleep(6)
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


def dump_leaderboard(pid, label, uid):
    status, body = get(f"/leaderboards/project/{pid}/")
    if status != 200 or not isinstance(body, list):
        print(f"== {label} leaderboard: HTTP {status} {str(body)[:150]}", flush=True)
        return
    for lb in body:
        ents = lb.get("entries") or []
        print(f"== {label} LB id={lb.get('id')} name={lb.get('name')!r} type={lb.get('score_type')} primary={lb.get('is_primary_leaderboard')} "
              f"pool={lb.get('prize_pool')} start={lb.get('start_time')} end={lb.get('end_time')} finalized={lb.get('finalized')} "
              f"max_coverage={lb.get('max_coverage')} bot_excl={lb.get('bot_exclusion_status')} entries={len(ents)}", flush=True)
        if ents:
            print("   entry keys:", sorted(ents[0].keys()), flush=True)
        for e in ents:
            u = e.get("user") or {}
            name = u.get("username") or e.get("aggregation_method")
            print(f"LB\t{label}\t{lb.get('id')}\t{e.get('rank')}\t{round(e.get('score') or 0, 2)}\t{round(e.get('take') or 0, 1)}\t"
                  f"{e.get('prize')}\t{e.get('contribution_count')}\t{round(e.get('coverage') or 0, 2)}\t{e.get('excluded')}\t"
                  f"{'OURS' if u.get('id') == uid else ''}\t{name}", flush=True)


def project(slug_or_id):
    for path in (f"/projects/tournaments/{slug_or_id}/", f"/projects/{slug_or_id}/"):
        status, body = get(path)
        if status == 200 and isinstance(body, dict):
            keys = sorted(body.keys())
            print(f"== project {path}: keys={keys}", flush=True)
            for k in ("id", "slug", "name", "prize_pool", "start_date", "close_date", "forecasting_end_date", "type", "bot_leaderboard_status", "posts_count", "questions_count"):
                if k in body:
                    print(f"   {k} = {body.get(k)!r}", flush=True)
            desc = body.get("description") or ""
            print("   DESCRIPTION >>>", desc[:6000].replace("\n", " | "), "<<<", flush=True)
            return body
        print(f"== project {path}: HTTP {status} {str(body)[:120]}", flush=True)
    return None


def posts(tournament, statuses):
    out, url = [], f"/posts/?tournaments={tournament}&statuses={statuses}&limit=100&order_by=-open_time"
    while url:
        status, body = get(url)
        if status != 200 or not isinstance(body, dict):
            print(f"   posts {tournament} {statuses}: HTTP {status} {str(body)[:120]}", flush=True)
            break
        out.extend(body.get("results", []))
        url = body.get("next")
    return out


status, me = get("/users/me")
uid = me.get("id") if isinstance(me, dict) else None
print(f"== me id={uid}", flush=True)

# 1) FutureEval: full leaderboard + project text (prize rules).
dump_leaderboard(33121, "FE", uid)
project("fall-futureeval-2026")

# 2) Question pipeline in FutureEval.
first_q_keys_printed = False
for st in ("open", "upcoming", "closed", "resolved"):
    ps = posts(33121, st)
    print(f"== FE {st}: {len(ps)} posts", flush=True)
    weeks = Counter()
    for p in ps:
        q = p.get("question") or {}
        if not first_q_keys_printed and q:
            print("   question keys:", sorted(q.keys()), flush=True)
            print("   post keys:", sorted(p.keys()), flush=True)
            first_q_keys_printed = True
        ot = (q.get("open_time") or p.get("open_time") or "")[:10]
        weeks[ot] += 1
        if st in ("open", "upcoming", "closed"):
            print(f"Q\t{st}\tpost={p.get('id')}\tq={q.get('id')}\ttype={q.get('type')}\topen={q.get('open_time')}\tclose={q.get('scheduled_close_time')}\t"
                  f"cp_reveal={q.get('cp_reveal_time')}\tspot={q.get('spot_scoring_time')}\tresolve={q.get('scheduled_resolve_time')}\t"
                  f"nfc={p.get('nr_forecasters') or q.get('nr_forecasters')}\t{(p.get('title') or '')[:70]}", flush=True)
    print(f"   {st} by open date:", sorted(weeks.items()), flush=True)

# 3) Does a post detail show our own forecast? (one open + one resolved example)
for st in ("open", "resolved"):
    status, body = get(f"/posts/?tournaments=33121&statuses={st}&forecaster_id={uid}&limit=2")
    if status == 200 and body.get("results"):
        pid = body["results"][0]["id"]
        s2, d = get(f"/posts/{pid}/")
        q = (d or {}).get("question") or {}
        mf = q.get("my_forecasts")
        print(f"== detail post {pid} ({st}): my_forecasts keys={sorted(mf.keys()) if isinstance(mf, dict) else mf!r}", flush=True)
        if isinstance(mf, dict):
            print("   latest:", json.dumps(mf.get("latest"))[:400], "| score_data:", json.dumps(mf.get("score_data"))[:600], flush=True)
        agg = (q.get("aggregations") or {})
        print("   aggregations keys:", sorted(agg.keys()) if isinstance(agg, dict) else agg, flush=True)
    else:
        print(f"== forecaster_id filter {st}: HTTP {status} {str(body)[:120]}", flush=True)

# 4) MiniBench: project info + leaderboards.
mb = project("minibench")
if mb and mb.get("id"):
    dump_leaderboard(mb.get("id"), "MB", uid)
