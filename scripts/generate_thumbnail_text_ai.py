#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import re
import subprocess
import sys

def main(issue_id, script_file):
    """
    AIを使用してサムネイルテキストを生成し、JSONファイルとして保存する。
    """
    prompt_file = "docs/02_thumbnail_prompt.md"
    output_dir = f"assets/issues/{issue_id}"
    output_file = os.path.join(output_dir, "thumbnail_text.json")

    # --- Validation ---
    if not issue_id:
        print("Error: Issue ID is required.", file=sys.stderr)
        sys.exit(1)
    if not script_file:
        print("Error: Script file path is required.", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(script_file):
        print(f"Error: Script file not found at '{script_file}'", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(prompt_file):
        print(f"Error: Prompt file not found at '{prompt_file}'", file=sys.stderr)
        sys.exit(1)

    # --- Main ---
    os.makedirs(output_dir, exist_ok=True)
    print(f"Generating thumbnail text for '{script_file}' using AI...")

    # プロンプトと台本の内容を読み込む
    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_content = f.read()
    with open(script_file, "r", encoding="utf-8") as f:
        script_content = f.read()

    # AIへの最終的な入力を組み立てる
    combined_prompt = f"{prompt_content}\n\n{script_content}"

    # Gemini CLIを呼び出す
    try:
        process = subprocess.run(
            ['gemini'],
            input=combined_prompt,
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True
        )
        raw_output = process.stdout
    except FileNotFoundError:
        print("Error: 'gemini' command not found. Make sure the Gemini CLI is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error executing Gemini CLI: {e}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    # AIの出力からJSON部分だけを抽出する
    cleaned_json = extract_json_from_text(raw_output)

    if not cleaned_json:
        print("Error: Could not extract valid JSON from the AI's output.", file=sys.stderr)
        print("--- Raw AI Output ---", file=sys.stderr)
        print(raw_output, file=sys.stderr)
        sys.exit(1)

    # JSONをファイルに書き込む
    try:
        # 一度Pythonオブジェクトに変換して、整形して書き出す
        json_data = json.loads(cleaned_json)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"Thumbnail text generated and saved to '{output_file}'")
    except json.JSONDecodeError:
        print("Error: The extracted content is not valid JSON.", file=sys.stderr)
        print("--- Extracted Content ---", file=sys.stderr)
        print(cleaned_json, file=sys.stderr)
        sys.exit(1)

    # --- Verification ---
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            json.load(f)
        print("JSON is valid. Generation complete.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Final JSON verification failed. {e}", file=sys.stderr)
        sys.exit(1)


def extract_json_from_text(text: str) -> str:
    """
    AIの出力からマークダウンのコードブロックに囲まれたJSON部分を抽出する。
    """
    # ```json ... ``` のパターンを探す
    match = re.search(r"```json\s*([\s\S]*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # もし上記パターンがなければ、[ から ] までを抽出する
    match = re.search(r"(\[[\s\S]*\])", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return ""


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/generate_thumbnail_text_ai.py <issue_id> <script_file>", file=sys.stderr)
        sys.exit(1)

    issue_id = sys.argv[1]
    script_file = sys.argv[2]
    main(issue_id, script_file)
