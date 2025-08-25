#!/usr/bin/env bash
#
# サムネイル画像生成スクリプト
#
# このスクリプトは、指定されたIssue IDに基づき、事前に生成された
# `thumbnail_text.json` と `Senpai_front.png` を使用して、
# ImageMagickでサムネイル画像を合成します。
#
# 使い方:
# ./scripts/create_thumbnail_image.sh <ISSUE_ID>
#
# 例:
# ./scripts/create_thumbnail_image.sh 3
#
# 依存関係:
# - jq
# - ImageMagick (convertコマンド)
# - assets/issues/<ISSUE_ID>/thumbnail_text.json
# - assets/issues/<ISSUE_ID>/images/Senpai_front.png
#

set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <ISSUE_ID>"
  exit 1
fi

ISSUE_ID=$1
JSON_FILE="assets/issues/${ISSUE_ID}/thumbnail_text.json"
CHARACTER_IMAGE="assets/issues/${ISSUE_ID}/images/Senpai_front.png"
OUTPUT_DIR="assets/issues/${ISSUE_ID}/images"
OUTPUT_THUMBNAIL="${OUTPUT_DIR}/thumbnail.jpg"

# --- 1. Validation ---
if ! command -v jq &> /dev/null; then echo "jq not found"; exit 1; fi
if ! command -v convert &> /dev/null; then echo "convert (ImageMagick) not found"; exit 1; fi
if [ ! -f "$JSON_FILE" ]; then echo "JSON file not found: $JSON_FILE"; exit 1; fi
if [ ! -f "$CHARACTER_IMAGE" ]; then echo "Character image not found: $CHARACTER_IMAGE"; exit 1; fi

# --- 2. Extract data from JSON (using the first scene, importance=3) ---
SERIF_TEXT=$(jq -r '.[0].serif_text' "$JSON_FILE")
SITUATION_TEXT=$(jq -r '.[0].situation_text' "$JSON_FILE")
SERIF_COLOR=$(jq -r '.[0].layout.serif.color' "$JSON_FILE")
SERIF_STROKE_COLOR=$(jq -r '.[0].layout.serif.stroke.color' "$JSON_FILE")
SERIF_STROKE_WIDTH=$(jq -r '.[0].layout.serif.stroke.width_px' "$JSON_FILE")
SERIF_POS_RAW=$(jq -r '.[0].layout.serif.position' "$JSON_FILE")
SITUATION_COLOR=$(jq -r '.[0].layout.situation.color' "$JSON_FILE")
SITUATION_STROKE_COLOR=$(jq -r '.[0].layout.situation.stroke.color' "$JSON_FILE")
SITUATION_STROKE_WIDTH=$(jq -r '.[0].layout.situation.stroke.width_px' "$JSON_FILE")
SITUATION_POS_RAW=$(jq -r '.[0].layout.situation.position' "$JSON_FILE")

# Map positions to ImageMagick gravity values
map_gravity() {
  case "$1" in
    "center") echo "Center" ;;
    "top-left") echo "NorthWest" ;;
    "bottom-right") echo "SouthEast" ;;
    "bottom-center") echo "South" ;;
    *) echo "Center" ;; # Default to Center
  esac
}

SERIF_POS=$(map_gravity "$SERIF_POS_RAW")
SITUATION_POS=$(map_gravity "$SITUATION_POS_RAW")

# --- 3. Create Text Layers ---
echo "Creating text layers..."
FONT="Noto-Sans-CJK-JP-Bold"
convert \
  -background none -size 1000x300 -font "$FONT" -pointsize 100 \
  -fill "$SERIF_COLOR" -stroke "$SERIF_STROKE_COLOR" -strokewidth "$SERIF_STROKE_WIDTH" \
  -gravity center "caption:$SERIF_TEXT" serif_layer.png

convert \
  -background none -size 800x200 -font "$FONT" -pointsize 50 \
  -fill "$SITUATION_COLOR" -stroke "$SITUATION_STROKE_COLOR" -strokewidth "$SITUATION_STROKE_WIDTH" \
  -gravity center "caption:$SITUATION_TEXT" situation_layer.png

# --- 4. Composite Layers ---
echo "Compositing layers..."
# For the character, we need to resize it and place it. Let's place it in the center.
# The original is 2048x2048, let's make it fit in 720x720.
# Background is black.
convert -size 1280x720 xc:black \
  \( "$CHARACTER_IMAGE" -resize 720x720 \) -gravity center -composite \
  serif_layer.png -gravity "$SERIF_POS" -geometry +0-150 -composite \
  situation_layer.png -gravity "$SITUATION_POS" -geometry +0+250 -composite \
  -quality 85 "$OUTPUT_THUMBNAIL"

# --- 5. Cleanup ---
rm serif_layer.png situation_layer.png

echo "Thumbnail created at ${OUTPUT_THUMBNAIL}"
