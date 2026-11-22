"""Read-only plus one tiny paid call: which companies host each candidate parse-fallback
model on OpenRouter, and does the chosen one answer a parse-style request at temperature 0.
Prints provider names, prices and the model's short answer only; no key is printed."""
import json, os, urllib.error, urllib.request

KEY = os.environ["OPENROUTER_API_KEY"].strip()


def call(path, body=None):
    req = urllib.request.Request("https://openrouter.ai" + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


models = [m["id"] for m in call("/api/v1/models")["data"]]
cands = sorted(m for m in models if m.startswith(("google/gemini-3", "anthropic/claude-haiku", "openai/gpt-6-luna",
                                                  "deepseek/deepseek-v3.2")))
print("== candidates:", cands, flush=True)
for m in cands:
    try:
        eps = call(f"/api/v1/models/{m}/endpoints")["data"]["endpoints"]
        print(f"-- {m}: " + "; ".join(f"{e.get('provider_name')} ({e.get('tag')}) in {e.get('pricing', {}).get('prompt')} "
                                       f"out {e.get('pricing', {}).get('completion')}" for e in eps), flush=True)
    except urllib.error.HTTPError as e:
        print(f"-- {m}: HTTP {e.code}", flush=True)

TEXT = ("Here is a forecaster's answer:\n\"After weighing the news, I think the event is fairly unlikely. "
        "Probability: 23%\"\nReturn only the final probability as a decimal between 0 and 1, nothing else.")
for m in os.environ.get("TRY_MODELS", "").split():
    try:
        r = call("/api/v1/chat/completions", {"model": m, "temperature": 0.0, "max_tokens": 2000,
                                              "messages": [{"role": "user", "content": TEXT}], "usage": {"include": True}})
        msg = (r["choices"][0]["message"].get("content") or "").strip()[:80]
        print(f"== try {m}: served by {r.get('provider')}, answer {msg!r}, cost {r.get('usage', {}).get('cost')}", flush=True)
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read()).get("error", {}).get("message", "")[:160]
        except Exception:
            err = ""
        print(f"== try {m}: HTTP {e.code} {err}", flush=True)
