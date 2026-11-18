import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run  # noqa: E402
from forecasting_tools import MultipleChoiceQuestion  # noqa: E402
from forecasting_tools.data_models.multiple_choice_report import PredictedOption, PredictedOptionList  # noqa: E402


def test_multiple_choice_with_number_options_scores_against_the_raw_label():
    q = MultipleChoiceQuestion(question_text="How many?", options=["0", "1", "2", "3 or more"], resolution_string="2")
    assert q.typed_resolution == 2.0  # the library's conversion the harness must not rely on
    pred = PredictedOptionList(predicted_options=[
        PredictedOption(option_name="0", probability=0.1),
        PredictedOption(option_name="1", probability=0.2),
        PredictedOption(option_name="2", probability=0.6),
        PredictedOption(option_name="3 or more", probability=0.1),
    ])
    out = run.score(q, pred)
    assert out["score"] == pytest.approx(100 * __import__("math").log(0.6 * 4) / __import__("math").log(4))
    assert run.resolution_text(q) == "2"


def test_compare_holds_back_a_verdict_until_enough_questions():
    few = run.compare([10.0, 20.0, 30.0], [0.0, 0.0, 0.0])
    assert few["verdict"] == "too few questions yet" and few["a_better"] == 3
    n = run.MIN_N
    clear = run.compare([10.0 + (i % 3) for i in range(n)], [0.0] * n)
    assert clear["verdict"] == "first is better" and clear["low"] > 0
    noisy = run.compare([(-1) ** i * 50.0 for i in range(n)], [0.0] * n)
    assert noisy["verdict"] == "no clear difference"


def test_sign_test():
    assert run._sign_p(5, 5) == pytest.approx(1.0)
    assert run._sign_p(10, 0) == pytest.approx(2 / 1024)


def test_four_setups_differ_only_in_news():
    r = run.logs.Research(1, "u", "2026-11-17T10:00:00Z", 1,
                          "## News from AskNews\nA\n\n## News from ChatGPT web search (searched 2026-11-17 UTC)\nB")
    t = run.texts_for(r)
    assert t["both"] == t["both_again"] == r.text
    assert t["asknews"] == "A" and t["chatgpt"].endswith("\nB") and set(t) == set(run.ARMS)
