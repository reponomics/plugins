#!/usr/bin/env bash
# Renders the PNG next to each SVG and compresses it.
#
#   tools/render-assets.sh                 every SVG under docs/assets/
#   tools/render-assets.sh FILE.svg DIR    only these SVGs, or every SVG under these folders
#
# Wordmarks (reponomics-wordmark-*.svg) render at 2x with a transparent background; everything else renders at its
# native size. rsvg-convert is required. pngquant (palette reduction at quality 90-100) and oxipng (lossless) are
# used when installed. RSVG, PNGQUANT and OXIPNG override the command names.
#
# Banners reference the shared wordmark as ../wordmark/reponomics-wordmark-*.svg. librsvg only loads referenced files
# from the SVG's own folder or below it, so each SVG is rendered from a temporary copy that has the wordmark folder
# beneath it instead of beside it.
set -euo pipefail

RSVG=${RSVG:-rsvg-convert}
PNGQUANT=${PNGQUANT:-pngquant}
OXIPNG=${OXIPNG:-oxipng}

if ! command -v "$RSVG" >/dev/null 2>&1; then
  echo "error: $RSVG not found. Install librsvg (macOS: brew install librsvg; Debian/Ubuntu: apt install librsvg2-bin)." >&2
  exit 1
fi

compress=true
for tool in "$PNGQUANT" "$OXIPNG"; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "note: $tool not found; PNGs will not be compressed (brew install pngquant oxipng)" >&2
    compress=false
  fi
done

if [ $# -eq 0 ]; then
  set -- "$(cd "$(dirname "$0")/.." && pwd)/docs/assets"
fi

svgs=()
for target in "$@"; do
  if [ -d "$target" ]; then
    while IFS= read -r -d '' svg; do svgs+=("$svg"); done < <(find "$target" -type f -name '*.svg' -print0 | sort -z)
  elif [ -f "$target" ] && [ "${target%.svg}" != "$target" ]; then
    svgs+=("$target")
  else
    echo "error: not an SVG file or folder: $target" >&2
    exit 1
  fi
done

if [ ${#svgs[@]} -eq 0 ]; then
  echo "error: no SVGs found in: $*" >&2
  exit 1
fi

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT

for svg in "${svgs[@]}"; do
  png="${svg%.svg}.png"
  case "$(basename "$svg")" in
    reponomics-wordmark-*) zoom=2 ;;
    *) zoom=1 ;;
  esac
  rm -rf "${stage:?}"/*
  wordmark="$(dirname "$svg")/../wordmark"
  [ -d "$wordmark" ] && cp -R "$wordmark" "$stage/wordmark"
  sed 's#xlink:href="\.\./wordmark/#xlink:href="wordmark/#g' "$svg" >"$stage/render.svg"
  "$RSVG" -z "$zoom" "$stage/render.svg" -o "$png"
  if $compress; then
    # exit 98 (result larger) and 99 (quality not reachable) leave the PNG unchanged
    "$PNGQUANT" --quality=90-100 --speed 1 --strip --skip-if-larger --force --ext .png -- "$png" || {
      rc=$?; [ "$rc" -eq 98 ] || [ "$rc" -eq 99 ] || exit "$rc"
    }
    "$OXIPNG" -q -o 4 --strip safe "$png"
  fi
  echo "${zoom}x  $(du -k "$png" | cut -f1)K  $png"
done
