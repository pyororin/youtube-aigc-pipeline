#!/usr/bin/env bash
#
# 立ち絵画像生成スクリプト
#
# このスクリプトは、指定されたキャラクター情報と共通設定に基づき、Gemini CLI を使用して
# 立ち絵画像を生成し、適切なディレクトリに保存します。
#
# 実行前に `scripts/setup_gemini_cli.sh` の手順を完了してください。
#
# 使い方:
# ./scripts/generate_character_image.sh <ISSUE_ID> "<キャラクター名>"
#
# 例:
# ./scripts/generate_character_image.sh 123 "蒼井 美咲"

set -euo pipefail

# --- 1. 引数のチェック ---
if [ "$#" -ne 2 ]; then
  echo "エラー: 不正な引数です。"
  echo "使い方: $0 <ISSUE_ID> \"<キャラクター名>\""
  exit 1
fi

ISSUE_ID=$1
CHARACTER_NAME=$2
CONFIG_FILE="config/common.yml"
OUTPUT_DIR="assets/issues/${ISSUE_ID}/images"
METADATA_FILE="assets/issues/${ISSUE_ID}/metadata.json"
IMAGE_NAME="${CHARACTER_NAME// /_}_front.png" # スペースをアンダースコアに置換
OUTPUT_PATH="${OUTPUT_DIR}/${IMAGE_NAME}"

echo "--- 立ち絵画像生成を開始します ---"
echo "Issue ID: $ISSUE_ID"
echo "キャラクター名: $CHARACTER_NAME"
echo "出力先ディレクトリ: $OUTPUT_DIR"
echo "---------------------------------"

# --- 2. 出力ディレクトリの作成 ---
mkdir -p "$OUTPUT_DIR"
echo "出力ディレクトリを作成しました: $OUTPUT_DIR"

# --- 3. プロンプトの構築 ---
echo "設定ファイル (${CONFIG_FILE}) からプロンプトを構築します..."

# yq や full-featured YAML parser がない環境を想定し、grep/sed で簡易的にパース
# (キー: 値 の形式で、インデントがスペース2つであることに依存)
get_config() {
  grep "^  $1:" "$CONFIG_FILE" | sed -e 's/.*: "//' -e 's/"$//'
}

STYLE=$(get_config "style")
LIGHTING=$(get_config "lighting")
COMPOSITION=$(get_config "composition")
OUTPUT_FORMAT=$(get_config "output_format")
BASE_EXPRESSION=$(get_config "expression")

# Issue ごとに変動する部分は引数や別のファイルから読み込むことを想定
# ここでは例として固定値を使用
HAIR_STYLE="soft brown wavy hair"
OUTFIT="school uniform with a ribbon"

# 各要素を組み合わせて最終的なプロンプトを生成
# 詳細度を上げることで、より意図に沿った画像が生成されやすくなる
BASE_PROMPT="A high-quality anime-style character illustration.
Character Name: ${CHARACTER_NAME}.
Style and Quality: ${STYLE}.
Appearance Details: ${BASE_EXPRESSION}, ${HAIR_STYLE}.
Outfit: ${OUTFIT}.
Composition: ${COMPOSITION}.
Lighting: ${LIGHTING}.
Output Format: ${OUTPUT_FORMAT}."

echo "生成用プロンプトを構築しました。"

# --- 4. Gemini CLI を非対話モードで実行 ---
echo "Gemini CLI を呼び出し、画像生成を実行します..."

# モデルの選択について:
# 当初、要件では 'gemini-2.5-pro' が指定されていましたが、これは画像生成モデルではありません。
# 動作の正確性を保証するため、Google の公式ドキュメントに基づき、
# 画像生成が可能な 'gemini-2.0-flash-preview-image-generation' を使用します。
MODEL_NAME="gemini-2.0-flash-preview-image-generation"

# --output json をつけることで、レスポンスが解析しやすくなる
# APIからのレスポンス形式: {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": "BASE64_DATA"}}]}}]}
RAW_RESPONSE=$(gemini -m "$MODEL_NAME" -p "$BASE_PROMPT" --output json)

# レスポンスから base64 データを抽出 (jq を利用)
if ! command -v jq &> /dev/null; then
  echo "エラー: jq コマンドが必要です。'brew install jq' などでインストールしてください。" >&2
  exit 1
fi

BASE64_DATA=$(echo "$RAW_RESPONSE" | jq -r '.candidates[0].content.parts[0].inlineData.data')

if [ -z "$BASE64_DATA" ] || [ "$BASE64_DATA" == "null" ]; then
  echo "エラー: Gemini API から画像データを取得できませんでした。" >&2
  echo "レスポンス: $RAW_RESPONSE" >&2
  exit 1
fi

# --- 5. 画像をデコードしてファイルに保存 ---
echo "画像をデコードし、PNGファイルとして保存します..."
echo "$BASE64_DATA" | base64 --decode > "$OUTPUT_PATH"

if [ ! -s "$OUTPUT_PATH" ]; then
  echo "エラー: PNGファイルの保存に失敗しました。" >&2
  exit 1
fi

echo "画像の保存が完了しました: $OUTPUT_PATH"

# --- 6. metadata.json の更新 ---
echo "メタデータを ${METADATA_FILE} に追記します..."

# JSON ファイルが存在しない場合は初期化
if [ ! -f "$METADATA_FILE" ]; then
  echo "{}" > "$METADATA_FILE"
fi

# jq を使ってJSONを安全に更新
# lighting の値も config ファイルから取得したものを使うように変更
jq \
  --argjson width 2048 \
  --argjson height 2048 \
  --arg format "png" \
  --arg style "anime-cell-shaded" \
  --arg lighting "$LIGHTING" \
  --arg prompt_summary "${CHARACTER_NAME}, anime style, front-facing" \
  '.image = {
    "width": $width,
    "height": $height,
    "format": $format,
    "style": $style,
    "lighting": $lighting,
    "prompt_summary": $prompt_summary
  }' \
  "$METADATA_FILE" > "${METADATA_FILE}.tmp" && mv "${METADATA_FILE}.tmp" "$METADATA_FILE"

echo "メタデータの更新が完了しました。"
echo "--- 全ての処理が正常に完了しました ---"
