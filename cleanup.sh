#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Cleanup script for PDF site project

Usage:
  ./cleanup.sh [options]

Options:
  --venv        Remove virtual environment (.venv)
  --docs        Remove generated docs/ folder
  --cache       Remove Python cache files (__pycache__)
  --all         Remove everything above
  -h, --help    Show this help

Examples:
  ./cleanup.sh --venv
  ./cleanup.sh --docs
  ./cleanup.sh --all
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REMOVE_VENV=0
REMOVE_DOCS=0
REMOVE_CACHE=0

if [ $# -eq 0 ]; then
  usage
  exit 0
fi

while [ $# -gt 0 ]; do
  case "$1" in
    --venv)
      REMOVE_VENV=1
      ;;
    --docs)
      REMOVE_DOCS=1
      ;;
    --cache)
      REMOVE_CACHE=1
      ;;
    --all)
      REMOVE_VENV=1
      REMOVE_DOCS=1
      REMOVE_CACHE=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

echo "Starting cleanup..."

if [ "$REMOVE_VENV" = "1" ]; then
  if [ -d "$SCRIPT_DIR/.venv" ]; then
    rm -rf "$SCRIPT_DIR/.venv"
    echo "Removed .venv"
  else
    echo ".venv not found"
  fi
fi

if [ "$REMOVE_DOCS" = "1" ]; then
  if [ -d "$SCRIPT_DIR/docs" ]; then
    rm -rf "$SCRIPT_DIR/docs"
    echo "Removed docs/"
  else
    echo "docs/ not found"
  fi
fi

if [ "$REMOVE_CACHE" = "1" ]; then
  find "$SCRIPT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  find "$SCRIPT_DIR" -type f -name "*.pyc" -delete
  echo "Removed Python cache"
fi

echo "Cleanup complete."
