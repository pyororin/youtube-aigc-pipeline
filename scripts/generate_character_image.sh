#!/usr/bin/env bash
#
# 立ち絵画像生成スクリプト (REST API / Imagen 4 版)
#
# このスクリプトは、指定されたキャラクター情報と共通設定に基づき、
# Google の Imagen 4 モデルを REST API 経由で呼び出して立ち絵画像を生成します。
#
# 使い方:
# ./scripts/generate_character_image.sh <ISSUE_ID> "<キャラクター名>"
#
# 例:
# ./scripts/generate_character_image.sh 123 "Aoi Misaki"

set -euo pipefail

# --- 1. 引数のチェック ---
if [ "$#" -ne 2 ]; then
  echo "エラー: 不正な引数です。"
  echo "使い方: $0 <ISSUE_ID> \"<キャラクター名 (英語推奨)>\""
  exit 1
fi

ISSUE_ID=$1
# Imagen 4 は英語プロンプトを推奨するため、キャラクター名も英語表記を想定
CHARACTER_NAME=$2
CONFIG_FILE="config/common.yml"
OUTPUT_DIR="assets/issues/${ISSUE_ID}/images"
METADATA_FILE="assets/issues/${ISSUE_ID}/metadata.json"

# ファイル名用にスペースをアンダースコアに置換
IMAGE_NAME="${CHARACTER_NAME// /_}_front.png"
OUTPUT_PATH="${OUTPUT_DIR}/${IMAGE_NAME}"

# --- 2. 依存関係の確認 ---
if ! command -v curl &> /dev/null; then
  echo "エラー: curl コマンドが見つかりません。インストールしてください。" >&2
  exit 1
fi
if ! command -v jq &> /dev/null; then
  echo "エラー: jq コマンドが見つかりません。'brew install jq' などでインストールしてください。" >&2
  exit 1
fi
if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "エラー: 環境変数 GEMINI_API_KEY が設定されていません。" >&2
  exit 1
fi

echo "--- 立ち絵画像生成を開始します (Imagen 4 / REST API) ---"
echo "Issue ID: $ISSUE_ID"
echo "キャラクター名: $CHARACTER_NAME"
echo "----------------------------------------------------"

# --- 3. 出力ディレクトリの作成 ---
mkdir -p "$OUTPUT_DIR"
echo "出力ディレクトリを作成しました: $OUTPUT_DIR"

# --- 4. プロンプトの構築 ---
echo "設定ファイル (${CONFIG_FILE}) からプロンプトを構築します..."

get_config() {
  grep "^  $1:" "$CONFIG_FILE" | sed -e 's/.*: "//' -e 's/"$//'
}

STYLE=$(get_config "style")
LIGHTING=$(get_config "lighting")
COMPOSITION=$(get_config "composition")
OUTPUT_FORMAT=$(get_config "output_format")
BASE_EXPRESSION=$(grep "^    expression:" "$CONFIG_FILE" | sed -e 's/.*: "//' -e 's/"$//')
HAIR_STYLE="soft brown wavy hair"
OUTFIT="school uniform with a ribbon"

# Issue からの動的な指定（例：シーン情報）は、ここで英語に変換して結合する想定
# 例: SCENE_JP="日当たりの良い教室" -> SCENE_EN="in a sunlit classroom"
# ここでは固定値を使用
SCENE_EN="in a sunlit classroom"

# Imagen 4 向けに、すべての要素を結合した英語プロンプトを作成
PROMPT="A high-quality anime-style character illustration of '${CHARACTER_NAME}'. Details: ${BASE_EXPRESSION}, ${HAIR_STYLE}, wearing a ${OUTFIT}. Style: ${STYLE}. Composition: ${COMPOSITION}, ${SCENE_EN}. Lighting: ${LIGHTING}. Output format: ${OUTPUT_FORMAT}."

echo "生成用プロンプトを構築しました。"

# --- 5. Imagen 4 REST API を呼び出し ---
echo "Imagen 4 API を呼び出し、画像生成を実行します..."

MODEL_NAME="imagen-4.0-generate-001"
API_URL="https://generativelanguage.googleapis.com/v1beta/models/${MODEL_NAME}:predict"

# APIリクエストを実行し、レスポンスから base64 データを抽出
# jq で `.predictions[0].bytesBase64Encoded` を指定
BASE64_DATA=$(curl -s -X POST \
  "$API_URL" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
        \"instances\": [{\"prompt\": \"${PROMPT}\"}],
        \"parameters\": {\"sampleCount\": 1, \"aspectRatio\": \"1:1\"}
      }" \
| jq -r '.predictions[0].bytesBase64Encoded')

if [ -z "$BASE64_DATA" ] || [ "$BASE64_DATA" == "null" ]; then
  echo "エラー: Imagen 4 API から画像データを取得できませんでした。" >&2
  # 失敗した場合、APIからのレスポンス全体をログに出力するとデバッグしやすい
  # (ただし、キー情報や個人情報を含まないように注意)
  exit 1
fi

# --- 6. 画像をデコードしてファイルに保存 ---
echo "画像をデコードし、PNGファイルとして保存します..."
echo "$BASE64_DATA" | base64 --decode > "$OUTPUT_PATH"

if [ ! -s "$OUTPUT_PATH" ]; then
  echo "エラー: PNGファイルの保存に失敗しました。" >&2
  exit 1
fi

echo "画像の保存が完了しました: $OUTPUT_PATH"

# --- 7. metadata.json の更新 ---
echo "メタデータを ${METADATA_FILE} に追記します..."

if [ ! -f "$METADATA_FILE" ]; then
  echo "{}" > "$METADATA_FILE"
fi

jq \
  --argjson width 2048 \
  --argjson height 2048 \
  --arg format "png" \
  --arg model "$MODEL_NAME" \
  --arg prompt_summary "${CHARACTER_NAME}, ${STYLE}" \
  --arg lighting "$(get_config "lighting")" \
  '.image = {
    "width": $width,
    "height": $height,
    "format": $format,
    "model": $model,
    "style": "anime-cell-shaded",
    "lighting": $lighting,
    "prompt_summary": $prompt_summary
  }' \
  "$METADATA_FILE" > "${METADATA_FILE}.tmp" && mv "${METADATA_FILE}.tmp" "$METADATA_FILE"

echo "メタデータの更新が完了しました。"
echo "--- 全ての処理が正常に完了しました ---"
