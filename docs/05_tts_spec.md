# CoeFont Standard (tts_input_all.txt) 運用

このドキュメントでは、台本ファイル（`script.md`）から自動生成された `tts_input_all.txt` を使って、CoeFont で音声合成を行う手順について説明します。

## 概要

`tts_input_all.txt` は、台本からセリフのテキスト部分のみを抽出したファイルです。話者名（【...】）や特殊効果（SFX）、SSMLタグなどがすべて取り除かれているため、CoeFont のテキスト入力フィールドに直接コピー＆ペーストして使用できます。

この運用方法は、手作業によるセリフの転記ミスを防ぎ、効率的に音声合成を進めることを目的としています。

## 利用手順

### 1. tts_input_all.txt の生成

まず、以下のコマンドを実行して、`script.md` から `tts_input_all.txt` を生成します。

```bash
python3 scripts/tts_build_input_all.py --issue-id <ID>
```

- `<ID>` には、対象の `issue` 番号を指定してください。
- 実行後、`assets/issues/<ID>/text/tts_input_all.txt` にファイルが生成されます。

**例:**
```bash
python3 scripts/tts_build_input_all.py --issue-id 00123
```
出力: `assets/issues/00123/text/tts_input_all.txt`

### 2. CoeFont への貼り付けと音声合成

次に、生成された `tts_input_all.txt` の内容を CoeFont に読み込ませます。

1.  `tts_input_all.txt` をテキストエディタで開き、内容をすべてコピーします。
2.  CoeFont のプロジェクトを開き、テキスト入力フィールドにコピーした内容を貼り付けます。
3.  声種、速度、イントネーション、感情などのパラメータをUIで調整します。
4.  調整が完了したら、音声を書き出します（Export）。

**注意点:**
- 句読点（、。）によるポーズは、CoeFont 側の設定（例: 読点0.8秒、句点1.5秒）で自動的に適用されます。テキスト側で `<pause>` タグなどを追加する必要はありません。
- 1行が1つのセリフに対応しているため、CoeFont の「改行で分割」機能との相性が良いです。

### 3. 音声ファイルの確認と後続処理

書き出された音声ファイルを確認し、問題がなければ後続の `ffmpeg` 処理などに進みます。

もし、セリフの抽出内容に問題がある場合は、`scripts/tts_build_input_all.py` の抽出ロジック（鉤括弧「...」の処理）や、元の `script.md` の記述が正しいかを確認してください。

## （旧）manifest.jsonl 運用について

`manifest.jsonl` を用いた運用は、現在非推奨です。今後は `tts_input_all.txt` を使用してください。
