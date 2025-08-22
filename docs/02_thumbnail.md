# サムネイル生成パイプライン

このドキュメントでは、ImageMagickを使用して動画のサムネイルを自動生成するパイプラインについて、その手法と具体的なコマンド例を解説します。

## 1. 環境構築

サムネイル生成には、`ImageMagick`と日本語フォントが必要です。
以下のスクリプトを実行することで、必要な依存関係を一度にインストールできます。

```bash
./scripts/setup_thumbnail_env.sh
```

このスクリプトは、Debian/Ubuntuベースの環境で`apt`を使用して依存関係をインストールします。

## 2. 生成フロー

サムネイルは、以下の2つの要素をメインに合成されます。

1.  **立ち絵**: `character.png`として生成された、背景透過済みのキャラクター画像。
2.  **日本語テキスト**: 動画タイトルや内容を元に、YouTubeの動画一覧で視聴者の目を引くよう、サムネイル専用に生成されたキャッチーなテキスト。

合成は、Linux CLI上でImageMagickの`convert`コマンドを駆使して行われます。

## 3. 主要なImageMagickの機能と手法

### テキストの自動折り返しと描画 (`caption:`)

ImageMagickでは、`caption:`プロトコルを使用することで、指定した横幅でテキストを自動的に折り返して画像化できます。これにより、長いタイトルでもサムネイルのレイアウトを崩さずに描画できます。

- **`size`**: テキストを描画する領域の最大幅と高さを指定します。
- **`caption:{テキスト}`**: ここに指定した文字列が、`size`の幅に合わせて自動で改行されます。
- **`font`**: `Noto-Sans-JP-Bold` のような、システムにインストールされた日本語フォントを指定します。
- **`pointsize`**: フォントのサイズを指定します。
- **`fill`**: 文字色を指定します。
- **`gravity`**: テキストの配置基準（中央揃えなど）を指定します。

### テキストの縁取り (`-stroke`, `-strokewidth`)

視認性を高めるため、テキストには縁取りを適用します。

- **`-stroke {色}`**: 縁の色を指定します。
- **`-strokewidth {幅}`**: 縁の太さをピクセル単位で指定します。
- **`-fill`** より前に `-stroke` と `-strokewidth` を指定することで、文字の輪郭を描画できます。

### 品質の圧縮とフォーマット指定 (`-quality`, `-format`)

YouTubeのサムネイルには2MBのサイズ制限があるため、適切な品質で圧縮する必要があります。

- **`-quality {0-100}`**: JPGの圧縮率を指定します。`85`あたりが品質とファイルサイズのバランスが良いとされます。
- **`-format jpg`**: 出力ファイル形式をJPGに指定します。

## 4. コマンド例

以下は、立ち絵 (`character.png`) と、サムネイル用に別途生成されたキャッチーなテキスト (`thumb_text.txt`) を合成するコマンドの一例です。

```bash
# 変数設定
CATCHY_TEXT=$(cat thumb_text.txt)
FONT_PATH="/usr/share/fonts/opentype/noto/NotoSansJP-Bold.ttf"
OUTPUT_THUMBNAIL="thumbnail.jpg"

# 1. テキストレイヤーを生成（白文字・黒縁）
convert \
  -background none \
  -size 1000x400 \
  -font "$FONT_PATH" \
  -pointsize 100 \
  -fill white \
  -stroke black \
  -strokewidth 5 \
  -gravity center \
  "caption:$CATCHY_TEXT" \
  text_layer.png

# 2. 立ち絵とテキストを合成
# まず1280x720の単色（例: 黒）のキャンバスを作成
convert -size 1280x720 xc:black \
  character.png -gravity center -composite \
  text_layer.png -gravity south -geometry +0+50 -composite \
  -quality 85 \
  "$OUTPUT_THUMBNAIL"

# 中間ファイルの削除
rm text_layer.png
```

## 5. 注意点

- **解像度**: 最終的な出力サムネイルの解像度は **1280x720** ピクセルに準拠する必要があります。
- **ファイル形式**: **JPG**形式で出力します。
- **ファイルサイズ**: **2MB**の制限を超えないように `-quality` オプションで調整が必要です。
- **フォント**: コマンドを実行する環境に、指定の日本語フォントがインストールされている必要があります。（`scripts/setup_thumbnail_env.sh` を参照）
- **座標指定**: `-geometry` オプションでの座標指定（例: `+50+100`）は、画像の左上からのオフセットです。レイアウトは試行錯誤して調整する必要があります。
