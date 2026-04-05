#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./build.sh path/to/file.pdf [options]

Options:
  --title "Site Title"        Override the site title
  --output docs               Output directory (default: ./docs)
  --dpi 160                   Render DPI (default: 160)
  --image-format webp         Image format: webp, png, jpg, jpeg (default: webp)
  --jpeg-quality 88           JPEG quality (default: 88)
  --webp-quality 82           WEBP quality (default: 82)
  --thumb-width 220           Thumbnail width in px (default: 220)
  --clean                     Remove output directory before build (default behavior)
  --no-clean                  Keep output directory if it exists
  -h, --help                  Show this help

Examples:
  ./build.sh ./site.pdf --title "My PDF Site"
  ./build.sh ./brochure.pdf --dpi 200 --image-format png
EOF
}

if [ $# -lt 1 ]; then
  usage
  exit 1
fi

PDF_PATH=""
TITLE=""
OUTPUT_DIR="docs"
DPI="160"
IMAGE_FORMAT="webp"
JPEG_QUALITY="88"
WEBP_QUALITY="82"
THUMB_WIDTH="220"
CLEAN_OUTPUT="1"

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --title)
      TITLE="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT_DIR="${2:-}"
      shift 2
      ;;
    --dpi)
      DPI="${2:-}"
      shift 2
      ;;
    --image-format)
      IMAGE_FORMAT="${2:-}"
      shift 2
      ;;
    --jpeg-quality)
      JPEG_QUALITY="${2:-}"
      shift 2
      ;;
    --webp-quality)
      WEBP_QUALITY="${2:-}"
      shift 2
      ;;
    --thumb-width)
      THUMB_WIDTH="${2:-}"
      shift 2
      ;;
    --clean)
      CLEAN_OUTPUT="1"
      shift
      ;;
    --no-clean)
      CLEAN_OUTPUT="0"
      shift
      ;;
    --*)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
    *)
      if [ -z "$PDF_PATH" ]; then
        PDF_PATH="$1"
        shift
      else
        echo "Unexpected argument: $1" >&2
        usage
        exit 1
      fi
      ;;
  esac
done

if [ -z "$PDF_PATH" ]; then
  echo "Error: missing PDF path." >&2
  usage
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
ABS_PDF_PATH="$PDF_PATH"

if [ ! -f "$ABS_PDF_PATH" ]; then
  if [ -f "$SCRIPT_DIR/$PDF_PATH" ]; then
    ABS_PDF_PATH="$SCRIPT_DIR/$PDF_PATH"
  else
    echo "Error: PDF not found: $PDF_PATH" >&2
    exit 1
  fi
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is not installed." >&2
  echo "Install it with: sudo apt update && sudo apt install -y python3 python3-venv python3-pip" >&2
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "[1/4] Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "[2/4] Installing dependencies..."
python -m pip install --upgrade pip >/dev/null
pip install -r "$SCRIPT_DIR/requirements.txt"

TARGET_OUTPUT="$OUTPUT_DIR"
case "$TARGET_OUTPUT" in
  /*) ;;
  *) TARGET_OUTPUT="$SCRIPT_DIR/$TARGET_OUTPUT" ;;
esac

if [ "$CLEAN_OUTPUT" = "1" ] && [ -d "$TARGET_OUTPUT" ]; then
  echo "[3/4] Removing existing output directory..."
  rm -rf "$TARGET_OUTPUT"
fi

echo "[4/4] Building GitHub Pages site..."

CMD=(python "$SCRIPT_DIR/pdf_to_github_pages.py" "$ABS_PDF_PATH" --output "$TARGET_OUTPUT" --dpi "$DPI" --image-format "$IMAGE_FORMAT" --jpeg-quality "$JPEG_QUALITY" --webp-quality "$WEBP_QUALITY" --thumb-width "$THUMB_WIDTH")

if [ -n "$TITLE" ]; then
  CMD+=(--title "$TITLE")
fi

"${CMD[@]}"

echo
echo "Build complete."
echo "Output: $TARGET_OUTPUT"
echo "Next: commit the generated files and let GitHub Actions publish them."
