# 立ち絵アセット（アニメ調キャラクター画像）作成仕様

## 1. 目的と概要
このドキュメントは、**立ち絵アセット（アニメ調キャラクター画像）**作成の仕様を定義します。
AI ツール（Gemini など）を活用し、高品質かつ一貫性のある立ち絵を生成するための設計ガイドです。

## 2. プロンプト設計のベストプラクティス（アニメ調立ち絵生成）

### 視覚要素の具体化
- **目**：大きく感情豊かな瞳、虹彩の輝き、ハイライト
- **髪**：長さ・質感（ストレート／ウェーブ／編み込み）、カラー（ナチュラル or 鮮やか）
- **表情**：優しい微笑・恥じらい・視線など、キャラクターの性格に応じた感情を
- **ポーズ**：肩から上中心、軽く見返す視線、手のしぐさなど演出を含む
- **衣装**：制服・カジュアル・ガーリースタイル、装飾やアクセの有無

### 画風・演出指定
- 清潔な線画／セルシェーディング
- 柔らかいグラデーション or パステル配色
- 照明：ソフトライティング or 夕暮れの暖色調、背景と調和するライティング

### 背景
- **透過PNG**：キャラクターを切り抜いて使用する場合。
- **単色またはぼかし背景**：背景をシンプルに演出する場合。
- **台本指定の背景**：台本やシーンの指示に基づき、具体的な背景を描画する場合。
- sfや自然などシーンとの差異を活かしたアレンジも可。

### 技術指標
- **アスペクト比**：1:1 正方形（例：2048×2048 px）
- **フォーマット**：PNG（背景が不要な場合は透過PNG）
- **メタデータ**：SynthID 等、AI生成識別メタ情報埋め込みの確認

## 3. 出力仕様・保存先
- **ファイル名**：`character.png` または `<キャラ名>_front.png` のように命名
- **保存パス**：`/assets/issues/<ISSUE-ID>/images/`
- **`metadata.json` に以下情報を記録**：
  ```json
  {
    "image": {
      "width": 2048,
      "height": 2048,
      "format": "png",
      "style": "anime-cell-shaded",
      "lighting": "soft",
      "character_prompt_summary": "<短いプロンプト要約>"
    }
  }
  ```

## 4. 自己チェック項目
- 画像サイズが正しいか（2048×2048 px、PNG形式）。
- 背景は指定通りか（透過・単色・台本指定など）、キャラクターを引き立てているか。
- キャラクターの目・表情・髪のディテールが明瞭であるか。
- SynthID が埋め込まれていること、または AI 生成の明記があるか。
- カラーバランスが崩れていないか（過剰な彩度や変な影がないか）。

## 5. プロンプト例（出力例）

### 背景ありの例
```
"Anime style half-body portrait, 20-year-old female senpai with soft brown wavy hair, large green sparkling eyes, warm smile, school uniform with ribbon, front-facing, cell-shaded, soft backlight, in a sunlit classroom, 2048x2048"
```

### 透過背景の例
```
"Anime style half-body portrait, 20-year-old female senpai with soft brown wavy hair, large green sparkling eyes, warm smile, school uniform with ribbon, front-facing, cell-shaded, soft backlight, plain white background, 2048x2048, transparent background"
```

## 6. 参考文献
- AI画像生成においては、Promptsの詳細度が品質を左右します。AI Art Revolution のガイドでは、目・髪・表情・lightingなどの指定が重要であるとされています。
- また、MidJourneyやStable Diffusionでのベストプラクティスでは、「シンプルかつ具体的な記述」で質の高い立ち絵が得られるとされています。
