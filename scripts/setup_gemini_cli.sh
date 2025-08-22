#!/usr/bin/env bash
#
# Gemini CLI 自動セットアップスクリプト (エージェント実行用)
#
# このスクリプトは、エージェント (Jules) が実行し、Gemini CLI 環境を
# 自動でセットアップすることを目的とします。
#
# 実行内容:
# 1. Node.js v20+ の存在確認
# 2. npm を使用した @google/gemini-cli のグローバルインストール
# 3. GEMINI_API_KEY 環境変数の存在確認
# 4. インストール後の gemini コマンドの動作確認

set -euo pipefail

echo "--- Gemini CLI 自動セットアップ開始 ---"

# --- 1. Node.js バージョン確認 ---
echo "[1/4] Node.js バージョンを確認中..."
if ! command -v node &> /dev/null; then
  echo "エラー: Node.js がインストールされていません。" >&2
  exit 1
fi

NODE_VERSION=$(node -v)
MAJOR_VERSION=$(echo "$NODE_VERSION" | sed 's/v//' | cut -d. -f1)

if [ "$MAJOR_VERSION" -lt 20 ]; then
  echo "エラー: Node.js v20 以上が必要です。(現在: $NODE_VERSION)" >&2
  exit 1
fi
echo "Node.js バージョンOK: $NODE_VERSION"

# --- 2. Gemini CLI のインストール ---
echo "[2/4] npm を使用して @google/gemini-cli をグローバルにインストール中..."
if ! npm install -g @google/gemini-cli; then
  echo "エラー: Gemini CLI のインストールに失敗しました。" >&2
  exit 1
fi
echo "Gemini CLI のインストールが完了しました。"

# --- 3. 認証情報の確認 ---
echo "[3/4] GEMINI_API_KEY の存在を確認中..."
if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "エラー: 環境変数 GEMINI_API_KEY が設定されていません。" >&2
  echo "APIキー認証が必要です。" >&2
  exit 1
fi
echo "GEMINI_API_KEY が設定されています。"

# --- 4. 動作確認 ---
echo "[4/4] gemini コマンドの動作を確認中..."
if ! gemini --version; then
  echo "エラー: gemini コマンドの実行に失敗しました。" >&2
  echo "パスが通っているか、インストールが正常に完了したか確認してください。" >&2
  exit 1
fi

echo "--- Gemini CLI のセットアップが正常に完了しました ---"
