#!/bin/bash

set -euo pipefail

# This script generates thumbnail text suggestions using Gemini.
#
# Usage:
#   ./scripts/generate_thumbnail_text.sh <issue_id> <script_file>
#
# Args:
#   issue_id: The ID of the issue, used to determine the output directory.
#   script_file: The path to the script file (e.g., docs/01_workflow.md).

# --- Args ---
ISSUE_ID=$1
SCRIPT_FILE=$2
DOCS_FILE="docs/02_thumbnail.md"
OUTPUT_DIR="assets/issues/${ISSUE_ID}"
OUTPUT_FILE="${OUTPUT_DIR}/thumbnail_text.json"

# --- Validation ---
if [[ -z "$ISSUE_ID" ]]; then
  echo "Error: Issue ID is required." >&2
  exit 1
fi

if [[ -z "$SCRIPT_FILE" ]]; then
  echo "Error: Script file path is required." >&2
  exit 1
fi

if [[ ! -f "$SCRIPT_FILE" ]]; then
  echo "Error: Script file not found at '$SCRIPT_FILE'" >&2
  exit 1
fi

if [[ ! -f "$DOCS_FILE" ]]; then
  echo "Error: Docs file not found at '$DOCS_FILE'" >&2
  exit 1
fi

# --- Main ---

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "Generating thumbnail text for '$SCRIPT_FILE'..."

# Extract the prompt content from the docs file
PROMPT_CONTENT=$(awk '/^## 🎨 サムネイル用テキスト生成仕様/,0' "$DOCS_FILE")

if [[ -z "$PROMPT_CONTENT" ]]; then
    echo "Error: Could not extract prompt from '$DOCS_FILE'" >&2
    exit 1
fi

# Combine the main prompt and the script content
SCRIPT_CONTENT=$(cat "$SCRIPT_FILE")
COMBINED_PROMPT="${PROMPT_CONTENT}

---

# 台本

${SCRIPT_CONTENT}"

# Call the Gemini CLI
# The 'gemini' command is expected to be in the PATH
# The output is expected to be a JSON array, so we'll pipe it to the output file.
# The 'cat' command is used to pass the prompt via stdin to gemini.
# The prompt itself instructs the model to output JSON.
RAW_OUTPUT=$(cat <<< "$COMBINED_PROMPT" | gemini)

# Clean the output to extract only the JSON part.
# The output may contain extra lines and markdown code fences.
CLEANED_JSON=$(echo "$RAW_OUTPUT" | sed -n '/^```json$/,/^```$/p' | sed '1d;$d')

# If the above fails (e.g., no markdown fences), try to find the JSON array directly.
if [[ -z "$CLEANED_JSON" ]]; then
  CLEANED_JSON=$(echo "$RAW_OUTPUT" | sed -n '/^\[/,/^\]$/p')
fi


echo "$CLEANED_JSON" > "$OUTPUT_FILE"


echo "Thumbnail text generated and saved to '$OUTPUT_FILE'"

# --- Verification ---
# Check if the output file is valid JSON
if ! jq . "$OUTPUT_FILE" > /dev/null 2>&1; then
  echo "Error: The generated output is not valid JSON." >&2
  echo "--- Raw Output ---"
  echo "$RAW_OUTPUT"
  echo "--- Cleaned JSON ---"
  cat "$OUTPUT_FILE"
  exit 1
fi

echo "JSON is valid. Generation complete."
