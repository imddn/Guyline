#!/usr/bin/env bash
# Developer installation shares the local source/wheel installer.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/install.sh" --dev "$@"
