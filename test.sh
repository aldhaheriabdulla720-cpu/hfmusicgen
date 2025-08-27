#!/usr/bin/env bash
# Usage: ./test.sh <ENDPOINT_ID> <RUNPOD_API_KEY>
set -euo pipefail
EP_ID="${1:-REPLACE_ENDPOINT_ID}"
KEY="${2:-REPLACE_API_KEY}"
curl -s -X POST "https://api.runpod.ai/v2/${EP_ID}/run"           -H "Authorization: Bearer ${KEY}"           -H "Content-Type: application/json"           -d '{
    "input": {
      "prompt": "uplifting electronic dance music with tropical vibes",
      "duration": 12
    }
  }' | tee response.json
echo
echo "Response saved to response.json"