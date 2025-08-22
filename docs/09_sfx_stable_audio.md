# 9. SFX生成（Stable Audio API）

## はじめに

本機能は、[Stable Audio](https://stableaudio.com/) の REST API を利用して、テキストプロンプトからSFX（効果音・環境音）を自動生成し、プロジェクトの `sfx/` ディレクトリに保存することを目的とします。

台本とは独立したSFX指示リスト（プロンプト集）を入力とし、一括で音声ファイルを生成することで、制作フローの効率化を図ります。

## 使い方

### 1. 初期セットアップ

まず、SFX生成用の環境をセットアップします。`scripts/` ディレクトリにあるセットアップスクリプトを実行してください。

```bash
bash scripts/setup_stable_audio.sh
```

このスクリプトは以下の処理を自動で行います。
- Python 3.10+ の仮想環境（`.venv/`）を作成
- 必要なライブラリ（`requests`, `pydub`）をインストール

### 2. APIキーの環境変数設定

スクリプトは、`STABILITY_API_KEY` という名前の環境変数からAPIキーを自動で読み込みます。
この環境変数を事前に設定してください。

例 (macOS/Linux):
```bash
export STABILITY_API_KEY="sk-..."
```

APIキーは [Stability AI Developer Platform](https://platform.stability.ai/account/keys) から取得できます。

### 3. プロンプトファイルの作成

生成したいSFXの指示を記述したテキストファイルを用意します。
ファイルは1行に1つのサウンドプロンプトを記述する形式です。

**入力ファイル例 (`/assets/issues/<ID>/sfx_prompts.txt`):**
```txt
雨が窓を打つ音、やや強め、室内からの距離感、ループ向け
ノートPCのキーボードタイピング、静か、近接
風が木の葉を揺らす音、穏やか、左右に軽く揺れる
```

### 4. SFX生成の実行

準備が整ったら、`sfx_generate_stable_audio.py` スクリプトを実行してSFXを生成します。

```bash
python scripts/sfx_generate_stable_audio.py --issue-id 00123 --prompts-file /assets/issues/00123/sfx_prompts.txt
```

生成された音声ファイルは `sfx/` ディレクトリに保存され、メタデータが `sfx/sfx_index.jsonl` に追記されます。

## プロンプト設計

高品質なSFXを生成するには、プロンプトの設計が重要です。Stable Audioの[公式ユーザーガイド](https://stableaudio.com/user-guide)で推奨されている構成に倣い、以下の要素を組み合わせることを推奨します。

- **音源の種類 (Source):** 何の音か (例: `Foley`, `Ambient sound`, `Drone`)
- **質感 (Texture):** 音の響きや素材感 (例: `soft`, `metallic`, `crisp`)
- **距離 (Distance):** 音源との距離 (例: `close-up`, `distant`)
- **動き (Movement):** 音の動きや変化 (例: `panning left to right`, `slowly fading out`)
- **収録環境 (Context):** 音が鳴っている場所 (例: `in a large hall`, `outdoors`)

**プロンプト例:**
- `Foley of footsteps on gravel, slow pace, close-up perspective`
- `Ambient sound of a quiet forest at night, with gentle wind and distant owl calls`
- `A deep, resonant drone with a slow, pulsating rhythm, ideal for a sci-fi scene`

スクリプトは日本語のプロンプトを英語に翻訳する機能も持ちますが（`--lang ja`）、より細かなニュアンスを反映したい場合は、最初から英語でプロンプトを記述することを推奨します。

## 推奨パラメータとデフォルト

APIリクエスト時に使用される主要なパラメータです。スクリプトの引数で上書きできますが、未指定の場合はスクリプト内に定義されたデフォルト値が使用されます。

- **duration_sec (`--duration`):** 生成する音声の長さ（秒）。BGMのような環境音は長め（15〜30秒）、効果音は短め（3〜10秒）が効果的です。
  - デフォルト: `12`
- **sample_rate:** サンプリングレート。Stable Audioの標準である `44100` Hzを推奨します。
  - デフォルト: `44100` (スクリプト内で固定)
- **format:** 出力フォーマット。編集耐性の高い `wav` を推奨します。
- **seed (`--seed`):** 乱数シード。同じシードと同じプロンプトでリクエストすると、同じ音声が再現されます。デバッグや再生成に便利です。
  - デフォルト: `None` (ランダム)

*注意: APIの仕様は更新される可能性があります。最新のパラメータ名は[公式APIリファレンス](https://platform.stability.ai/docs/api-reference)をご確認ください。*

## 命名規則と格納先

- **音声ファイル:**
  - すべて `sfx/` ディレクトリ直下に保存されます。
  - ファイル名は `sfx_<プロンプトの要約>_<連番>.wav` の形式で自動生成されます。（例: `sfx_rain_window_soft_01.wav`）
- **メタデータ:**
  - `sfx/sfx_index.jsonl` に、生成した音声ごとの情報（プロンプト、ファイル名、長さ、シード等）がJSONL形式で追記されます。

**`sfx_index.jsonl` のレコード例:**
```json
{"file": "sfx_rain_window_soft_01.wav", "prompt": "heavy rain hitting a window, close, loopable", "duration": 12, "seed": 123456789, "created_at": "2023-10-27T10:00:00Z"}
```

## 料金・クレジット・商用利用の注意

- **APIクレジット:**
  - APIの利用にはクレジットが必要です。消費量と残高は[Stability AI Developer Platform](https://platform.stability.ai/account/credits)で確認できます。
  - 無料クレジットの範囲を超えて利用する場合は、プランに応じた課金が発生します。
- **商用利用:**
  - Web版のStable Audioとはライセンス体系が異なる場合があります。API経由で生成した音声を商用プロジェクト（例: YouTube配信、ゲーム）で利用する場合は、契約しているプランの利用規約を必ずご確認ください。
- **Stable Audio Open:**
  - 短尺のSFX生成には、オープンソースで公開されている `Stable Audio Open` モデルをローカル環境で動かす選択肢もあります。こちらは商用利用の制約が比較的緩やかですが、本仕様の対象はSaaS版APIとします。

## トラブルシュート

- **`429 Too Many Requests`:**
  - APIのリクエスト制限に達した場合のエラーです。スクリプトは自動的に指数バックオフ（リトライ間隔を徐々に長くする）を行いますが、頻発する場合はリクエスト頻度を下げるか、プランの見直しを検討してください。
- **`5xx Server Error`:**
  - Stability AI側のサーバーで一時的な問題が発生している可能性があります。時間をおいて再試行してください。
- **タイムアウト:**
  - 長い音声の生成には時間がかかることがあります。`sfx_generate_stable_audio.py` のタイムアウト値（デフォルト120秒）を調整する必要があるかもしれません。
- **生成された音質が低い / ノイズが多い:**
  - プロンプトをより具体的に記述し直すことで改善される場合があります。
  - 同じプロンプトでも、`--seed` を変えて再生成すると全く違う結果が得られます。

## 参考リンク

- **公式ドキュメント:**
  - [Stable Audio User Guide](https://stableaudio.com/user-guide) - プロンプト設計のベストプラクティス
  - [Stability AI Developer Platform](https://platform.stability.ai/docs/getting-started) - API利用開始の手引き
  - [API Reference](https://platform.stability.ai/docs/api-reference) - エンドポイントとパラメータの詳細
- **その他:**
  - [Stable Audio 概要](https://stability.ai/stable-audio) - モデルの特長や `Stable Audio Open` について
