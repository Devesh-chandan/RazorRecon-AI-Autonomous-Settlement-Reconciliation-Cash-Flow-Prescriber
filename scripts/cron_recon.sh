#!/usr/bin/env bash
# RazorRecon — Production Cron Job Runner
# Prevents hosting platform (e.g., Render, EasyCron, GitHub Actions) output buffer overflow.
# Usage:
#   bash scripts/cron_recon.sh [API_URL]
# Example:
#   bash scripts/cron_recon.sh "https://your-backend-domain.com" > /dev/null 2>&1

set -euo pipefail

API_URL="${1:-http://localhost:8000}"
ENDPOINT="${API_URL}/api/recon/cron"

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Starting RazorRecon scheduled cron job via ${ENDPOINT}..."

# Execute POST request to lightweight HTTP 204 endpoint
# -s: Silent mode (no progress meters)
# -S: Show errors if request fails
# -o /dev/null: Discard response body to protect host buffer limit
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${ENDPOINT}" -H "Content-Type: application/json")

if [ "${HTTP_STATUS}" -eq 204 ] || [ "${HTTP_STATUS}" -eq 200 ]; then
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] SUCCESS: Reconciliation cron job triggered (HTTP ${HTTP_STATUS})."
    exit 0
else
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] ERROR: Cron job failed with HTTP status ${HTTP_STATUS}." >&2
    exit 1
fi
