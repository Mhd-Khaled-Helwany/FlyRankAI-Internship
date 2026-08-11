#!/usr/bin/env bash
set -eu

# Run 8 curl requests (one per case) and save responses to evals/response_<i>.json
CASES=evals/cases.json
HOST=${HOST:-http://127.0.0.1:8000}

if [ ! -f "$CASES" ]; then
  echo "Cases file not found: $CASES. Run evals/generate_cases.py first." >&2
  exit 1
fi

mkdir -p evals/responses

for i in $(seq 0 7); do
  echo "Running case $i..."
  python3 -c "import json; cases=json.load(open('evals/cases.json')); import sys; print(json.dumps({'record': cases[$i]['record']}, ensure_ascii=False))" \
    | curl -s -X POST "$HOST/enrich" -H "Content-Type: application/json" -d @- \
    > evals/responses/response_${i}.json || echo "curl failed for case $i"
done

echo "Done. Responses saved in evals/responses/. Run evals/compare_results.py to summarize."
