# 立ち絵アセット（アニメ調キャラクター画像）作成仕様

## 1. 目的
本ドキュメントは、**立ち絵アセット（アニメ調キャラクター画像）**作成の標準的なフローを定義します。
Google の画像生成モデル **Imagen 4** を **REST API** 経由で直接利用し、高品質かつ安定した立ち絵生成を行うことを目的とします。

## 2. 前提・要件

### 必須環境
- **cURL**, **jq**: API通信とレスポンス解析のために必要です。
- **認証**: `GEMINI_API_KEY` 環境変数に有効な API キーが設定されていること。
- **その他**: `setup_gemini_cli.sh` は、CLIを利用する他タスクのために残置しますが、本画像生成フローでは直接使用しません。

### 生成画像の仕様
- **解像度**: 2048×2048 ピクセル（`aspectRatio: "1:1"` で指定）
- **形式**: PNG（背景透過プロンプトを推奨）
- **ファイル名**: `<キャラ名>_front.png` (例: `Aoi_Misaki_front.png`)
- **出力先**: `/assets/issues/<ISSUE-ID>/images/`
- **AI生成の明記**: 生成された画像には、Google の **SynthID** によって電子透かしが自動的に埋め込まれます。

### メタデータ
画像生成に成功すると、`/assets/issues/<ISSUE-ID>/metadata.json` に以下の情報が自動的に追記されます。
```json
{
  "image": {
    "width": 2048,
    "height": 2048,
    "format": "png",
    "model": "imagen-4.0-generate-001",
    "style": "anime-cell-shaded",
    "lighting": "soft backlight",
    "prompt_summary": "Aoi Misaki, anime, cell-shaded, clean line, high quality"
  }
}
```

## 3. 実行フロー
立ち絵の生成は、`scripts/generate_character_image.sh` を実行することで行います。

```bash
# ISSUE-ID とキャラクター名（英語推奨）を指定して実行
./scripts/generate_character_image.sh <ISSUE-ID> "<Character_Name>"
```
このスクリプトは、内部で **Imagen 4 の REST API** を `curl` で直接呼び出します。
プロンプトは、引数と `config/common.yml` の設定を基に動的に構築されます。

## 4. プロンプト設計
プロンプトは `generate_character_image.sh` スクリプト内で組み立てられます。

### 基本方針
- **英語推奨**: Imagen 4 モデルは英語プロンプトで最も性能を発揮します。キャラクター名やシーンの指定など、動的な要素はスクリプト内で英語に変換するか、初めから英語で入力することが推奨されます。
- **具体的かつ詳細に**: 画風、表情、髪、衣装、構図、ライティング、背景などを具体的に記述します。

**プロンプト例（スクリプト内で生成される文字列の例）:**
> "A high-quality anime-style character illustration of 'Aoi Misaki'. Details: soft smile, gentle expression, soft brown wavy hair, wearing a school uniform with a ribbon. Style: anime, cell-shaded, clean line, high quality. Composition: upper body, front-facing, even margins, in a sunlit classroom. Lighting: soft backlight, pastel tone. Output format: 2048x2048, PNG, transparent background."

## 5. 自己チェックリスト
- [ ] `GEMINI_API_KEY` は正しく設定されているか？
- [ ] `curl` と `jq` はインストールされているか？
- [ ] 画像の仕様（解像度, 形式, 透過）を満たしているか？
- [ ] `metadata.json` への追記は正しく行われているか？
- [ ] プロンプトは英語で記述されているか？
- [ ] SynthID が埋め込まれる仕様を理解しているか？

## 6. (参考) その他の技術的選択肢

### Gemini CLI を利用する場合 (MCPブリッジ)
どうしても Gemini CLI を利用したい場合、CLI の関数呼び出し機能と画像生成APIを仲介する **MCP (Model Context Protocol) サーバー**を別途構築する方法があります。これにより、CLIから間接的に Imagen モデルを呼び出すことが可能になります。
この方法は設定が複雑なため、本プロジェクトではREST APIを標準とします。

---
## 脚注・出典
- **Gemini API: 画像生成ドキュメント**
  [https://ai.google.dev/gemini-api/docs/image-generation?hl=ja](https://ai.google.dev/gemini-api/docs/image-generation?hl=ja)
- **SynthID (DeepMind) 概要**
  [https://deepmind.google/science/synthid/](https://deepmind.google/science/synthid/)
