import io
import json
import random
import urllib.error

import pytest

import ai_check
import lab
import report
import strategies as S

from .test_lab import NOW, gamma, serial

LATE = NOW - NOW % 86400 + 20 * 3600  # late in the UTC day: most of the day's money is free
# a market that rose 15c in a day: outcome 0 ("Yes") went up, Yes costs 60c, No costs 41c
MOVED = dict(bid=0.59, ask=0.60, oneDayPriceChange=0.15)


def view(**kw):
    args = dict(MOVED)
    args.update(kw)
    return lab.market_view(gamma(**args), NOW)


def answer(chance=0.7, searches=2, tin=12_000, tout=1_500, text=None, status="completed", url=None):
    out = [{"type": "reasoning"}]
    out += [{"type": "web_search_call", "action": {"type": "search", "query": f"q{i}"}} for i in range(searches)]
    msg = text if text is not None else f'The news says so.\n{{"chance": {chance}, "why": "because"}}'
    out.append({"type": "message", "content": [{"type": "output_text", "text": msg,
                                                "annotations": [{"type": "url_citation", "url": url}] if url else []}]})
    return {"status": status, "output": out, "usage": {"input_tokens": tin, "output_tokens": tout}}


@pytest.fixture
def openai(monkeypatch):
    """A fake OpenAI: records the requests and answers with whatever `replies` holds (a dict, or an exception)."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("PM_AI_CHECK", raising=False)
    calls = {"requests": [], "replies": []}

    def fake(request, timeout=ai_check.TIMEOUT_SECONDS):
        calls["requests"].append(request)
        reply = calls["replies"].pop(0) if calls["replies"] else answer()
        if isinstance(reply, Exception):
            raise reply
        return reply

    monkeypatch.setattr(ai_check, "ask_openai", fake)
    serial(monkeypatch)
    return calls


# ---------------------------------------------------------------- rules

def test_follow_and_fade_ai_buy_only_with_a_margin_over_the_price():
    v = view()
    assert S.ai_candidate(v)
    assert S.follow_move_ai(v, 0.70) == (0, 0.65)  # AI 70% for the side that rose, priced 60c: buy, pay at most 65c
    assert S.fade_move_ai(v, 0.70) is None
    assert S.follow_move_ai(v, 0.64) is None  # 4c over the price: not enough
    assert S.follow_move_ai(v, 0.65) == (0, 0.6)
    assert S.fade_move_ai(v, 0.30) == (1, 0.65)  # AI 70% for No, priced 41c
    assert S.follow_move_ai(v, 0.30) is None
    for c in (0.01, 0.2, 0.5, 0.65, 0.8, 0.99):  # never both
        assert not (S.follow_move_ai(v, c) and S.fade_move_ai(v, c))
    assert S.follow_move_ai(v, 0.99) == (0, 0.85)  # never above follow_move's 85c


def test_ai_rules_follow_the_direction_and_price_window_of_the_jump():
    down = view(oneDayPriceChange=-0.15)  # Yes fell: No is the side that rose
    assert S.follow_move_ai(down, 0.20) == (1, 0.75)
    assert S.fade_move_ai(down, 0.80) == (0, 0.75)
    dear = view(bid=0.89, ask=0.90)  # rising side at 90c: outside 10-85c, but No at 11c is in
    assert S.follow_move_ai(dear, 0.99) is None
    assert S.ai_candidate(dear) and S.fade_move_ai(dear, 0.02) == (1, 0.85)
    assert not S.ai_candidate(view(oneDayPriceChange=0.05))  # no real move
    assert not S.ai_candidate(view(sportsMarketType="moneyline"))
    assert not S.ai_candidate(view(volume24hr=0))
    assert not S.ai_candidate(view(bid=0.50, ask=0.60))  # gap too wide to trust the quote


def test_ai_strategies_start_on_their_own_date_and_are_judged_like_bets():
    for name in ("follow_move_ai", "fade_move_ai"):
        cfg = S.STRATEGIES[name]
        assert cfg["active"] and cfg["rule"] is None and cfg["since"] == "2026-11-18"
        assert cfg.get("judge", "bet") == "bet"


# ---------------------------------------------------------------- answer, prompt, cost

def test_parse_chance_takes_the_last_json_line():
    assert ai_check.parse_chance('{"chance": 0.2}\nthen\n{"chance": 0.64, "why": "x"}') == (0.64, "x")
    assert ai_check.parse_chance('{"chance": 64, "why": "pct"}') == (0.64, "pct")
    assert ai_check.parse_chance('{"chance": 1.0}') == (0.99, "")
    assert ai_check.parse_chance('{"chance": 0}') == (0.01, "")
    assert ai_check.parse_chance("I think about 60%.")[0] is None
    assert ai_check.parse_chance('{"chance": "high"}')[0] is None
    assert ai_check.parse_chance('{"chance": 250}')[0] is None


def test_prompt_never_shows_the_price_and_request_keeps_nothing():
    v = view(question="Will X happen by Friday?")
    events = {v["event_id"]: {"markets": [{"conditionId": v["conditionId"], "description": "Resolves Yes if X.",
                                           "resolutionSource": "https://example.org"}]}}
    prompt = ai_check.prompt_for(v, ai_check.rules_of(v, events), NOW)
    assert "Will X happen by Friday?" in prompt and "Resolves Yes if X." in prompt and "example.org" in prompt
    for price in ("0.59", "0.6", "60", "0.41", "41", "0.15", "15c"):
        assert price not in prompt.replace(ai_check._stamp(NOW), "").replace(ai_check._stamp(v["ends_at"]), "")
    req = ai_check.request_for(prompt)
    assert req["store"] is False and "timeout" not in req and req["tools"][0]["type"] == "web_search"
    assert req["max_tool_calls"] == ai_check.MAX_TOOL_CALLS and req["max_output_tokens"] == ai_check.MAX_OUTPUT_TOKENS


def test_most_a_check_can_cost_bounds_a_normal_answer():
    most = ai_check.most_a_check_can_cost("x" * 4000)
    assert 0.15 < most < 0.20
    big = answer(searches=ai_check.MAX_TOOL_CALLS, tin=25_000, tout=ai_check.MAX_OUTPUT_TOKENS)
    real = ai_check.token_cost(25_000, ai_check.MAX_OUTPUT_TOKENS) + ai_check.tool_calls(big) * ai_check.USD_PER_SEARCH
    assert real < most


def test_daily_money_is_let_out_evenly():
    midnight = NOW - NOW % 86400
    assert ai_check.allowance(midnight) == pytest.approx(0.20)
    assert ai_check.allowance(midnight + 43200) == pytest.approx(0.70)
    assert ai_check.allowance(midnight + 86399) == pytest.approx(1.00)
    st = {"ai_budget": {"day": "2000-01-01", "spent": 0.9, "checks": 9}}
    assert ai_check.budget(st, NOW) == {"day": ai_check._day(NOW), "spent": 0.0, "checks": 0}


# ---------------------------------------------------------------- run_checks

def _state():
    return {"positions": [], "traded_events": {}, "verdicts": {}}


def test_run_checks_buys_where_the_ai_beats_the_price_and_records_every_check(openai):
    vs = [view(cid=f"0x{i}") for i in range(5)]
    openai["replies"] = [answer(0.70), answer(0.61), answer(0.30)]
    st, problems = _state(), []
    picks, rows = ai_check.run_checks(vs, {}, st, LATE, random.Random(1), problems)
    assert len(rows) == ai_check.MAX_CHECKS_PER_RUN == 3 and not problems
    assert [r["decision"] for r in rows] == ["follow_move_ai", None, "fade_move_ai"]
    (v, i, cap, note), = picks["follow_move_ai"]
    assert (i, cap) == (0, 0.65) and note["ai_chance0"] == 0.70 and v["conditionId"] == rows[0]["condition_id"]
    assert picks["fade_move_ai"][0][1:3] == (1, 0.65)
    cost = ai_check.token_cost(12_000, 1_500) + 2 * ai_check.USD_PER_SEARCH
    assert rows[0]["cost"] == pytest.approx(cost, abs=1e-4) and rows[0]["searches"] == 2
    assert st["ai_budget"]["spent"] == pytest.approx(3 * cost, abs=1e-3) and st["ai_budget"]["checks"] == 3
    assert len(st["ai_watch"]) == 3 and len(st["ai_checked"]) == 3
    assert rows[0]["ask0"] == 0.6 and rows[0]["ask1"] == pytest.approx(0.41) and rows[0]["move"] == 0.15
    # the next run checks only markets not checked before
    openai["replies"] = []
    _, rows2 = ai_check.run_checks(vs, {}, st, LATE + 3600, random.Random(2), [])
    assert rows2 and {r["condition_id"] for r in rows2}.isdisjoint({r["condition_id"] for r in rows})


def test_run_checks_stays_inside_the_day_budget(openai):
    vs = [view(cid=f"0x{i}") for i in range(5)]
    midnight = NOW - NOW % 86400
    st = _state()
    _, rows = ai_check.run_checks(vs, {}, st, midnight + 60, random.Random(1), [])
    assert len(rows) == 1  # just after midnight only BURST_USD is free: room for one check
    st["ai_budget"]["spent"] = 0.95
    _, rows = ai_check.run_checks(vs, {}, st, midnight + 86000, random.Random(1), [])
    assert rows == [] and len(openai["requests"]) == 1


def test_one_check_per_event_and_none_on_events_already_held(openai):
    a, b = view(cid="0xa"), view(cid="0xb")
    b["event_id"] = a["event_id"]
    c = view(cid="0xc")
    st = _state()
    st["traded_events"]["fade_move_ai"] = {c["event_id"]: NOW + 1e6}
    _, rows = ai_check.run_checks([a, b, c], {}, st, NOW, random.Random(1), [])
    assert len(rows) == 1 and rows[0]["event_id"] == a["event_id"]


def test_no_key_is_a_problem_only_when_there_is_something_to_check(openai, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    problems = []
    assert ai_check.run_checks([view(oneDayPriceChange=0.01)], {}, _state(), NOW, random.Random(1), problems)[1] == []
    assert problems == []
    st = _state()
    picks, rows = ai_check.run_checks([view()], {}, st, NOW, random.Random(1), problems)
    assert rows == [] and not any(picks.values()) and "no OPENAI_API_KEY" in problems[0]
    assert not st.get("ai_checked") and openai["requests"] == []


def test_switched_off_makes_no_checks(openai, monkeypatch):
    monkeypatch.setenv("PM_AI_CHECK", "off")
    assert ai_check.run_checks([view()], {}, _state(), NOW, random.Random(1), []) == (
        {"follow_move_ai": [], "fade_move_ai": []}, [])
    assert openai["requests"] == []


def test_used_up_credit_stops_quietly_and_costs_nothing(openai):
    openai["replies"] = [ai_check.Stop("OpenAI credit used up (insufficient_quota)")] * 3
    st, problems = _state(), []
    picks, rows = ai_check.run_checks([view(cid=f"0x{i}") for i in range(3)], {}, st, LATE, random.Random(1), problems)
    assert rows == [] and not any(picks.values())
    assert problems == ["AI check: OpenAI credit used up (insufficient_quota)"]
    assert st["ai_budget"]["spent"] == 0 and not st["ai_checked"]


def test_cut_off_call_counts_the_most_it_could_cost_and_buys_nothing(openai):
    openai["replies"] = [ai_check.CutOff("TimeoutError"), answer(text="no idea"), answer(0.9, status="incomplete")]
    st, problems = _state(), []
    picks, rows = ai_check.run_checks([view(cid=f"0x{i}") for i in range(3)], {}, st, LATE, random.Random(1), problems)
    assert not any(picks.values()) and len(rows) == 3 and all(r["decision"] is None for r in rows)
    assert rows[0]["error"].startswith("cut off") and rows[0]["cost"] > 0.15
    assert rows[1]["error"] == "no chance in the answer" and rows[2]["error"].startswith("answer")
    assert "3 of 3 check(s) failed" in problems[0]
    assert not st.get("ai_watch") and len(st["ai_checked"]) == 3


def test_polymarket_peeks_are_recorded(openai):
    openai["replies"] = [answer(0.7, url="https://polymarket.com/event/x")]
    _, rows = ai_check.run_checks([view()], {}, _state(), NOW, random.Random(1), [])
    assert rows[0]["saw_polymarket"] is True


# ---------------------------------------------------------------- the OpenAI call itself

class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _http_error(code, body):
    return urllib.error.HTTPError(ai_check.API_URL, code, "err", {}, io.BytesIO(json.dumps(body).encode()))


def test_ask_openai_sorts_out_what_openai_says(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-123")
    monkeypatch.setattr(ai_check.time, "sleep", lambda s: None)
    sent = []

    def urlopen_with(*outcomes):
        seq = list(outcomes)

        def urlopen(req, timeout):
            sent.append(req)
            o = seq.pop(0)
            if isinstance(o, BaseException):
                raise o
            return _Resp(json.dumps(o).encode())
        monkeypatch.setattr(ai_check.urllib.request, "urlopen", urlopen)

    urlopen_with({"status": "completed", "output": []})
    assert ai_check.ask_openai({"model": "m"})["status"] == "completed"
    assert sent[-1].get_header("Authorization") == "Bearer sk-secret-123"
    quota = {"error": {"code": "insufficient_quota", "message": "You exceeded... sk-secret-123"}}
    for outcome, kind, text in [
        ((_http_error(429, quota),), ai_check.Stop, "credit used up"),
        ((_http_error(401, {"error": {"message": "Incorrect API key sk-secret-123"}}),), ai_check.Stop, "HTTP 401"),
        ((_http_error(500, {}), _http_error(503, {})), RuntimeError, "HTTP 503"),
        ((TimeoutError("slow"),), ai_check.CutOff, "TimeoutError"),
    ]:
        urlopen_with(*outcome)
        with pytest.raises(kind) as e:
            ai_check.ask_openai({"model": "m"})
        assert text in str(e.value) and "sk-secret" not in str(e.value)
    urlopen_with(_http_error(429, {"error": {"code": "rate_limit_exceeded"}}), {"status": "completed"})
    assert ai_check.ask_openai({"model": "m"})["status"] == "completed"  # busy once, then answered


# ---------------------------------------------------------------- results and the report

def test_settle_checks_records_results_of_ended_markets_only():
    st = {"ai_watch": [
        {"condition_id": "0xdone", "ends_at": NOW - 10, "chance0": 0.7, "bid0": 0.59, "ask0": 0.6},
        {"condition_id": "0xopen", "ends_at": NOW + 3600, "chance0": 0.4, "bid0": 0.3, "ask0": 0.31},
        {"condition_id": "0xlost", "ends_at": NOW - 31 * 86400, "chance0": 0.5, "bid0": 0.5, "ask0": 0.51},
    ]}
    asked = []

    def closed(ids):
        asked.append(set(ids))
        return {"0xdone": {"closed": True, "outcomePrices": '["1", "0"]'}}

    done = ai_check.settle_checks(st, NOW, closed, lab.final_prices)
    assert asked == [{"0xdone", "0xlost"}]
    assert {d["condition_id"]: d["result0"] for d in done} == {"0xdone": 1.0, "0xlost": None}
    assert [w["condition_id"] for w in st["ai_watch"]] == ["0xopen"]


def test_ai_summary_compares_ai_and_market_errors(tmp_path):
    rows = [{"chance0": 0.8, "bid0": 0.59, "ask0": 0.61, "result0": 1.0, "settled_at": NOW},
            {"chance0": 0.3, "bid0": 0.49, "ask0": 0.51, "result0": 0.0, "settled_at": NOW},
            {"chance0": 0.3, "bid0": 0.49, "ask0": 0.51, "result0": None, "settled_at": NOW}]
    lab.append_jsonl(tmp_path / "ai_results" / "2026-11.jsonl", rows)
    lab.append_jsonl(tmp_path / "ai_checks" / "2026-11-18.jsonl",
                     [{"cost": 0.07, "decision": "follow_move_ai"}, {"cost": 0.05, "decision": None, "error": "x"}])
    out = report.ai_summary(tmp_path, {"ai_budget": {"day": ai_check._day(NOW), "spent": 0.12, "checks": 2}}, NOW)
    assert out["decided"] == 2 and out["checks"] == 2 and out["bought"] == 1 and out["failed"] == 1
    assert out["ai_error"] == pytest.approx((0.04 + 0.09) / 2) and out["market_error"] == pytest.approx((0.16 + 0.25) / 2)
    assert out["ai_closer"] == 2 and out["spent_today"] == 0.12 and out["spent"] == 0.12


def test_full_run_buys_on_the_ai_check_at_the_real_book(tmp_path, openai):
    m = gamma(cid="0xjump", end_h=30, **MOVED, description="Resolves Yes if the thing happens.")
    openai["replies"] = [answer(0.72)]

    def fetch(url, body):
        if "/markets?" in url and "closed=true" in url:
            return []
        if "/events?" in url:
            return [{"id": "ev-0xjump", "title": "E", "markets": [m]}] if "offset=0" in url else []
        if url.endswith("/books"):
            return [{"asset_id": b["token_id"], "asks": [{"price": "0.66", "size": "100"}, {"price": "0.60", "size": "4"}]}
                    for b in body]
        raise AssertionError(url)

    row = lab.run(tmp_path, NOW, fetch, seed=1)
    assert not row["problems"], row["problems"]
    trades = report.read_jsonl(tmp_path / "trades")
    ai = [t for t in trades if t["strategy"] == "follow_move_ai"]
    assert len(ai) == 1 and ai[0]["note"]["ai_chance0"] == 0.72
    assert ai[0]["legs"][0]["outcome"] == "Yes" and ai[0]["avg_price"] <= 0.67 + 0.01  # never past the 67c cap (+fee)
    assert "Resolves Yes if the thing happens." in openai["requests"][0]["input"]
    checks = report.read_jsonl(tmp_path / "ai_checks")
    assert len(checks) == 1 and checks[0]["decision"] == "follow_move_ai"
    text = (tmp_path / "report.md").read_text()
    assert "## AI check" in text and "Today: 1 checks" in text and "follow_move_ai" in text
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["ai_check"]["checks"] == 1 and summary["strategies"]["follow_move_ai"]["trades"] == 1
    # the next run neither checks nor buys the same market again
    row2 = lab.run(tmp_path, NOW + 2400, fetch, seed=2)
    assert len(openai["requests"]) == 1 and not [t for t in report.read_jsonl(tmp_path / "trades")
                                                if t["strategy"] == "follow_move_ai" and t["opened_at"] > NOW]
    assert not row2["problems"]
