"""Read-only: prize split by rank, MiniBench prizes, and the question pipeline. Slow on purpose (rate limits)."""
import json, os, time, urllib.error, urllib.request
from collections import Counter

TOKEN = os.environ["METACULUS_TOKEN"]
BASE = "https://www.metaculus.com/api"
DEADLINE = time.time() + 20 * 60


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


def posts(tournament, statuses, max_pages=4):
    out = []
    for page in range(max_pages):
        status, body = get(f"/posts/?tournaments={tournament}&statuses={statuses}&limit=100&offset={page*100}&with_cp=true")
        if status != 200 or not isinstance(body, dict):
            print(f"   posts {tournament} {statuses} page {page}: HTTP {status} {str(body)[:120]}", flush=True)
            break
        res = body.get("results") or []
        out.extend(res)
        if len(res) < 100:
            break
    return out


def qs(post):
    if post.get("group_of_questions"):
        return post["group_of_questions"].get("questions") or []
    if post.get("conditional"):
        return [post["conditional"].get("question_yes") or {}]
    return [post["question"]] if post.get("question") else []


def ts(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        import datetime
        return datetime.datetime.utcfromtimestamp(x).strftime("%Y-%m-%dT%H:%M")
    return str(x)[:16]


status, me = get("/users/me")
uid = me.get("id") if isinstance(me, dict) else None
print(f"== me id={uid}", flush=True)

# 1) FutureEval: full leaderboard + project text (prize rules).

# 2) Question pipeline in FutureEval and MiniBench, with our own forecast times and scores.
for tour, label in (("33121", "FE"), ("minibench", "MB")):
    for st in ("open", "closed", "resolved"):
        ps = posts(tour, st)
        weeks, n_q, n_mine = Counter(), 0, 0
        for p in ps:
            for q in qs(p):
                n_q += 1
                mf = q.get("my_forecasts") or {}
                hist = mf.get("history") or []
                first = min((h.get("start_time") for h in hist if h.get("start_time")), default=None)
                last = max((h.get("start_time") for h in hist if h.get("start_time")), default=None)
                sd = mf.get("score_data") or {}
                n_mine += bool(hist)
                weeks[(ts(q.get("open_time")) or "")[:10]] += 1
                print(f"Q\t{label}\t{st}\tpost={p.get('id')}\tq={q.get('id')}\topen={ts(q.get('open_time'))}\tclose={ts(q.get('scheduled_close_time'))}\t"
                      f"cp_reveal={ts(q.get('cp_reveal_time'))}\tspot={ts(q.get('spot_scoring_time'))}\tresolve={ts(q.get('scheduled_resolve_time'))}\t"
                      f"mine_first={ts(first)}\tmine_last={ts(last)}\tn_mine={len(hist)}\tspot_peer={sd.get('spot_peer_score')}\tpeer={sd.get('peer_score')}\t{(p.get('title') or '')[:60]}", flush=True)
        print(f"== {label} {st}: {len(ps)} posts, {n_q} questions, we forecast {n_mine}; by open date: {sorted(weeks.items())}", flush=True)
        if ps and st == "open":
            q0 = qs(ps[0])[0] if qs(ps[0]) else {}
            print("   question keys:", sorted(q0.keys()), flush=True)

# 4) MiniBench: project info + leaderboards.
mb = project("minibench")
if mb and mb.get("id"):
    dump_leaderboard(mb.get("id"), "MB", uid)
