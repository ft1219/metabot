#!/usr/bin/env bash
# One news-test run inside GitHub Actions: fetch the news-test-data branch,
# run newstest/run.py with the options in newstest/args.txt, push the data
# back. Needs GH_TOKEN with contents: write and actions: read.
set -euo pipefail

BRANCH="news-test-data"
URL="https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
HERE="$(cd "$(dirname "$0")" && pwd)"
DATA="${RUNNER_TEMP:-/tmp}/news-test-data"

rm -rf "$DATA"
found=0
git ls-remote --exit-code --heads "$URL" "$BRANCH" >/dev/null || found=$?
if [ "$found" -eq 0 ]; then
  git clone --quiet --depth 1 --branch "$BRANCH" "$URL" "$DATA"
elif [ "$found" -eq 2 ]; then
  echo "No $BRANCH branch yet; starting a new one."
  mkdir -p "$DATA"
  git -C "$DATA" init --quiet -b "$BRANCH"
  git -C "$DATA" remote add origin "$URL"
else
  echo "Could not reach the repository to read the $BRANCH branch." >&2
  exit 1
fi

# grep finds nothing when every line is a comment; that must not stop the script.
args_line="$(grep -v '^#' "$HERE/args.txt" | tr '\n' ' ' || true)"
ARGS=()
read -r -a ARGS <<< "$args_line" || true
failed=0
(cd "$HERE/../metaculus-bot" && poetry run python ../newstest/run.py --data "$DATA" "${ARGS[@]}") || failed=$?

cd "$DATA"
git add -A
if git diff --cached --quiet; then
  echo "Nothing new to save."
  exit "$failed"
fi
git -c user.name="news-test" -c user.email="actions@users.noreply.github.com" \
  commit --quiet -m "News test run $(date -u +%Y-%m-%dT%H:%MZ)"
git push --quiet origin "HEAD:$BRANCH"
echo "Saved to the $BRANCH branch."
exit "$failed"
