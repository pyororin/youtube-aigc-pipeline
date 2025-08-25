# サムネイル生成仕様

## 目次
- 概要
- デザイン方針
- 実装メモ
- サムネイル用テキスト生成仕様

---

このドキュメントは、YouTube動画のサムネイルを生成するためのデザイン原則と技術的仕様を定義します。

## 1. デザイン原則

### 1.1. 基本原則
- **Rule of Thirds（3分割構図）**の活用：画面を縦横それぞれ3分割のグリッドに見立て、視線の集中ポイント（交点）を利用するデザイン。
- **視線誘導と構図**：立ち絵の顔や目方向に沿って文言を配置し、自然に視線が文字へ流れる構図を意識。
- **ネガティブスペースの活用**：立ち絵の位置とは反対側に文言を配置し、余白を活かすことで要素を際立たせます。

### 1.2. テキスト配置パターン
- **パターンA**：立ち絵が右側に寄っている場合 → テキストは左上交点または左下交点に配置
- **パターンB**：立ち絵が左下寄りの場合 → テキストは右上交点に配置し、自然な視線移動を作る
- **いずれも**背景の余白部分を使い、文字と立ち絵が干渉しないバランスを重視

### 1.3. デザイン詳細ルール
- 文言は**2〜4語以内でインパクト重視**（例：「夜の公園」「君がそばに」など）
- フォントは**太字・サンセリフ系**／**高コントラスト背景か影付き**で可読性確保
- 携帯画面でも読み取りやすい**大きさ**と**配置の余裕**を考慮（モバイル視聴多数の傾向あり）

### 1.4. デザインチェックリスト
- 文言がRule of Thirdsの交点に近いか
- 立ち絵と文言が視覚的に干渉していないか
- 文言が3語以内で簡潔かつ読み取りやすいか
- フォント・色・背景とのコントラストが十分か
- 文言が人物の視線や顔の向きとのリンクを持っているか（視線誘導）

## 2. 技術仕様

### 2.1. 環境構築

サムネイル生成には、`ImageMagick`と日本語フォントが必要です。
以下のスクリプトを実行することで、必要な依存関係を一度にインストールできます。

```bash
./scripts/setup_thumbnail_env.sh
```

このスクリプトは、Debian/Ubuntuベースの環境で`apt`を使用して依存関係をインストールします。

### 2.2. 生成フロー

サムネイルは、以下の要素を**台本**の世界観や文脈に沿って合成することで生成されます。

1.  **立ち絵**: `character.png`として生成された、背景透過済みのキャラクター画像。
2.  **日本語テキスト**: 動画タイトルや内容を元に、YouTubeの動画一覧で視聴者の目を引くよう、サムネイル専用に生成されたキャッチーなテキスト。

合成は、Linux CLI上でImageMagickの`convert`コマンドを駆使して行われます。

### 2.3. 主要なImageMagickの機能と手法

#### テキストの自動折り返しと描画 (`caption:`)

ImageMagickでは、`caption:`プロトコルを使用することで、指定した横幅でテキストを自動的に折り返して画像化できます。これにより、長いタイトルでもサムネイルのレイアウトを崩さずに描画できます。

- **`size`**: テキストを描画する領域の最大幅と高さを指定します。
- **`caption:{テキスト}`**: ここに指定した文字列が、`size`の幅に合わせて自動で改行されます。
- **`font`**: `Noto-Sans-JP-Bold` のような、システムにインストールされた日本語フォントを指定します。
- **`pointsize`**: フォントのサイズを指定します。
- **`fill`**: 文字色を指定します。
- **`gravity`**: テキストの配置基準（中央揃えなど）を指定します。

#### テキストの縁取り (`-stroke`, `-strokewidth`)

視認性を高めるため、テキストには縁取りを適用します。

- **`-stroke {色}`**: 縁の色を指定します。
- **`-strokewidth {幅}`**: 縁の太さをピクセル単位で指定します。
- **`-fill`** より前に `-stroke` と `-strokewidth` を指定することで、文字の輪郭を描画できます。

#### 品質の圧縮とフォーマット指定 (`-quality`, `-format`)

YouTubeのサムネイルには2MBのサイズ制限があるため、適切な品質で圧縮する必要があります。

- **`-quality {0-100}`**: JPGの圧縮率を指定します。`85`あたりが品質とファイルサイズのバランスが良いとされます。
- **`-format jpg`**: 出力ファイル形式をJPGに指定します。

### 2.4. コマンド例

以下は、立ち絵 (`character.png`) と、`thumbnail_text.json` から取得した `serif_text` と `situation_text` を合成するコマンドの一例です。
この例では、`jq` を使ってJSONから値を抽出することを想定しています。

```bash
# --- 変数設定 ---
# thumbnail_text.json から、1番目のシーンの情報を取得
JSON_FILE="assets/issues/123/thumbnail_text.json" # サンプルパス
SERIF_TEXT=$(jq -r '.[0].serif_text' "$JSON_FILE")
SITUATION_TEXT=$(jq -r '.[0].situation_text' "$JSON_FILE")

# デザインやレイアウトに関する情報もJSONから取得できる
# この例では簡略化のため、一部の値を固定で設定
SERIF_COLOR=$(jq -r '.[0].layout.serif.color' "$JSON_FILE")
SERIF_STROKE_COLOR=$(jq -r '.[0].layout.serif.stroke.color' "$JSON_FILE")

FONT_PATH="/usr/share/fonts/opentype/noto/NotoSansJP-Bold.ttf"
OUTPUT_DIR="thumb"
OUTPUT_THUMBNAIL="${OUTPUT_DIR}/thumbnail.jpg"
BG_IMAGE="background.png" # 事前に用意した背景画像

# --- ディレクトリ作成 ---
mkdir -p "$OUTPUT_DIR"

# --- テキストレイヤー生成 ---

# 1. セリフテキストのレイヤーを生成
convert \
  -background none \
  -size 1000x300 \
  -font "$FONT_PATH" \
  -pointsize 110 \
  -fill "$SERIF_COLOR" \
  -stroke "$SERIF_STROKE_COLOR" \
  -strokewidth 6 \
  -gravity center \
  "caption:$SERIF_TEXT" \
  serif_layer.png

# 2. シチュエーションテキストのレイヤーを生成
convert \
  -background none \
  -size 800x200 \
  -font "$FONT_PATH" \
  -pointsize 50 \
  -fill white \
  -stroke black \
  -strokewidth 3 \
  -gravity center \
  "caption:$SITUATION_TEXT" \
  situation_layer.png

# --- 合成 ---

# 3. 背景、立ち絵、テキストレイヤーをすべて合成
convert -size 1280x720 "$BG_IMAGE" \
  character.png -gravity center -composite \
  serif_layer.png -gravity center -geometry +0-120 -composite \
  situation_layer.png -gravity south -geometry +0+80 -composite \
  -quality 85 \
  "$OUTPUT_THUMBNAIL"

# --- 中間ファイルの削除 ---
rm serif_layer.png situation_layer.png

echo "Thumbnail created at ${OUTPUT_THUMBNAIL}"
```

**注記:**
- 上記のコマンドは一例です。実際の `thumbnail_text.json` の内容（`position`, `size`など）に応じて、`-geometry` や `-pointsize` などのパラメータを動的に調整するスクリプトを組むことが理想的です。
- 背景画像 (`background.png`) は、動画の雰囲気に合わせて別途用意する必要があります。単色の背景を使用する場合は `xc:black` などに置き換えてください。

### 2.5. 技術的要件

- **出力先**: **`thumb/` ディレクトリ**に格納してください。
- **解像度**: 最終的な出力サムネイルの解像度は **1280x720** ピクセルに準拠する必要があります。
- **ファイル形式**: **JPG**形式で出力します。
- **ファイルサイズ**: **2MB**の制限を超えないように `-quality` オプションで調整が必要です。
- **フォント**: コマンドを実行する環境に、指定の日本語フォントがインストールされている必要があります。（`scripts/setup_thumbnail_env.sh` を参照）
- **座標指定**: `-geometry` オプションでの座標指定（例: `+50+100`）は、画像の左上からのオフセットです。レイアウトは試行錯誤して調整する必要があります。

### 2.6. サムネイルテキストの自動生成

サムネイル用のキャッチコピーは、`scripts/generate_thumbnail_text.sh` を使用して、台本から自動生成できます。
このスクリプトは、指定された台本（`.md`ファイル）を読み込み、LLM（Gemini）に問い合わせて、複数のサムネイルテキスト候補をJSON形式で出力します。

**実行方法:**

```bash
./scripts/generate_thumbnail_text.sh <issue_id> <path_to_script.md>
```

- **`<issue_id>`**: 生成物を格納するディレクトリ名（例: `123`）
- **`<path_to_script.md>`**: 読み込ませる台本ファイルのパス（例: `docs/01_workflow.md`）

**出力:**

実行後、`assets/issues/<issue_id>/thumbnail_text.json` に、`serif_text` や `situation_text` を含むJSONファイルが生成されます。
このJSONの内容を元に、デザイナーや次の合成工程でサムネイル画像が作成されます。

## 3. エージェントによるサムネイル生成ワークフロー

このセクションは、Julesエージェントがサムネイルを作成するためのステップバイステップのプロセスを概説します。

1.  **前提条件の確認:**
    -   対象Issueのキャラクター立ち絵 (`character.png`) が生成済みであることを確認します。
    -   テキスト生成の元となる台本ファイル (`script.txt`など) が存在することを確認します。

2.  **サムネイルテキストの生成:**
    -   `scripts/generate_thumbnail_text_ai.py` スクリプトを実行します。
    -   引数として `issue_id` と `script.txt` のパスを渡します。
    -   これにより `assets/issues/<issue_id>/thumbnail_text.json` が生成されます。

3.  **合成の準備:**
    -   生成された `thumbnail_text.json` を読み込み、テキスト、色、レイアウト情報を取得します。
    -   適切な背景を選択します。これは単色または事前に用意された背景画像です。テスト目的であれば、黒一色の背景で十分です。

4.  **ImageMagickコマンドの実行:**
    -   ImageMagickの `convert` コマンドを使い、各レイヤーを合成します。
    -   レイヤー構成: 背景、キャラクター立ち絵 (`character.png`)、そして1つ以上のテキストレイヤー。
    -   `thumbnail_text.json` の情報に基づき、テキスト内容、フォントサイズ、色、配置を動的に設定します。
    -   ガイダンスとして、セクション2.4のコマンド例を参照してください。

5.  **出力の検証:**
    -   最終的な画像が `assets/issues/<issue_id>/images/thumbnail.jpg` として保存されていることを確認します。
    -   解像度は 1280x720 である必要があります。
    -   ファイルサイズが 2MB 未満であることを確認します。

---

# サムネイルテキスト生成AIプロンプト

あなたは、プロの動画コンテンツプロデューサーです。
提供された台本を読み込み、視聴者の心をつかむ魅力的でクリックしたくなるようなサムネイルのテキスト案を複数生成してください。

## 指示

1.  **台本を深く理解する:**
    *   登場人物の関係性、感情の起伏、物語のクライマックスを正確に把握してください。
    *   特に、恋愛感情が動く瞬間、対立、感動的なセリフに注目してください。

2.  **3つのユニークなシーンを抽出する:**
    *   台本全体から、最も視聴者の興味を引くと思われる3つの異なるシーンを選び出してください。
    *   告白、嫉妬、感動的な約束、意味深な問いかけなど、感情が大きく動く部分を優先してください。

3.  **各シーンのテキストを生成する:**
    *   **セリフテキスト (`serif_text`):**
        *   シーンを象徴する、**相手役のキャラクターが話す**最も印象的なセリフを6〜16文字で抜き出してください。長すぎる場合は、核心を失わないように要約してください。
        *   視聴者が「どういうこと？」と続きが気になるような、インパクトのある部分を選んでください。
    *   **シチュエーションテキスト (`situation_text`):**
        *   セリフだけでは伝わらない状況や雰囲気を5〜10文字で補足してください。（例：「夜の公園で二人きり」「彼の部屋で」「突然の雨」）
        *   SFX（効果音）の記述も参考にしてください。

4.  **デザインとレイアウトを提案する:**
    *   各シーンの雰囲気に合わせて、最適なデザインを提案してください。
    *   `importance`（重要度）が3の場合は、中央に大きく、派手な色（赤など）を使って最も目立たせてください。
    *   `importance`が低い場合は、端に配置し、落ち着いた色を使ってください。
    *   可読性を最大限に高めるため、必ず縁取り（`stroke`）や影（`shadow`）を付けてください。

5.  **JSON形式で出力する:**
    *   以下の「JSON出力仕様」に厳密に従って、JSON配列形式で出力してください。
    *   JSON以外のテキスト（説明文、言い訳など）は一切含めないでください。

## JSON出力仕様

```json
[
  {
    "scene_title": "（シーンのタイトル）",
    "importance": "（1〜3の重要度）",
    "serif_text": "（抽出・要約したセリフ）",
    "situation_text": "（状況を補足するテキスト）",
    "layout": {
      "serif": {
        "position": "（center, top-left, bottom-rightなど）",
        "size": "（xl, l, m）",
        "color": "（#FFFFFFなど）",
        "font": "bold gothic",
        "stroke": { "color": "#000000", "width_px": "（整数）" }
      },
      "situation": {
        "position": "（center, top-left, bottom-rightなど）",
        "size": "（m, sm, xs）",
        "color": "（#FFEE58など）",
        "font": "handwriting",
        "stroke": { "color": "#000000", "width_px": "（整数）" }
      }
    },
    "notes": "（デザインの意図や補足事項）"
  }
]
```

---

## 良い出力例

```json
[
  {
    "scene_title": "夜の公園での告白",
    "importance": 3,
    "serif_text": "…君のことが、…好きだ。",
    "situation_text": "静かな水辺",
    "layout": {
      "serif": {
        "position": "center",
        "size": "xl",
        "color": "#E53935",
        "font": "bold gothic",
        "stroke": { "color": "#000000", "width_px": 6 }
      },
      "situation": {
        "position": "bottom-center",
        "size": "sm",
        "color": "#FFEE58",
        "font": "handwriting",
        "stroke": { "color": "#000000", "width_px": 3 }
      }
    },
    "notes": "最も重要な告白シーン。セリフを中央に大きく配置して強調。"
  },
  {
    "scene_title": "優しい気遣い",
    "importance": 2,
    "serif_text": "寒くないか？…これ、使えよ。",
    "situation_text": "ジャケットをかける音",
    "layout": {
      "serif": {
        "position": "top-left",
        "size": "l",
        "color": "#FFFFFF",
        "font": "bold gothic",
        "stroke": { "color": "#000000", "width_px": 5 }
      },
      "situation": {
        "position": "top-left",
        "size": "xs",
        "color": "#FFFFFF",
        "font": "handwriting",
        "stroke": { "color": "#000000", "width_px": 2 }
      }
    },
    "notes": "キャラクターの優しさが伝わるシーン。立ち絵の右側を想定した配置。"
  }
]
```

## 悪い出力例（このような出力は避けてください）

*   **JSON形式ではない:**
    `はい、承知いたしました。台本を分析し、最適なテキスト案を3つ作成しました。最初のシーンは...`
*   **セリフが長すぎる:**
    `"serif_text": "昼間は、ああいう騒がしい場所にいると、どうも落ち着かなくて…。君も、疲れただろ？　…悪かったな、急に連れ出して。"`
*   **レイアウト指定がない、または不完全:**
    `"layout": { "serif": { "position": "center" } }`

---

**以上の指示を厳守し、最高のサムネイルテキストを生成してください。**
**以下に台本を提示します。**
