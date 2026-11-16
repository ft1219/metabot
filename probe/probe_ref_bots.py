"""Read-only probe: can our ordinary bot token read other forecasters' per-question scores
or forecasts on closed/resolved FutureEval and MiniBench questions?

Run in GitHub Actions with env METACULUS_TOKEN (never printed). Optional env:
FE_PROJECT (default 33121), MB_PROJECT (default 33135, a past MiniBench round).

Only GET requests. 6 s between calls, 60 s back-off on 429, 20-minute deadline.
Only resolved questions are printed row by row; open/unscored questions are only counted.

Endpoints tried (from github.com/Metaculus/metaculus):
  /api/users/me/                                    our id
  /api/leaderboards/project/{pid}/                  all entries (user, score, rank, exclusion_status...)
  /api/users/by-username/{name}/                    fallback id lookup (AllowAny)
  /api/medals/contributions/?for_user=&project=     per-question score of ANY user (AllowAny, project view perm)
  /api/medals/contributions/?...&score_type=...     other leaderboard types, 404 if the project has none
  /api/medals/contributions/?score_type=baseline_global&start_time=&end_time=  (no project = site main)
                                                    time-averaged BASELINE + coverage, if FE/MB are in the main feed
  /api/users/{id}/?include_stats=true               score_scatter_plot: per-post PEER (time-averaged) score
  /api/comments/?author={id}&post={resolved post}   public comments on one fully resolved post only
  /api/posts/?tournaments={pid}&statuses=resolved   questions, CP score_data, forecaster_count, our score_data
"""
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

TOKEN = os.environ["METACULUS_TOKEN"]
BASE = "https://www.metaculus.com/api"
DEADLINE = time.time() + 20 * 60
FE_PROJECT = int(os.environ.get("FE_PROJECT", "33121"))
MB_PROJECT = int(os.environ.get("MB_PROJECT", "33135"))
BOTS = {
    "sonnet": "metac-claude-sonnet-5-5-high+asknews",
    "astra": "metac-gpt-6-astra-high+asknews",
    "astra_agent": "metac-agent-gpt-6-astra",  # optional extra
}
CONTINUOUS = ("numeric", "date", "discrete")


def fetch(path, raw=False):
    """Returns (status, body). body is parsed JSON, raw bytes (raw=True), or a short error string."""
    url = path if path.startswith("http") else BASE + path
    for _ in range(3):
        if time.time() > DEADLINE:
            return None, "out of time"
        time.sleep(6)
        req = urllib.request.Request(url, headers={"Accept": "*/*" if raw else "application/json"})
        # Unredirected: urllib copies ordinary headers onto redirect targets, even on another host,
        # which would hand the token to whatever host a redirect points at.
        req.add_unredirected_header("Authorization", f"Token {TOKEN}")
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
                if raw:
                    return r.status, data
                return r.status, json.loads(data or b"null")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"   (429 on {path}, waiting 60 s)", flush=True)
                time.sleep(60)
                continue
            return e.code, e.read()[:200].decode(errors="replace")
        except Exception as e:  # noqa: BLE001
            return None, repr(e)[:200]
    return 429, "still rate limited"


def short(x, n=160):
    s = json.dumps(x, default=str) if not isinstance(x, str) else x
    return s if len(s) <= n else s[:n] + "..."


def ts(x):
    if x is None:
        return ""
    if isinstance(x, (int, float)):
        return time.strftime("%Y-%m-%dT%H:%M", time.gmtime(x))
    return str(x)[:16]


def shape(label, status, body):
    if isinstance(body, dict):
        print(f"   {label}: HTTP {status} dict keys={sorted(body.keys())}", flush=True)
    elif isinstance(body, list):
        print(f"   {label}: HTTP {status} list len={len(body)}", flush=True)
    else:
        print(f"   {label}: HTTP {status} {short(body, 200)}", flush=True)


# ---------------------------------------------------------------- score math (from scoring/score_math.py)
def k_of(qtype):
    # spot peer / spot baseline: continuous scores are divided by 2
    return 50.0 if qtype in CONTINUOUS else 100.0


def c_of(qtype, n):
    # spot peer = k * N/(N-1) * ln(p / GM), N = forecasters in the geometric mean at spot time
    k = k_of(qtype)
    return k * n / (n - 1) if n and n > 1 else k


def log_mean_exp2(x):
    """ln((1 + e^x) / 2), numerically stable."""
    return max(x, 0.0) + math.log1p(math.exp(-abs(x))) - math.log(2.0)


def ensemble_delta(s_a, s_b, qtype, n):
    """Spot-peer gain of the 50/50 linear pool (mean == median for two) over bot A.
    ln(pB/pA) = (S_B - S_A)/c.  Returns (delta if E replaces A inside the GM, delta if GM unchanged)."""
    c = c_of(qtype, n)
    lme = log_mean_exp2((s_b - s_a) / c)
    return k_of(qtype) * lme, c * lme


def c_hat(qtype, my_sd, cp_sd, n_options=None):
    """Empirical c from two forecasts scored against the same GM (ours and the CP):
    c = (S_ours - S_cp) / (ln p_ours - ln p_cp), and ln p_ours - ln p_cp follows from the spot baseline
    scores (binary: dB*ln2/100, MC: dB*lnK/100, continuous: dB/50; the continuous bucket baseline cancels).
    Returns (c_hat, N_hat) or (None, None). Checks the N/(N-1) factor and N without forecaster_count."""
    keys = ("spot_peer_score", "spot_baseline_score")
    if any(my_sd.get(k) is None or cp_sd.get(k) is None for k in keys):
        return None, None
    d_b = my_sd["spot_baseline_score"] - cp_sd["spot_baseline_score"]
    d_s = my_sd["spot_peer_score"] - cp_sd["spot_peer_score"]
    if qtype == "binary":
        d_lnp = d_b * math.log(2.0) / 100.0
    elif qtype == "multiple_choice" and n_options and n_options > 1:
        d_lnp = d_b * math.log(n_options) / 100.0
    elif qtype in CONTINUOUS:
        d_lnp = d_b / 50.0
    else:
        return None, None
    if abs(d_lnp) < 0.01:  # forecasts too close to the CP: ratio is noise
        return None, None
    c = d_s / d_lnp
    k = k_of(qtype)
    return c, (c / (c - k) if c > k * 1.0001 else None)


def p_from_spot_baseline(b, qtype, n_options=2):
    if b is None:
        return None
    if qtype == "binary":
        return 2.0 ** (b / 100.0 - 1.0)
    if qtype == "multiple_choice" and n_options and n_options > 1:
        return n_options ** (b / 100.0) / n_options
    return None


# ---------------------------------------------------------------- 1) who am I
status, me = fetch("/users/me/")
uid = me.get("id") if isinstance(me, dict) else None
print(f"== me: HTTP {status} id={uid} is_bot={me.get('is_bot') if isinstance(me, dict) else None}", flush=True)
ids = {"ours": uid}


# ---------------------------------------------------------------- 2) project leaderboards
def leaderboards(pid, label):
    status, body = fetch(f"/leaderboards/project/{pid}/")
    if status != 200 or not isinstance(body, list):
        shape(f"{label} leaderboards", status, body)
        return []
    for lb in body:
        ents = lb.get("entries") or []
        print(f"== {label} LB id={lb.get('id')} name={lb.get('name')!r} score_type={lb.get('score_type')} "
              f"primary={lb.get('is_primary_leaderboard')} finalized={lb.get('finalized')} "
              f"max_coverage={lb.get('max_coverage')} bot_excl={lb.get('bot_exclusion_status')} entries={len(ents)}", flush=True)
        if ents:
            print("   entry keys:", sorted(ents[0].keys()), flush=True)
        for e in ents:
            u = e.get("user") or {}
            name = (u.get("username") or "").lower()
            for key, want in BOTS.items():
                if name == want.lower() and key not in ids:
                    ids[key] = u.get("id")
            if name.startswith("metac-") or u.get("id") == uid:
                print(f"   LBROW\t{label}\t{lb.get('id')}\trank={e.get('rank')}\tscore={e.get('score')}\t"
                      f"n={e.get('contribution_count')}\tcov={e.get('coverage')}\texcl_status={e.get('exclusion_status')}\t"
                      f"uid={u.get('id')}\t{'OURS' if u.get('id') == uid else u.get('username')}", flush=True)
    return body


fe_lbs = leaderboards(FE_PROJECT, "FE")
mb_lbs = leaderboards(MB_PROJECT, "MB")

for key, name in BOTS.items():
    if key not in ids:
        status, body = fetch("/users/by-username/" + urllib.parse.quote(name, safe="") + "/")
        if status == 200 and isinstance(body, dict):
            ids[key] = body.get("id")
        else:
            shape(f"by-username {name}", status, body)
print(f"== resolved ids: {ids}", flush=True)


# ---------------------------------------------------------------- 3) per-question contributions (candidate (a))
def contributions(pid, label, who, extra=""):
    u = ids.get(who)
    if not u:
        print(f"   {label} contributions {who}: no user id", flush=True)
        return None
    path = f"/medals/contributions/?for_user={u}" + (f"&project={pid}" if pid else "") + extra  # no project = site main
    status, body = fetch(path)
    shape(f"{label} contributions {who}{extra}", status, body)
    if status != 200 or not isinstance(body, dict):
        return None
    lb = body.get("leaderboard") or {}
    le = body.get("leaderboard_entry") or {}
    rows = body.get("contributions") or []
    scored = [r for r in rows if r.get("score") is not None]
    print(f"   leaderboard id={lb.get('id')} name={lb.get('name')!r} score_type={lb.get('score_type')} | "
          f"entry score={le.get('score')} n={le.get('contribution_count')} cov={le.get('coverage')} | "
          f"contributions={len(rows)} scored={len(scored)} types={dict(Counter(r.get('question_type') for r in scored))}", flush=True)
    if rows:
        print("   contribution keys:", sorted(rows[0].keys()), flush=True)
    for r in scored[:3]:
        print("   sample:", short({k: r.get(k) for k in ("question_id", "post_id", "question_type", "question_resolution",
                                                       "question_weight", "score", "coverage")}, 300), flush=True)
    return {r.get("question_id"): r for r in scored if r.get("question_id") is not None}


contrib = {}
for pid, label in ((FE_PROJECT, "FE"), (MB_PROJECT, "MB")):
    for who in list(BOTS) + ["ours"]:
        contrib[(label, who)] = contributions(pid, label, who) or {}

# Other score types exist only if the project has such a leaderboard (else 404).
alt = {}
for st in ("spot_baseline_tournament", "peer_tournament"):
    res = contributions(FE_PROJECT, "FE", "sonnet", f"&score_type={st}")
    if res:
        alt[("FE", "sonnet", st)] = res
        for who in ("astra", "ours"):
            alt[("FE", who, st)] = contributions(FE_PROJECT, "FE", who, f"&score_type={st}") or {}


# ---------------------------------------------------------------- 4) profile stats (score_scatter_plot = PEER score per post)
scatter = {}
for who in ("sonnet", "astra"):
    if not ids.get(who):
        continue
    status, body = fetch(f"/users/{ids[who]}/?include_stats=true")
    shape(f"profile {who}", status, body)
    if status == 200 and isinstance(body, dict):
        sp = body.get("score_scatter_plot") or []
        print(f"   score_scatter_plot len={len(sp)} keys={sorted(sp[0].keys()) if sp else None}", flush=True)
        for r in sp[-3:]:
            print("   sample:", short({k: r.get(k) for k in ("post_id", "score", "score_timestamp", "question_resolution")}), flush=True)
        scatter[who] = {r.get("post_id"): r.get("score") for r in sp}


# ---------------------------------------------------------------- 5) resolved questions with CP and our own score data
def qs(post):
    if post.get("group_of_questions"):
        return post["group_of_questions"].get("questions") or []
    if post.get("conditional"):
        c = post["conditional"]
        return [q for q in (c.get("question_yes"), c.get("question_no")) if q]
    return [post["question"]] if post.get("question") else []


# Posts whose every question is resolved. statuses=resolved matches a post if ANY of its questions is
# resolved, so a group post can still have open sub-questions; those are dropped and never looked at.
RESOLVED_POSTS = set()


def resolved_questions(pid, label, max_pages=5):
    out = {}
    dropped = 0
    for page in range(max_pages):
        status, body = fetch(f"/posts/?tournaments={pid}&statuses=resolved&limit=100&offset={page * 100}&with_cp=true")
        if status != 200 or not isinstance(body, dict):
            shape(f"{label} posts page {page}", status, body)
            break
        res = body.get("results") or []
        for p in res:
            pq = qs(p)
            if pq and all(q.get("resolution") is not None for q in pq):
                RESOLVED_POSTS.add(p.get("id"))
            for q in pq:
                if q.get("id") is None:
                    continue
                if q.get("resolution") is None:
                    dropped += 1
                    continue
                q["_post_id"] = p.get("id")
                out[q["id"]] = q
        if len(res) < 100:  # MAX_LIMIT is 100; list endpoints link a next page forever
            break
    if dropped:
        print(f"   {label}: skipped {dropped} unresolved sub-questions on partly resolved posts", flush=True)
    print(f"== {label}: {len(out)} resolved questions in posts list", flush=True)
    if out:
        q0 = next(iter(out.values()))
        print("   question keys:", sorted(q0.keys()), flush=True)
        agg = (q0.get("aggregations") or {}).get(q0.get("default_aggregation_method") or "recency_weighted") or {}
        print("   aggregation keys:", sorted(agg.keys()), "score_data:", short(agg.get("score_data"), 300), flush=True)
        print("   my score_data:", short(((q0.get("my_forecasts") or {}).get("score_data")), 300), flush=True)
    return out


questions = {"FE": resolved_questions(FE_PROJECT, "FE"), "MB": resolved_questions(MB_PROJECT, "MB")}


# ---------------------------------------------------------------- 5b) 2026 global BASELINE leaderboard (untested route)
# Global leaderboards live on the site-main project and take approved public questions of projects with
# NORMAL visibility (scoring/models.py get_questions + posts filter_for_main_feed). If FutureEval/MiniBench
# are in the main feed, this gives other users' time-averaged BASELINE score AND coverage per question;
# for a single forecast s = score/coverage, so p(outcome) is exact without the CP anchor. 404 / no
# overlap means the route is closed. Global contributions list scored questions only.
glob = {}
fe_mb_qids = set(questions["FE"]) | set(questions["MB"])
for who in ("sonnet", "astra"):
    res_g = contributions(None, "GLOBAL-2026", who, "&score_type=baseline_global"
                          "&start_time=2026-01-01T00:00:00Z&end_time=2027-01-01T00:00:00Z")
    if res_g is not None:
        glob[who] = {qid: r for qid, r in res_g.items() if qid in fe_mb_qids}
        print(f"   GLOBAL-2026 {who}: {len(glob[who])} of its scored questions are resolved FE/MB questions", flush=True)


def p_yes_global(r, qtype, res):
    """Binary p_yes from a time-averaged BASELINE score, exact only if the bot made one forecast."""
    if not r or qtype != "binary" or res not in ("yes", "no"):
        return None
    sc, cov = r.get("score"), r.get("coverage")
    if sc is None or not cov:
        return None
    p_out = 2.0 ** ((sc / cov) / 100.0 - 1.0)
    return p_out if res == "yes" else 1 - p_out


# ---------------------------------------------------------------- 6) public comments with included_forecast (candidate (b))
for who in ("sonnet", "astra"):
    if not ids.get(who):
        continue
    # The newest 10 comments are likely on recent posts; also ask directly about one resolved FE post this bot scored on.
    sample_post = next((r.get("post_id") for r in (contrib.get(("FE", who)) or {}).values()
                        if r.get("post_id") in RESOLVED_POSTS), None)
    if sample_post:
        status, body = fetch(f"/comments/?author={ids[who]}&post={sample_post}&limit=5")
        res = (body.get("results") or []) if status == 200 and isinstance(body, dict) else []
        print(f"   comments {who} on resolved post {sample_post}: HTTP {status} n={len(res)} "
              f"with_included_forecast={sum(1 for c in res if c.get('included_forecast'))} "
              f"included_forecast keys={sorted((res[0].get('included_forecast') or {}).keys()) if res else None}", flush=True)


# ---------------------------------------------------------------- 8) join: one TSV line per resolved question
def agg_info(q):
    method = q.get("default_aggregation_method") or "recency_weighted"
    agg = (q.get("aggregations") or {}).get(method) or {}
    latest = agg.get("latest") or {}
    return method, agg.get("score_data") or {}, latest.get("forecaster_count"), latest.get("forecast_values")


print("\nTSV\tproj\tpost\tqid\ttype\tclose\tspot\tresolution\tweight\tN\tbots_in_agg\tdefault_score\t"
      "N_hat\tc_hat\tS_sonnet\tS_astra\tS_astra_agent\tS_ours\tours_spot_peer\tours_spot_base\tcp_spot_peer\tcp_spot_base\t"
      "dE_replace\tdE_fixedGM\tp_sonnet_yes\tp_astra_yes\tdLogOdds_replace\tpeer_sonnet_profile\tpeer_astra_profile\t"
      "p_sonnet_yes_global\tp_astra_yes_global", flush=True)
for label in ("FE", "MB"):
    cs, ca = contrib.get((label, "sonnet")) or {}, contrib.get((label, "astra")) or {}
    cg, co = contrib.get((label, "astra_agent")) or {}, contrib.get((label, "ours")) or {}
    qmap = questions.get(label) or {}
    tot = Counter()
    n_match = Counter()
    for qid in sorted(set(cs) | set(ca) | set(co)):
        rs, ra = cs.get(qid), ca.get(qid)
        base = rs or ra or co.get(qid) or {}
        q = qmap.get(qid) or {}
        qtype = base.get("question_type") or q.get("type")
        res = base.get("question_resolution") or q.get("resolution")
        # explicit None checks: a question_weight of 0.0 is legitimate and must not become 1.0
        w = next((v for v in (base.get("question_weight"), q.get("question_weight")) if v is not None), 1.0)
        method, cp_sd, n, cp_vals = agg_info(q)
        my_sd = (q.get("my_forecasts") or {}).get("score_data") or {}
        s_s = rs.get("score") if rs else None
        s_a = ra.get("score") if ra else None
        s_o = (co.get(qid) or {}).get("score")
        for key in ("spot_peer_score", "peer_score", "spot_baseline_score", "baseline_score"):
            if s_o is not None and my_sd.get(key) is not None and abs(my_sd[key] - s_o) < 1e-6:
                n_match[key] += 1
        c_emp, n_emp = c_hat(qtype, my_sd, cp_sd, len(q.get("options") or []) or None)
        if n_emp is not None and n:
            tot["n_Nhat"] += 1
            tot["sum_Nhat_over_N"] += n_emp / n
        d_rep = d_fix = p_s_yes = p_a_yes = d_lo = None
        if s_s is not None and s_a is not None and qtype:
            d_rep, d_fix = ensemble_delta(s_s, s_a, qtype, n)
            tot["n_both"] += 1
            tot["sum_sonnet"] += w * s_s
            tot["sum_astra"] += w * s_a
            tot["sum_ens_replace"] += w * (s_s + d_rep)
            tot["sum_ens_fixed"] += w * (s_s + d_fix)
            tot["ens_beats_sonnet"] += d_rep > 0
            tot[f"n_{qtype}"] += 1
            # Binary: absolute probabilities from the CP anchor (CP spot baseline gives p_cp, CP spot peer gives ln GM).
            if qtype == "binary" and res in ("yes", "no"):
                c = c_of(qtype, n)
                p_cp = p_from_spot_baseline(cp_sd.get("spot_baseline_score"), qtype)
                anchor = None
                if p_cp and cp_sd.get("spot_peer_score") is not None:
                    anchor = math.log(p_cp) - cp_sd["spot_peer_score"] / c
                elif my_sd.get("spot_baseline_score") is not None and my_sd.get("spot_peer_score") is not None:
                    p_o = p_from_spot_baseline(my_sd["spot_baseline_score"], qtype)
                    anchor = math.log(p_o) - my_sd["spot_peer_score"] / c
                if anchor is not None:
                    pr_s = min(max(math.exp(anchor + s_s / c), 1e-9), 1 - 1e-9)
                    pr_a = min(max(math.exp(anchor + s_a / c), 1e-9), 1 - 1e-9)
                    p_s_yes = pr_s if res == "yes" else 1 - pr_s
                    p_a_yes = pr_a if res == "yes" else 1 - pr_a
                    lo = (math.log(p_s_yes / (1 - p_s_yes)) + math.log(p_a_yes / (1 - p_a_yes))) / 2
                    p_lo_yes = 1 / (1 + math.exp(-lo))
                    pr_lo = p_lo_yes if res == "yes" else 1 - p_lo_yes
                    d_lo = k_of(qtype) * math.log(pr_lo / pr_s)
                    tot["n_binary_logodds"] += 1
                    tot["sum_sonnet_binary"] += w * s_s
                    tot["sum_logodds_binary"] += w * (s_s + d_lo)
                    tot["sum_mean_binary"] += w * (s_s + d_rep)
        post_id = base.get("post_id") or q.get("_post_id")
        cells = [label, post_id, qid, qtype, ts(q.get("scheduled_close_time")), ts(q.get("spot_scoring_time") or q.get("cp_reveal_time")),
                 res, w, n, q.get("include_bots_in_aggregates"), q.get("default_score_type"), n_emp, c_emp,
                 s_s, s_a, (cg.get(qid) or {}).get("score"), s_o, my_sd.get("spot_peer_score"), my_sd.get("spot_baseline_score"),
                 cp_sd.get("spot_peer_score"), cp_sd.get("spot_baseline_score"),
                 d_rep, d_fix, p_s_yes, p_a_yes, d_lo,
                 (scatter.get("sonnet") or {}).get(post_id), (scatter.get("astra") or {}).get(post_id),
                 p_yes_global((glob.get("sonnet") or {}).get(qid), qtype, res),
                 p_yes_global((glob.get("astra") or {}).get(qid), qtype, res)]
        print("TSV\t" + "\t".join("" if v is None else (f"{v:.4f}" if isinstance(v, float) else str(v)) for v in cells), flush=True)
    print(f"== {label} summary (question_weight applied): {dict((k, round(v, 2)) for k, v in tot.items())}", flush=True)
    print(f"== {label} our contribution score equals my_forecasts score_data[...] on: {dict(n_match)} "
          f"(of {sum(1 for v in co.values() if v.get('score') is not None)} scored)", flush=True)

print("== done", flush=True)
