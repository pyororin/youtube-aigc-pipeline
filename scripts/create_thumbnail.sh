#!/bin/bash

set -e

ISSUE_ID=$1
if [ -z "$ISSUE_ID" ]; then
  echo "Usage: $0 <issue_id>"
  exit 1
fi

# Paths
ASSETS_DIR="assets/issues/$ISSUE_ID"
IMAGE_DIR="$ASSETS_DIR/images"
THUMBNAIL_DIR="$ASSETS_DIR/thumbnail"
TEXT_FILE="$ASSETS_DIR/thumbnail_text.json"
CHARACTER_IMAGE="$IMAGE_DIR/Senpai_front.png"
OUTPUT_THUMBNAIL="$THUMBNAIL_DIR/thumbnail.jpg"

# Check if required files exist
if [ ! -f "$TEXT_FILE" ]; then
  echo "Error: Thumbnail text file not found at $TEXT_FILE"
  exit 1
fi
if [ ! -f "$CHARACTER_IMAGE" ]; then
  echo "Error: Character image not found at $CHARACTER_IMAGE"
  exit 1
fi

# Create output directory
mkdir -p "$THUMBNAIL_DIR"

# Parse JSON to get text and layout info
SERIF_TEXT=$(jq -r '.[0].serif_text' "$TEXT_FILE")
SITUATION_TEXT=$(jq -r '.[0].situation_text' "$TEXT_FILE")

SERIF_COLOR=$(jq -r '.[0].layout.serif.color' "$TEXT_FILE")
SERIF_STROKE_COLOR=$(jq -r '.[0].layout.serif.stroke.color' "$TEXT_FILE")
SITUATION_COLOR=$(jq -r '.[0].layout.situation.color' "$TEXT_FILE")
SITUATION_STROKE_COLOR=$(jq -r '.[0].layout.situation.stroke.color' "$TEXT_FILE")

# Font settings
FONT_BOLD="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc[0]"
FONT_HANDWRITING="/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc[0]" # Using Medium as a substitute for handwriting

# Create text layers
/usr/bin/convert \
  -background none \
  -size 1000x400 \
  -font "$FONT_BOLD" \
  -pointsize 120 \
  -fill "$SERIF_COLOR" \
  -stroke "$SERIF_STROKE_COLOR" \
  -strokewidth 6 \
  -gravity center \
  "caption:$SERIF_TEXT" \
  serif_text_layer.png

/usr/bin/convert \
  -background none \
  -size 1000x200 \
  -font "$FONT_HANDWRITING" \
  -pointsize 60 \
  -fill "$SITUATION_COLOR" \
  -stroke "$SITUATION_STROKE_COLOR" \
  -strokewidth 3 \
  -gravity center \
  "caption:$SITUATION_TEXT" \
  situation_text_layer.png

# Create a temporary transparent version of the character image
/usr/bin/convert "$CHARACTER_IMAGE" -transparent white temp_character.png

# Create base image and composite layers
/usr/bin/convert -size 1280x720 xc:black \
  temp_character.png -gravity center -geometry +0-50 -composite \
  serif_text_layer.png -gravity center -geometry +0+100 -composite \
  situation_text_layer.png -gravity south -geometry +0+50 -composite \
  -quality 85 \
  "$OUTPUT_THUMBNAIL"

# Clean up temporary transparent image
rm temp_character.png

# Clean up temporary files
rm serif_text_layer.png situation_text_layer.png

echo "Thumbnail created successfully at $OUTPUT_THUMBNAIL"
