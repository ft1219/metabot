"""
The news the bot had for each question, read back out of its GitHub Actions
logs. The bot logs its whole research text ("Found Research for URL ...")
before it forecasts, so the logs keep exactly what it read at that moment,
long before the answer was known. That is what makes a fair test possible:
news searched today about an old question would already contain its answer.

Since 17 November 2026 the research text is
    ## News from AskNews
    <AskNews articles>

    ## News from ChatGPT web search (searched YYYY-MM-DD UTC)
    <ChatGPT's findings>
and only one of the two parts when the other source failed or was thrown away.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

# GitHub puts its own timestamp in front of every log line.
GH_LINE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z) ?(.*)$")
# A new line from the bot's logger ("2026-11-17 15:28:29,249 - __main__ - INFO - ...").
LOGGER_LINE = re.compile(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3} - ")
FOUND = re.compile(r" - __main__ - INFO - Found Research for URL (\S+?):\s*$")
POST_ID = re.compile(r"/questions/(\d+)")
ASKNEWS_HEAD = "## News from AskNews"
WEB_HEAD = re.compile(r"^## News from ChatGPT web search \(searched [^)\n]*\)[ \t]*$", re.M)
# The research is one logger call, so all its lines carry (almost) the same
# GitHub timestamp; a later line belongs to something else.
MAX_GAP_SECONDS = 5.0


@dataclass
class Research:
    post_id: int
    url: str
    at: str  # when the bot had this news (GitHub's timestamp of the log line), ISO UTC
    run_id: int
    text: str  # the research exactly as the bot used it

    def parts(self) -> tuple[str, str] | None:
        """
        (AskNews part, ChatGPT part) when both sources gave news, else None.
        The AskNews part is what the bot reads with no web search; the
        ChatGPT part (with its heading) is what it reads with no AskNews.
        """
        if not self.text.startswith(ASKNEWS_HEAD + "\n"):
            return None
        m = WEB_HEAD.search(self.text)
        if not m:
            return None
        asknews = self.text[len(ASKNEWS_HEAD) + 1 : m.start()].strip()
        web = self.text[m.start() :].strip()
        if not asknews or web == m.group(0).strip():
            return None
        return asknews, web

    def sources(self) -> str:
        """'both', 'asknews' or 'chatgpt': which sources this question's news came from."""
        if self.parts():
            return "both"
        if WEB_HEAD.match(self.text):
            return "chatgpt"
        return "asknews"


def _seconds(ts: str) -> float:
    """Seconds since 1970 for GitHub's "2026-11-17T15:28:29.2498404Z" (7 decimals)."""
    whole, _, frac = ts.rstrip("Z").partition(".")
    at = datetime.fromisoformat(whole).replace(tzinfo=timezone.utc)
    return at.timestamp() + (float("0." + frac) if frac else 0.0)


def parse_log(log: str, run_id: int) -> list[Research]:
    """Every research text in one forecast job's log, in log order."""
    out: list[Research] = []
    # Split on newlines only: splitlines() would also break the news at
    # characters such as U+2028 that can appear inside articles.
    lines = [line[:-1] if line.endswith("\r") else line for line in log.split("\n")]
    i = 0
    while i < len(lines):
        m = GH_LINE.match(lines[i])
        found = FOUND.search(m.group(2)) if m else None
        if not found or not LOGGER_LINE.match(m.group(2)):
            i += 1
            continue
        started = m.group(1)
        body: list[str] = []
        i += 1
        while i < len(lines):
            n = GH_LINE.match(lines[i])
            if n is None:
                # A line without GitHub's timestamp is a continuation.
                body.append(lines[i])
                i += 1
                continue
            content = n.group(2)
            if (
                LOGGER_LINE.match(content)
                or content.startswith("##[")
                or abs(_seconds(n.group(1)) - _seconds(started)) > MAX_GAP_SECONDS
            ):
                break
            body.append(content)
            i += 1
        url = found.group(1)
        pid = POST_ID.search(url)
        text = "\n".join(body).strip()
        if pid and text:
            out.append(Research(int(pid.group(1)), url, started, run_id, text))
    return out


def latest_per_question(found: list[Research]) -> dict[int, Research]:
    """
    One research text per question: the latest. A question is only researched
    again when its earlier forecast failed, so the latest is what was posted.
    """
    out: dict[int, Research] = {}
    for r in sorted(found, key=lambda r: r.at):
        out[r.post_id] = r
    return out
