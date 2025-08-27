#!/usr/bin/env bash
# Usage: ./test.sh <ENDPOINT_ID> <RUNPOD_API_KEY>
set -euo pipefail
EP_ID="${1:-REPLACE_ENDPOINT_ID}"
KEY="${2:-REPLACE_API_KEY}"

echo "Submitting job..."
JOB_JSON=$(curl -s -X POST "https://api.runpod.ai/v2/${EP_ID}/run" \
  -H "Authorization: Bearer ${KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "uplifting electronic dance music with tropical vibes",
      "duration": 12,
      "format": "mp3"
    }
  }')

JOB_ID=$(echo "$JOB_JSON" | jq -r '.id // .jobId // .status.id')
echo "Job ID: $JOB_ID"

echo "Polling status..."
while true; do
  STATUS_JSON=$(curl -s -H "Authorization: Bearer ${KEY}" \
    "https://api.runpod.ai/v2/${EP_ID}/status/${JOB_ID}")
  PHASE=$(echo "$STATUS_JSON" | jq -r '.status // .state // .status.status')
  echo "  -> $PHASE"
  if [[ "$PHASE" == "COMPLETED" ]]; then
    echo "$STATUS_JSON" > response.json
    echo "Saved response.json"
    # Extract audio and write to file
    echo "$STATUS_JSON" | jq -r '.output.audio_base64' | base64 -d > output.mp3
    echo "Wrote output.mp3"
    break
  elif [[ "$PHASE" == "FAILED" || "$PHASE" == "ERROR" ]]; then
    echo "$STATUS_JSON" > response.json
    echo "Job failed; saved response.json"
    exit 1
  fi
  sleep 3
done
