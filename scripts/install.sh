#!/usr/bin/env bash
# Install Guyline from this checkout or an explicit local source/wheel.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR=""
WHEEL_FILE=""
DEV=false
GLOBAL_VENV=false
while [ "$#" -gt 0 ]; do
    case "$1" in
        --source|--wheel)
            [ "$#" -ge 2 ] || { echo "Missing path for $1" >&2; exit 2; }
            if [ "$1" = "--source" ]; then SOURCE_DIR="$2"; else WHEEL_FILE="$2"; fi
            shift 2 ;;
        --dev) DEV=true; shift ;;
        --global-venv) GLOBAL_VENV=true; shift ;;
        --with-channels) shift ;; # Common channel dependencies are included.
        --help|-h)
            echo "Usage: $0 [--source PATH | --wheel PATH] [--dev] [--global-venv]"
            echo "Default: install the local checkout; no remote product fallback."
            exit 0 ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done
if [ -n "$SOURCE_DIR" ] && [ -n "$WHEEL_FILE" ]; then
    echo "Choose either --source or --wheel" >&2
    exit 2
fi
if [ -n "$WHEEL_FILE" ]; then
    [ -f "$WHEEL_FILE" ] && [[ "$WHEEL_FILE" == *.whl ]] || {
        echo "Local wheel not found: $WHEEL_FILE" >&2; exit 2;
    }
    TARGET="$(cd "$(dirname "$WHEEL_FILE")" && pwd)/$(basename "$WHEEL_FILE")"
else
    SOURCE_DIR="${SOURCE_DIR:-$SCRIPT_DIR/..}"
    [ -f "$SOURCE_DIR/pyproject.toml" ] || {
        echo "No local checkout. Supply --source PATH or --wheel PATH." >&2; exit 2;
    }
    SOURCE_DIR="$(cd "$SOURCE_DIR" && pwd)"
    TARGET="$SOURCE_DIR"
fi

PYTHON_CMD="$(command -v python3 || command -v python || true)"
[ -n "$PYTHON_CMD" ] || { echo "Python 3.10+ is required" >&2; exit 1; }
"$PYTHON_CMD" -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ is required"'
VENV_DIR="$HOME/.guyline-venv"
if [ "$DEV" = true ] && [ "$GLOBAL_VENV" = false ] && [ -z "$WHEEL_FILE" ]; then
    VENV_DIR="$SOURCE_DIR/.guyline-venv"
fi
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi
VENV_PYTHON="$VENV_DIR/bin/python"
[ -x "$VENV_PYTHON" ] || { echo "Incomplete venv: $VENV_DIR" >&2; exit 1; }
if [ -n "$WHEEL_FILE" ]; then
    "$VENV_PYTHON" -m pip install "$TARGET"
else
    "$VENV_PYTHON" -m pip install -e "$TARGET"
fi

# Resolve resources with the installed interpreter, independent of caller cwd.
"$VENV_PYTHON" -m guyline --version
"$VENV_PYTHON" -m guyline agent --help
"$VENV_PYTHON" -m guyline gateway --help
FRONTEND_DIR="$("$VENV_PYTHON" -c 'from guyline.ui.react_launcher import get_frontend_dir; print(get_frontend_dir())')"
[ -f "$FRONTEND_DIR/package.json" ] || { echo "Installed frontend missing: $FRONTEND_DIR" >&2; exit 1; }
if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    if [ -f "$FRONTEND_DIR/package-lock.json" ]; then
        (cd "$FRONTEND_DIR" && npm ci --no-fund --no-audit)
    else
        (cd "$FRONTEND_DIR" && npm install --no-fund --no-audit)
    fi
else
    echo "Node.js 18+ and npm are required for the React terminal; install them before launch."
fi
CONFIG_DIR="$("$VENV_PYTHON" -c 'from guyline.config.paths import get_config_dir; print(get_config_dir())')"
mkdir -p "$CONFIG_DIR/skills" "$CONFIG_DIR/plugins"

LAUNCHER="$VENV_DIR/bin/guyline"
[ -x "$LAUNCHER" ] || { echo "Guyline launcher missing: $LAUNCHER" >&2; exit 1; }
"$LAUNCHER" --version
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
ln -snf "$LAUNCHER" "$BIN_DIR/guyline"
echo "Guyline installed from $TARGET"
echo "Launcher: $BIN_DIR/guyline"
echo "Add $BIN_DIR to PATH. Run: guyline, guyline agent, or guyline gateway --help."
