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
MOVED = dict(bid=0.59, ask=0.60, oneDayPriceChange=0.15, question="Will the price of Ethereum be above $1,800 on Friday?")


def view(**kw):
    args = dict(MOVED)
    args.update(kw)
    return lab.market_view(gamma(**args), NOW)


def answer(chance=0.7, searches=2, tin=12_000, tout=1_500, text=None, status="completed", url=None, said="false",
           sources=("https://news.example.com/a",), echo=MOVED["question"]):
    out = [{"type": "reasoning"}]
    out += [{"type": "web_search_call", "action": {"type": "search", "query": f"q{i}",
                                                   "sources": [{"type": "url", "url": u} for u in sources]}}
            for i in range(searches)]
    msg = text if text is not None else (f'The news says so.\n{{"question": {json.dumps(echo)}, "chance": {chance}, '
                                         f'"saw_odds": {said}, "why": "because"}}')
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

def test_move_ai_buys_the_side_the_ai_rates_5c_over_its_price():
    v = view()
    assert S.ai_candidate(v)
    assert S.move_ai(v, 0.70, False) == (0, 0.65)  # AI 70% for Yes, priced 60c: buy, pay at most 65c
    assert S.move_ai(v, 0.64, False) is None  # 4c over the price: not enough, and No (36% vs 41c) neither
    assert S.move_ai(v, 0.65, False) == (0, 0.6)
    assert S.move_ai(v, 0.30, False) == (1, 0.65)  # AI 70% for No, priced 41c
    assert S.move_ai(v, 0.99, False) == (0, 0.85)  # never above follow_move's 85c
    for c in [x / 100 for x in range(1, 100)]:  # at most one side, and only with the margin
        hit = S.move_ai(v, c, False)
        if hit:
            chance = c if hit[0] == 0 else 1 - c
            ask = 0.60 if hit[0] == 0 else 0.41
            assert chance - ask >= S.AI_MARGIN - 1e-9 and hit[1] >= ask - 1e-9


def test_move_ai_clean_skips_checks_that_saw_odds():
    v = view()
    assert S.move_ai_clean(v, 0.70, False) == S.move_ai(v, 0.70, False) == (0, 0.65)
    assert S.move_ai_clean(v, 0.70, True) is None and S.move_ai(v, 0.70, True) == (0, 0.65)


def test_ai_rules_keep_follow_moves_price_window_and_market_filters():
    dear = view(bid=0.89, ask=0.90)  # Yes at 90c is outside 10-85c, but No at 11c is in
    assert S.move_ai(dear, 0.99, False) is None
    assert S.ai_candidate(dear) and S.move_ai(dear, 0.02, False) == (1, 0.85)
    assert S.move_ai(view(oneDayPriceChange=-0.15), 0.20, False) == (1, 0.75)
    assert not S.ai_candidate(view(oneDayPriceChange=0.05))  # no real move
    assert S.move_ai(view(oneDayPriceChange=0.05), 0.99, False) is None
    assert not S.ai_candidate(view(sportsMarketType="moneyline"))
    assert not S.ai_candidate(view(volume24hr=0))
    assert not S.ai_candidate(view(bid=0.50, ask=0.60))  # gap too wide to trust the quote


def test_ai_strategies_start_on_their_own_date_and_wait_for_150_trades():
    for name in ("move_ai", "move_ai_clean"):
        cfg = S.STRATEGIES[name]
        assert cfg["active"] and cfg["rule"] is None and cfg["since"] == "2026-11-19"
        assert cfg.get("judge", "bet") == "bet" and cfg["min_settled"] == S.AI_MIN_SETTLED == 150
    st = {"settled": 60, "wins": 60, "pnl": 100.0, "p_luck": 1e-9, "days": 12}
    assert report.judge("move_ai", st, 20) is None  # a perfect 60 trades is still too early
    assert report.judge("follow_move", st, 20) == "PASS"
    assert report.judge("move_ai", dict(st, settled=150, wins=150), 30) == "PASS"


# ---------------------------------------------------------------- answer, prompt, cost

def test_parse_answer_takes_the_last_json_line():
    assert ai_check.parse_answer('{"chance": 0.2}\nthen\n{"question": " Will X? ", "chance": 0.64, "saw_odds": false, '
                                 '"why": "x"}') == (0.64, False, "x", "Will X?")
    assert ai_check.parse_answer('{"chance": 64, "saw_odds": true, "why": "pct"}') == (0.64, True, "pct", "")
    assert ai_check.parse_answer('{"chance": 1.0, "question": 7}') == (0.99, None, "", "")
    assert ai_check.parse_answer('{"chance": 0, "saw_odds": "no"}') == (0.01, None, "", "")
    assert ai_check.parse_answer("I think about 60%.")[0] is None
    assert ai_check.parse_answer('{"chance": "high"}')[0] is None
    assert ai_check.parse_answer('{"chance": 250}')[0] is None


def test_an_answer_to_another_question_is_caught():
    eth = view(question="Will the price of Ethereum be above $1,800 on November 19?")
    for echo in ("Will the price of Ethereum be above $1,800 on November 19?",
                 "will the price of ethereum be above 1800 on november 19",  # case, $ and commas do not matter
                 "Will the price of Ethereum be above $1,800 on Nov 19?"):
        assert not ai_check.wrong_question(echo, eth), echo
    for echo in ("Will the price of XRP be above $1.00 on November 19?",  # 19 Nov: another market's prompt
                 "Will the price of Ethereum be above $1,900 on November 19?",  # the same event, another level
                 "", "  "):
        assert ai_check.wrong_question(echo, eth), echo
    googl = view(question="Will Alphabet Inc. (GOOGL) hit (LOW) $275 Week of November 16 2026?")
    assert not ai_check.wrong_question("Will Alphabet (GOOGL) hit (LOW) $275 Week of November 16 2026?", googl)
    assert ai_check.wrong_question("Will Donald Trump post 40-59 Truth Social posts November 14-21?", googl)
    pm = view(question="Will Pedro Sánchez remain Prime Minister of Spain through 2026?")
    assert not ai_check.wrong_question("Will Pedro Sanchez remain Prime Minister of Spain through 2026?", pm)
    assert not ai_check.wrong_question("anything", view(question="Will the price be above?"))  # nothing telling to check


def test_the_record_keeps_what_was_searched_and_read():
    r = answer(searches=2, sources=("https://www.reuters.com/a", "https://coindesk.com/b"), url="https://cnbc.com/c")
    # cited first, then opened, then read; each once
    assert ai_check.searched(r) == (["q0", "q1"], ["cnbc.com", "www.reuters.com", "coindesk.com"])
    r["output"][1]["action"] = {"type": "open_page", "url": "https://example.org/p"}
    assert ai_check.searched(r)[1] == ["cnbc.com", "example.org", "www.reuters.com", "coindesk.com"]
    r["output"][2]["action"]["url"] = "https://" + "x" * 300 + ".com/p"  # no real site has a name this long
    assert len(ai_check.searched(r)[1]) == 4
    assert ai_check.searched({"output": []}) == ([], [])


def test_the_record_says_when_its_lists_were_cut(openai):
    many = answer(searches=3, sources=[f"https://s{i}.example.com/" for i in range(40)])
    many["output"][1]["action"]["queries"] = [f"extra {i}" for i in range(10)]
    openai["replies"] = [many]
    _, (row,) = ai_check.run_checks([view()], {}, _state(), LATE, random.Random(1), [])
    assert len(row["sites"]) == ai_check.SITES_KEPT and row["sites_count"] == 40
    assert len(row["queries"]) == ai_check.QUERIES_KEPT and row["queries_count"] == 13


def test_saw_odds_is_strict():
    sites = ai_check.odds_sites(answer(sources=("https://news.example.com/a", "https://polymarket.com/event/x")))
    assert sites == ["polymarket.com"]
    assert ai_check.odds_sites(answer(url="https://kalshi.com/markets/x")) == ["kalshi.com"]
    q = answer()
    q["output"][1]["action"]["query"] = "Polymarket odds Trump posts"
    assert ai_check.odds_sites(q) == ["search: polymarket"]
    assert ai_check.odds_sites(answer()) == []
    # anywhere in a page's address, in betting words in a search, and in the written answer
    assert ai_check.odds_sites(answer(sources=("https://x.com/Polymarket/status/1",))) == ["x.com: polymarket"]
    assert ai_check.odds_sites(answer(url="https://www.coindesk.com/markets/polymarket-traders-bet-xrp")) == [
        "www.coindesk.com: polymarket"]
    assert ai_check.odds_sites(answer(sources=("https://sports.betmgm.com/en/x",))) == ["sports.betmgm.com"]
    q = answer()
    q["output"][1]["action"]["query"] = "Trump approval betting odds"
    assert ai_check.odds_sites(q) == ["search: betting odds"]
    told = answer(text='Polymarket has this at 70%.\n{"chance": 0.7, "saw_odds": false, "why": "x"}')
    assert ai_check.odds_sites(told) == ["answer: polymarket"]


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
    assert req["include"] == ["web_search_call.action.sources"] and '"saw_odds"' in prompt and '"question"' in prompt
    assert prompt.count("Will X happen by Friday?") == 2  # asked again right before the answer
    assert req["max_tool_calls"] == ai_check.MAX_TOOL_CALLS and req["max_output_tokens"] == ai_check.MAX_OUTPUT_TOKENS


def test_most_a_check_can_cost_bounds_a_normal_answer():
    most = ai_check.most_a_check_can_cost("x" * 4000)
    assert 0.18 < most < 0.22
    # the trial's priciest check (32,800 input tokens with 6 searches) fits even though only 4 are allowed now
    big = answer(searches=ai_check.MAX_TOOL_CALLS, tin=32_800, tout=ai_check.MAX_OUTPUT_TOKENS)
    real = ai_check.token_cost(32_800, ai_check.MAX_OUTPUT_TOKENS) + ai_check.tool_calls(big) * ai_check.USD_PER_SEARCH
    assert real < most


def test_daily_money_is_let_out_evenly():
    midnight = NOW - NOW % 86400
    assert ai_check.allowance(midnight) == pytest.approx(0.25)
    assert ai_check.allowance(midnight + 43200) == pytest.approx(0.625)
    assert ai_check.allowance(midnight + 86399) == pytest.approx(1.00, abs=1e-4)
    assert ai_check.allowance(midnight + 0.9 * 86400) < 1.0  # money still comes free late in the evening
    st = {"ai_budget": {"day": "2000-01-01", "spent": 0.9, "checks": 9}}
    assert ai_check.budget(st, NOW) == {"day": ai_check._day(NOW), "spent": 0.0, "checks": 0}


# ---------------------------------------------------------------- run_checks

def _state():
    return {"positions": [], "traded_events": {}, "verdicts": {}}


def test_run_checks_buys_where_the_ai_beats_the_price_and_records_every_check(openai):
    vs = [view(cid=f"0x{i}") for i in range(5)]
    openai["replies"] = [answer(0.70), answer(0.61), answer(0.30, sources=("https://polymarket.com/e",))]
    st, problems = _state(), []
    picks, rows = ai_check.run_checks(vs, {}, st, LATE, random.Random(1), problems)
    assert len(rows) == ai_check.MAX_CHECKS_PER_RUN == 3 and not problems
    assert [r["side"] for r in rows] == [0, None, 1]
    assert [r["saw_odds"] for r in rows] == [False, False, True] and rows[2]["odds_sites"] == ["polymarket.com"]
    assert rows[0]["with_move"] is True and rows[2]["with_move"] is False  # Yes rose; the third bought No
    assert [(p[1], p[2]) for p in picks["move_ai"]] == [(0, 0.65), (1, 0.65)]
    (v, i, cap, note), = picks["move_ai_clean"]  # the check that saw Polymarket is left out
    assert (i, cap) == (0, 0.65) and note["ai_chance0"] == 0.70 and v["conditionId"] == rows[0]["condition_id"]
    cost = ai_check.token_cost(12_000, 1_500) + 2 * ai_check.USD_PER_SEARCH
    assert rows[0]["cost"] == pytest.approx(cost, abs=1e-4) and rows[0]["searches"] == 2
    assert st["ai_budget"]["spent"] == pytest.approx(3 * cost, abs=1e-3) and st["ai_budget"]["checks"] == 3
    assert len(st["ai_watch"]) == 3 and set(st["ai_checked"]) == {r["event_id"] for r in rows}
    assert rows[0]["ask0"] == 0.6 and rows[0]["ask1"] == pytest.approx(0.41) and rows[0]["move"] == 0.15
    # the next run checks only events not checked before
    openai["replies"] = []
    _, rows2 = ai_check.run_checks(vs, {}, st, LATE + 3600, random.Random(2), [])
    assert rows2 and {r["event_id"] for r in rows2}.isdisjoint({r["event_id"] for r in rows})


def _echo(request, timeout=None):
    """An OpenAI that answers whatever question it was sent (read back from the prompt) and copies it back."""
    asked = request["input"].split("Remember that the question is: ", 1)[1].split("\n", 1)[0]
    reply = answer(0.95, echo=asked)
    reply["output"][-1]["content"][0]["text"] = reply["output"][-1]["content"][0]["text"].replace(
        '"because"', json.dumps(asked))
    return reply


@pytest.mark.parametrize("when, n", [(LATE, 3), (LATE - 20 * 3600 + 60, 1)])
def test_each_check_is_sent_its_own_markets_question(openai, monkeypatch, when, n):
    # 19 Nov: every check was sent the last prompt built, even one for a market the budget then left out
    monkeypatch.setattr(ai_check, "ask_openai", _echo)
    names = ["Ethereum", "Solana", "Dogecoin", "Cardano", "Litecoin"]
    vs = [view(cid=f"0x{i}", question=f"Will {name} be above $1 on Friday?") for i, name in enumerate(names)]
    events = {v["event_id"]: {"markets": [{"conditionId": v["conditionId"], "description": f"About {name} only."}]}
              for v, name in zip(vs, names)}
    picks, rows = ai_check.run_checks(vs, events, _state(), when, random.Random(3), [])
    assert len(rows) == n
    for r in rows:
        assert r["why"] == r["question"] == r["echo"] and not r.get("error")
        assert r["ai_version"] == S.AI_VERSION
    assert all(note["ai_version"] == S.AI_VERSION for *_, note in picks["move_ai"])


def test_trades_from_the_first_version_are_left_out_of_results(tmp_path):
    old = {"strategy": "move_ai", "title": "Old market Zebra?", "cost": 5.0, "avg_price": 0.744,
           "payout_if_won": 6.7, "opened_at": NOW, "settled_at": NOW, "payout": 6.7, "pnl": 1.7,
           "legs": [{"condition_id": "0x1", "outcome": "No", "outcome_index": 1}], "note": {"ai_chance0": 0.2}}
    new = dict(old, title="New market Quokka?", note={"ai_chance0": 0.2, "ai_version": S.AI_VERSION},
               legs=[{"condition_id": "0x2", "outcome": "No", "outcome_index": 1}])
    assert not S.counted("move_ai", old) and S.counted("move_ai", new) and S.counted("follow_move", old)
    lab.append_jsonl(tmp_path / "settled" / "2026-11.jsonl", [old, new])
    lab.append_jsonl(tmp_path / "trades" / "2026-11.jsonl", [old, new])
    text, summary = report.build(tmp_path, NOW, state={"positions": [dict(old, strategy="move_ai_clean")]})
    assert summary["strategies"]["move_ai"]["settled"] == 1 and summary["strategies"]["move_ai"]["trades"] == 1
    assert summary["strategies"]["move_ai_clean"]["open"] == 0
    assert "Quokka" in text and "Zebra" not in text  # not in the daily table or the latest buys either


def test_nothing_is_bought_on_an_answer_to_another_question(openai):
    xrp = "Will the price of XRP be above $1.00 on Friday?"
    openai["replies"] = [answer(0.95, echo=xrp), answer(0.95)]
    vs = [view(cid="0x1"), view(cid="0x2")]
    st, problems = _state(), []
    picks, rows = ai_check.run_checks(vs, {}, st, LATE, random.Random(1), problems)
    bad, good = sorted(rows, key=lambda r: not r.get("wrong_question"))
    assert bad["wrong_question"] and bad["side"] is None and xrp in bad["error"]
    assert bad["cost"] > 0 and bad["event_id"] in st["ai_checked"]  # billed, and not asked again
    assert good["side"] == 0 and not good.get("wrong_question") and good["echo"] == good["question"]
    assert [p[0]["conditionId"] for p in picks["move_ai"]] == [good["condition_id"]]
    assert [w["condition_id"] for w in st["ai_watch"]] == [good["condition_id"]]  # only real answers are scored
    assert "1 of 2 check(s) failed (answered another question (Will the price of XRP" in problems[0]
    assert good["queries"] == ["q0", "q1"] and good["sites"] == ["news.example.com"]


def test_a_check_that_does_not_say_whether_it_saw_odds_counts_as_seen(openai):
    openai["replies"] = [answer(0.70, said="null")]
    picks, rows = ai_check.run_checks([view()], {}, _state(), LATE, random.Random(1), [])
    assert rows[0]["saw_odds"] is True and picks["move_ai"] and not picks["move_ai_clean"]


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
    st["traded_events"]["move_ai_clean"] = {c["event_id"]: NOW + 1e6}
    _, rows = ai_check.run_checks([a, b, c], {}, st, LATE, random.Random(1), [])
    assert len(rows) == 1 and rows[0]["event_id"] == a["event_id"]
    # a sister market of an event already checked is not checked on a later run either
    _, rows = ai_check.run_checks([b], {}, st, LATE + 2400, random.Random(1), [])
    assert rows == []


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
        {"move_ai": [], "move_ai_clean": []}, [])
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
    assert not any(picks.values()) and len(rows) == 3 and all(r["side"] is None for r in rows)
    assert rows[0]["error"].startswith("cut off") and rows[0]["cost"] == pytest.approx(ai_check.most_a_check_can_cost(openai["requests"][0]["input"]), abs=1e-4)
    assert rows[1]["error"] == "no chance in the answer" and rows[2]["error"].startswith("answer")
    assert "3 of 3 check(s) failed" in problems[0]
    assert not st.get("ai_watch") and len(st["ai_checked"]) == 3


def test_a_refused_check_costs_nothing_and_leaves_the_event_for_later(openai):
    openai["replies"] = [RuntimeError("OpenAI HTTP 429 (rate_limit_exceeded)"), answer(0.7)]
    st, problems = _state(), []
    vs = [view(cid="0xa"), view(cid="0xb")]
    picks, rows = ai_check.run_checks(vs, {}, st, LATE, random.Random(1), problems)
    assert len(rows) == 1 and st["ai_budget"]["checks"] == 1 and len(st["ai_checked"]) == 1
    assert "1 of 2 check(s) failed (OpenAI HTTP 429 (rate_limit_exceeded))" in problems[0]
    # the refused event is checked on a later run
    openai["replies"] = []
    _, later = ai_check.run_checks(vs, {}, st, LATE + 2400, random.Random(1), [])
    assert len(later) == 1 and later[0]["event_id"] != rows[0]["event_id"]


def test_lasting_openai_refusals_stop_the_run_without_using_up_markets(openai):
    for err in ("OpenAI HTTP 404 (model_not_found), so no more checks this run",
                "OpenAI HTTP 403, so no more checks this run"):
        openai["replies"] = [ai_check.Stop(err)] * 3
        st, problems = _state(), []
        _, rows = ai_check.run_checks([view(cid=f"0x{i}") for i in range(3)], {}, st, LATE, random.Random(1), problems)
        assert rows == [] and problems == [f"AI check: {err}"] and not st["ai_checked"]


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
        ((_http_error(403, {}),), ai_check.Stop, "HTTP 403"),
        ((_http_error(404, {"error": {"code": "model_not_found"}}),), ai_check.Stop, "model_not_found"),
        ((_http_error(400, {"error": {"code": "unsupported_parameter"}}),), ai_check.Stop, "unsupported_parameter"),
        ((_http_error(400, {"error": {"code": "unsupported_value", "param": "reasoning.effort"}}),), ai_check.Stop,
         "unsupported_value"),
        ((_http_error(400, {"error": {"code": None, "type": "invalid_request_error"}}),), ai_check.Stop,
         "invalid_request_error"),
        ((_http_error(400, {"error": {"code": "invalid_prompt"}}),), RuntimeError, "HTTP 400 (invalid_prompt)"),
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
    rows = [{"chance0": 0.8, "bid0": 0.59, "ask0": 0.61, "result0": 1.0, "saw_odds": False, "settled_at": NOW},
            {"chance0": 0.3, "bid0": 0.49, "ask0": 0.51, "result0": 0.0, "saw_odds": True, "settled_at": NOW},
            {"chance0": 0.3, "bid0": 0.49, "ask0": 0.51, "result0": None, "saw_odds": False, "settled_at": NOW}]
    first = {"chance0": 0.9, "bid0": 0.49, "ask0": 0.51, "result0": 0.0, "saw_odds": False, "settled_at": NOW}
    v2 = {"ai_version": S.AI_VERSION}
    lab.append_jsonl(tmp_path / "ai_results" / "2026-11.jsonl", [dict(r, **v2) for r in rows] + [first])
    lab.append_jsonl(tmp_path / "ai_checks" / "2026-11-18.jsonl", [dict(r, **v2) for r in [
        {"cost": 0.07, "chance0": 0.8, "side": 0, "bought": ["move_ai", "move_ai_clean"], "saw_odds": False},
        {"cost": 0.06, "chance0": 0.3, "side": 1, "bought": [], "saw_odds": True},
        {"cost": 0.05, "side": None, "error": "x"},
        {"cost": 0.08, "chance0": 0.2, "side": None, "error": "answered another question (x)", "wrong_question": True}]]
        + [{"cost": 0.10, "chance0": 0.9, "side": 1, "bought": ["move_ai"], "saw_odds": False}])  # first version
    out = report.ai_summary(tmp_path, {"ai_budget": {"day": ai_check._day(NOW), "spent": 0.36, "checks": 5}}, NOW)
    assert out["checks"] == 4 and out["rule_said_buy"] == 2 and out["bought"] == 1 and out["failed"] == 2
    assert out["wrong_question"] == 1 and out["answered"] == 2 and out["saw_odds"] == 1 and out["left_out"] == 1
    assert out["spent_today"] == 0.36 and out["spent"] == 0.36  # money spent counts, whatever the version
    assert out["all"] == {"n": 2, "ai_error": pytest.approx((0.04 + 0.09) / 2),
                          "market_error": pytest.approx((0.16 + 0.25) / 2), "ai_closer": 2}
    assert out["clean"]["n"] == 1 and out["clean"]["ai_error"] == pytest.approx(0.04)


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
    ai = [t for t in trades if t["strategy"] == "move_ai"]
    assert len(ai) == 1 and ai[0]["note"]["ai_chance0"] == 0.72
    assert [t["strategy"] for t in trades if t["strategy"].endswith("_clean")] == ["move_ai_clean"]
    assert ai[0]["legs"][0]["outcome"] == "Yes" and ai[0]["avg_price"] <= 0.67 + 0.01  # never past the 67c cap (+fee)
    assert "Resolves Yes if the thing happens." in openai["requests"][0]["input"]
    checks = report.read_jsonl(tmp_path / "ai_checks")
    assert len(checks) == 1 and checks[0]["side"] == 0 and checks[0]["bought"] == ["move_ai", "move_ai_clean"]
    text = (tmp_path / "report.md").read_text()
    assert "## AI check" in text and "Today: 1 checks" in text and "move_ai_clean" in text
    assert "move_ai and move_ai_clean wait for 150 finished trades" in text
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["ai_check"]["checks"] == 1 and summary["ai_check"]["bought"] == 1
    assert summary["strategies"]["move_ai"]["trades"] == 1
    # the next run neither checks nor buys the same market again
    row2 = lab.run(tmp_path, NOW + 2400, fetch, seed=2)
    assert len(openai["requests"]) == 1 and not [t for t in report.read_jsonl(tmp_path / "trades")
                                                if t["strategy"] == "move_ai" and t["opened_at"] > NOW]
    assert not row2["problems"]
