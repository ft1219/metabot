The results page (Artifact https://claude.ai/artifact/AeiM2cfKiFkeVyMkUM9e73).

To refresh it after a news test run:

    gh api "repos/ft1219/metabot/contents/summary.json?ref=news-test-data" --jq .content | base64 -d > summary.json
    python3 build_page.py news-source-test.html summary.json 0.55   # 0.55 = the two pipeline checks, not in spend.json

then publish news-source-test.html to that Artifact URL (read it first from a new session).
To start a run, push any change to newstest/args.txt on the news-test branch (comment lines are ignored).
