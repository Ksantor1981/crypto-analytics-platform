#!/bin/bash
# Generate requirements-pinned.txt for reproducible installs
# Run from project root: ./scripts/generate_requirements_pinned.sh
set -e
cd "$(dirname "$0")/.."
for svc in backend ml-service workers; do
  if [ -f "$svc/requirements.txt" ]; then
    echo "Generating $svc/requirements-pinned.txt..."
    (cd "$svc" && pip install -r requirements.txt -q && pip freeze > requirements-pinned.txt)
    echo "  -> $svc/requirements-pinned.txt"
  fi
done
echo "Done. Commit requirements-pinned.txt for reproducible builds."
