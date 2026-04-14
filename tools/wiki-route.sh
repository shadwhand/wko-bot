#!/usr/bin/env bash
# Usage: tools/wiki-route.sh "What interval protocol targets FRC?"
# Returns: 2-3 wiki page paths most relevant to the question
# Uses local Qwen3-4B model via omlx for fast routing (~5-15s)

QUESTION="$1"
if [ -z "$QUESTION" ]; then
    echo "Usage: tools/wiki-route.sh \"your question here\""
    exit 1
fi

WIKI_DIR="docs/research/wiki"
INDEX=$(cat "$WIKI_DIR/index.md")

curl -s http://127.0.0.1:8001/v1/chat/completions \
    -H "Authorization: Bearer 9538" \
    -H "Content-Type: application/json" \
    -d "$(jq -n \
        --arg model "Qwen3-4B-Instruct-2507-Claude-Haiku-4.5-Distill-qx86-hi-mlx" \
        --arg prompt "Given this question and wiki index, return ONLY the file paths (e.g. concepts/ftp-threshold-testing.md) of the 2-3 most relevant pages. One path per line, nothing else.\n\nQuestion: $QUESTION\n\nIndex:\n$INDEX" \
        '{model: $model, messages: [{role: "user", content: $prompt}], max_tokens: 200, temperature: 0.1}')" \
    | jq -r '.choices[0].message.content' \
    | grep -E '\.md$' \
    | sed 's/^[- *]*//' \
    | head -3
