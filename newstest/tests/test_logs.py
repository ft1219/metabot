import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import logs  # noqa: E402

LOG = """\
2026-11-17T15:28:10.0170925Z 2026-11-17 15:28:10,016 - __main__ - INFO - 3 open questions, 2 to forecast now, 0 deferred to the next run
2026-11-17T15:28:29.2498404Z 2026-11-17 15:28:29,249 - __main__ - INFO - Found Research for URL https://www.metaculus.com/questions/46552:
2026-11-17T15:28:29.2499677Z ## News from AskNews
2026-11-17T15:28:29.2500570Z Here are the relevant news articles:
2026-11-17T15:28:29.2501292Z 
2026-11-17T15:28:29.2501945Z **Nvidia news**
2026-11-17T15:28:29.2684403Z 
2026-11-17T15:28:29.2684677Z ## News from ChatGPT web search (searched 2026-11-17 UTC)
2026-11-17T15:28:29.2686833Z - **November 11:** the board met.
2026-11-17T15:28:35.6492235Z ##[warning]https://www.metaculus.com/questions/46498: searched for Metaculus, so its answer was not used.
2026-11-17T15:28:35.6504555Z 2026-11-17 15:28:35,646 - __main__ - INFO - Found Research for URL https://www.metaculus.com/questions/46498:
2026-11-17T15:28:35.6505956Z Here are the relevant news articles:
2026-11-17T15:28:35.6506298Z 
2026-11-17T15:28:35.6506579Z **Uruguay Open**
2026-11-17T15:28:40.5052856Z 2026-11-17 15:28:40,504 - __main__ - INFO - Forecasted URL https://www.metaculus.com/questions/46552 with prediction: 0.01.
2026-11-17T15:29:00.0000000Z 2026-11-17 15:29:00,000 - __main__ - INFO - Found Research for URL https://www.metaculus.com/questions/46600:
2026-11-17T15:29:00.0000001Z ## News from ChatGPT web search (searched 2026-11-17 UTC)
2026-11-17T15:29:00.0000002Z - only the web part
2026-11-17T15:29:09.2742732Z 2026-11-17 15:29:09,273 - forecasting_tools.helpers.metaculus_client - INFO - Posted prediction on question 46754
"""


def test_parse_splits_each_question_and_its_two_sources():
    found = logs.parse_log(LOG, run_id=7)
    assert [r.post_id for r in found] == [46552, 46498, 46600]
    both, asknews_only, web_only = found
    assert both.at == "2026-11-17T15:28:29.2498404Z" and both.run_id == 7
    assert both.sources() == "both"
    a, w = both.parts()
    assert a == "Here are the relevant news articles:\n\n**Nvidia news**"
    assert w == "## News from ChatGPT web search (searched 2026-11-17 UTC)\n- **November 11:** the board met."
    assert both.text.startswith("## News from AskNews\n") and both.text.endswith("the board met.")
    assert asknews_only.sources() == "asknews" and asknews_only.parts() is None
    assert asknews_only.text == "Here are the relevant news articles:\n\n**Uruguay Open**"
    assert web_only.sources() == "chatgpt" and web_only.parts() is None


def test_research_stops_at_a_time_gap_even_without_a_new_logger_line():
    log = (
        "2026-11-17T23:59:59.9000000Z 2026-11-17 23:59:59,900 - __main__ - INFO - Found Research for URL https://www.metaculus.com/questions/1:\n"
        "2026-11-17T23:59:59.9100000Z news line\n"
        "2026-11-18T00:00:00.0100000Z still the same write, after midnight\n"
        "2026-11-18T00:00:30.0000000Z 💰  AI cost this run: $0.10\n"
    )
    (r,) = logs.parse_log(log, run_id=1)
    assert r.text == "news line\nstill the same write, after midnight"


def test_latest_research_per_question_wins():
    a = logs.Research(1, "u", "2026-11-17T10:00:00Z", 1, "old")
    b = logs.Research(1, "u", "2026-11-17T11:00:00Z", 2, "new")
    assert logs.latest_per_question([b, a])[1].text == "new"
