#!/usr/bin/env bash
# Usage: ./test.sh <ENDPOINT_ID> <RUNPOD_API_KEY>
set -euo pipefail
EP_ID="${1:-REPLACE_ENDPOINT_ID}"
KEY="${2:-REPLACE_API_KEY}"

JOB=$(
  curl -s -X POST "https://api.runpod.ai/v2/${EP_ID}/run" \
    -H "Authorization: Bearer ${KEY}" \
    -H "Content-Type: application/json" \
    -d '{"input":{"prompt":"uplifting electronic dance music with tropical vibes","duration":12,"format":"mp3","seed":42}}'
)

JOB_ID=$(echo "$JOB" | jq -r '.id // .jobId // .status.id')
echo "JOB_ID=$JOB_ID"

# Choose base64 decode flag cross-platform
DEC="-d"; if [[ "$(uname -s)" == "Darwin" ]]; then DEC="-D"; fi

while true; do
  R=$(curl -s -H "Authorization: Bearer ${KEY}" \
       "https://api.runpod.ai/v2/${EP_ID}/status/${JOB_ID}")
  S=$(echo "$R" | jq -r '.status // .state // .status.status')
  echo "status=$S"
  if [[ "$S" == "COMPLETED" ]]; then
    echo "$R" | jq -r '.output.audio_base64' | base64 "$DEC" > output.mp3
    echo "Saved output.mp3"
    break
  elif [[ "$S" == "FAILED" || "$S" == "ERROR" ]]; then
    echo "$R" && exit 1
  fi
  sleep 3
done
