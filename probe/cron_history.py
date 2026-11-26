"""
Throwaway: what cron-job.org recorded for the bot's two timer jobs (which
calls failed, and the 25 Nov 16:07 UTC slot). Prints dates, status codes and
cron-job.org's status text only; no URLs, headers or keys.
"""
import json
import os
import time
import urllib.error
import urllib.request

API = "https://api.cron-job.org"
KEY = os.environ["CRONJOB_API_KEY"]
STATUS = {0: "unknown", 1: "OK", 2: "DNS failed", 3: "connect failed", 4: "HTTP error",
          5: "timeout", 6: "too much data", 7: "invalid URL", 8: "internal error", 9: "unknown error"}


def get(path):
    req = urllib.request.Request(API + path, headers={"Authorization": f"Bearer {KEY}", "User-Agent": "bot-timer-check"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, None


def ts(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t)) if t else "-"


status, body = get("/jobs")
print("list jobs HTTP", status)
for job in (body or {}).get("jobs", []):
    jid = job["jobId"]
    print(f"\njob {jid} {job.get('title')!r} enabled={job.get('enabled')} lastStatus={STATUS.get(job.get('lastStatus'), job.get('lastStatus'))} "
          f"lastExecution={ts(job.get('lastExecution'))} lastDuration={job.get('lastDuration')} nextExecution={ts(job.get('nextExecution'))}")
    s, hist = get(f"/jobs/{jid}/history")
    rows = (hist or {}).get("history", [])
    print(f"history HTTP {s}: {len(rows)} entries, from {ts(min((r['date'] for r in rows), default=0))} to {ts(max((r['date'] for r in rows), default=0))}")
    for r in sorted(rows, key=lambda r: r["date"]):
        bad = r.get("status") != 1 or r.get("httpStatus") not in (200, 204)
        window = time.gmtime(r["date"])[:3] == (2026, 11, 25) and 14 <= time.gmtime(r["date"]).tm_hour <= 17
        if bad or window:
            print(f"  {'BAD ' if bad else ''}date={ts(r['date'])} planned={ts(r.get('datePlanned'))} status={STATUS.get(r.get('status'), r.get('status'))} "
                  f"http={r.get('httpStatus')} text={r.get('statusText')!r} duration={r.get('duration')}ms")
