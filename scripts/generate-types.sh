#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:5055}"

echo "Generating TypeScript types from ${BACKEND_URL}/openapi.json..."
cd "$(dirname "$0")/../frontend"
npx openapi-typescript "${BACKEND_URL}/openapi.json" -o src/types/api.ts
echo "Done: frontend/src/types/api.ts"
