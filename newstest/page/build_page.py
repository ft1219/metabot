"""Puts summary.json's numbers into the page's data block."""
import json, re, sys
from pathlib import Path
page, summary, extra_spent = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()), float(sys.argv[3])
data = {
    "updated": summary["updated"], "questions": summary["questions"], "min_n": summary["min_questions_for_a_verdict"],
    "pairs": summary["pairs"], "setups": summary["setups"], "by_type": summary.get("by_type", {}),
    "waiting": [{"scheduled": w.get("scheduled"), "type": w.get("type")} for w in summary.get("waiting", [])],
    "sources": summary["news_sources_seen"], "spent_usd": round(summary.get("spent_in_total_usd", 0) + extra_spent, 2),
}
s = page.read_text()
s2 = re.sub(r'(<script id="data" type="application/json">).*?(</script>)',
            lambda m: m.group(1) + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + m.group(2), s, flags=re.S)
assert s2 != s or json.dumps(data) in s
page.write_text(s2)
print("ok", data["questions"], len(data["waiting"]), data["spent_usd"])
