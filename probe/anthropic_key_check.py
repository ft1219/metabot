"""Read-only check that ANTHROPIC_API_KEY works and has credit. Never prints the key.
1) GET /v1/models/claude-sonnet-5-5 (free).
2) One tiny Messages request (a fraction of a cent of the free credit) to prove the credit balance is usable."""
import json, os, urllib.error, urllib.request

KEY = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
if not KEY:
    print("== ANTHROPIC_API_KEY is not set in this run")
    raise SystemExit(0)
H = {"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}


def call(method, url, body=None):
    req = urllib.request.Request(url, method=method, headers=H,
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"null")
        except Exception:
            return e.code, None
    except Exception as e:
        return None, repr(e)[:200]


s, b = call("GET", "https://api.anthropic.com/v1/models/claude-sonnet-5-5")
print(f"== models/claude-sonnet-5-5: HTTP {s} id={(b or {}).get('id') if isinstance(b, dict) else None} "
      f"max_input={(b or {}).get('max_input_tokens') if isinstance(b, dict) else None} "
      f"error={(b or {}).get('error') if isinstance(b, dict) else b}")

s, b = call("POST", "https://api.anthropic.com/v1/messages", {
    "model": "claude-sonnet-5-5",
    "max_tokens": 2000,
    "output_config": {"effort": "low"},
    "messages": [{"role": "user", "content": "Reply with the single word OK."}],
})
if s == 200 and isinstance(b, dict):
    text = " ".join(c.get("text", "") for c in b.get("content", []) if c.get("type") == "text").strip()
    print(f"== messages: HTTP 200 stop_reason={b.get('stop_reason')} text={text[:40]!r} usage={b.get('usage')}")
else:
    err = (b or {}).get("error") if isinstance(b, dict) else b
    print(f"== messages: HTTP {s} error={err}")
