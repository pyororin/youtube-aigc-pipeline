# 立ち絵アセット（アニメ調キャラクター画像）作成仕様

## 1. 目的
本ドキュメントは、**立ち絵アセット（アニメ調キャラクター画像）**作成の標準的なフローを定義します。
**Gemini API** を **Gemini CLI** 経由で利用し、高品質かつ一貫性のある立ち絵を効率的に生成することを目的とします。

生成プロセスは `scripts/` 配下のシェルスクリプトに集約されており、手動でのコマンド実行を不要にします。

## 2. 前提・要件

### 必須環境
- **OS**: macOS または Linux (Windows は WSL2 を推奨)
- **Node.js**: `20` 以上のバージョン
- **認証**: Google アカウント (OAuth) または Gemini API キー

### 生成画像の仕様
- **解像度**: 2048×2048 ピクセル（正方形）を推奨
- **形式**: PNG（背景透過を推奨）
- **ファイル名**: `<キャラ名>_front.png` (例: `aoi_misaki_front.png`)
- **出力先**: `/assets/issues/<ISSUE-ID>/images/`
- **AI生成の明記**: 生成された画像には、Google の **SynthID** によって電子透かしが自動的に埋め込まれます。これは、AI によって生成されたコンテンツであることを示すためのものです。

### メタデータ
画像生成に成功すると、`/assets/issues/<ISSUE-ID>/metadata.json` に以下の情報が自動的に追記されます。
```json
{
  "image": {
    "width": 2048,
    "height": 2048,
    "format": "png",
    "style": "anime-cell-shaded",
    "lighting": "soft backlight",
    "prompt_summary": "<キャラクター名>, anime style, front-facing"
  }
}
```

## 3. 実行フロー
立ち絵の生成は、以下のスクリプトを実行することで行います。

### Step 1: 環境セットアップ (エージェント担当)
画像生成に必要な `Gemini CLI` のインストールと認証は、担当エージェント (Jules) が自動的に行います。
ユーザーが手動でセットアップ作業を行う必要はありません。

### Step 2: 画像生成 (ユーザー/エージェント担当)
`scripts/generate_character_image.sh` を実行し、プロンプトに基づいた立ち絵を生成します。
```bash
# ISSUE-ID とキャラクター名を指定して実行
./scripts/generate_character_image.sh <ISSUE-ID> "<キャラクター名>"
```
このスクリプトは、引数で受け取った情報と `config/common.yml` に定義された共通設定を組み合わせてプロンプトを動的に構築し、**Gemini CLI を非対話モードで呼び出し**ます。
成功すると、base64形式の画像レスポンスをデコードし、指定のパスにPNGとして保存後、`metadata.json` を更新します。

## 4. プロンプト設計
プロンプトは、`generate_character_image.sh` スクリプト内で組み立てられます。ベースとなるプロンプトの設計指針は以下の通りです。

- **画風**: `anime`, `cell-shaded`, `clean line` などを指定。
- **顔・表情**: 大きな瞳、柔らかい微笑み、視線の向きなど、キャラクターの性格を反映。
- **髪**: 長さ、色、質感（例: `soft brown wavy hair`）。
- **衣装**: Issue で指定された制服や私服を反映。
- **ライティング**: `soft backlight`, `pastel tone` などで雰囲気作り。
- **構図**: `上半身 (upper body)`, `正面向き (front-facing)`, `均等な余白 (even margins)`。
- **出力形式**: `2048x2048`, `PNG`, `transparent background`（背景透過）。

**プロンプト例（スクリプト内で使用される文章の例）:**
> 「セル調のアニメ立ち絵、キャラクター名「<名前>」、20代前半、柔らかな表情、大きな緑色の瞳、ソフトブラウンのウェーブヘア。白いブラウスと青いスカートの制服を着用。上半身の構図で、ライティングは柔らかい逆光。2048×2048ピクセルのPNG形式で、背景は透過。」

## 5. 自己チェックリスト
生成後は、以下の項目を必ず確認してください。

- [ ] `scripts/setup_gemini_cli.sh` によるセットアップは完了しているか？
- [ ] 画像の仕様（2048x2048, PNG, 透過背景）を満たしているか？
- [ ] ファイルサイズは適切か？（過度に大きくないか）
- [ ] `metadata.json` への追記は正しく行われているか？
- [ ] AI生成である旨の表記（SynthID）について理解しているか？
- [ ] 生成に失敗した場合、スクリプトのログを確認し、再実行の手順を理解しているか？

## 6. PR（Pull Request）本文テンプレート
```markdown
## 立ち絵生成 概要
- **キャラ**: <Issue指定名>
- **スタイル**: anime / セル調 / soft backlight
- **解像度/形式**: 2048×2048 / PNG（透過）
- **実行方法**: Gemini CLI（非対話モード）を利用。プロンプトは Issue 情報 + `common.yml` から構成。
- **保存先**: `/assets/issues/<ISSUE-ID>/images/<キャラ名>_front.png`
- **備考**: SynthID（自動埋め込み）、メタデータ (`metadata.json`) 更新済み。
```

---
## 脚注・出典
- **Gemini CLI 公式リポジトリ (GitHub)**
  [https://github.com/google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli)
- **Gemini API: 画像生成ドキュメント**
  [https://ai.google.dev/gemini-api/docs/image-generation?hl=ja](https://ai.google.dev/gemini-api/docs/image-generation?hl=ja)
- **SynthID (DeepMind) 概要**
  [https://deepmind.google/science/synthid/](https://deepmind.google/science/synthid/)
