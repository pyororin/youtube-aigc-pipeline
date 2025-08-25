import os
import sys
import json
import time
import argparse
import logging
import re
import base64
from datetime import datetime
from pathlib import Path

import requests

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# --- Main Generation Class ---
class SfxGenerator:
    """
    Generates SFX using the Stable Audio v2beta Text-to-Audio API.
    """

    def __init__(self, api_key: str, base_url: str):
        if not api_key:
            raise ValueError("STABILITY_API_KEY cannot be empty.")
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        self.api_endpoint = f"{self.base_url}/v2beta/audio/stable-audio-2/text-to-audio"

    def _translate_prompt(self, prompt_text: str) -> str:
        """
        Placeholder for Japanese to English translation.
        For now, it returns the original text with a warning.
        """
        # TODO: Implement actual translation if required, e.g., using a translation API.
        logging.warning(
            "Language is set to 'ja' but translation is not implemented. "
            "Using the original Japanese prompt. For best results, use English prompts."
        )
        return prompt_text

    def _generate_filename(self, prompt: str, outdir: Path) -> str:
        """
        Generates a sanitized, unique filename from the prompt.
        Example: "rain_window_soft_01.wav"
        """
        # Sanitize prompt into a short description
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", prompt.lower())
        sanitized = re.sub(r"_+", "_", sanitized).strip("_")
        base_name = "_".join(sanitized.split("_")[:4]) # Use first 4 words

        # Find the next available sequence number
        i = 1
        while True:
            filename = f"{base_name}_{i:02d}.wav"
            if not (outdir / filename).exists():
                return filename
            i += 1

    def generate(
        self,
        prompt_text: str,
        duration_sec: int,
        seed: int = None,
        lang: str = "en",
    ) -> tuple[bytes, int]:
        """
        Makes a request to the Stable Audio v2beta Text-to-Audio API to generate audio.
        Implements exponential backoff for retries.
        Returns audio data as binary and seed as int.
        """
        if lang == "ja":
            prompt_text = self._translate_prompt(prompt_text)

        files = {
            'prompt': (None, prompt_text),
            'duration': (None, str(duration_sec)),
            'format': (None, 'wav'),
        }
        if seed:
            files['seed'] = (None, str(seed))

        max_retries = 5
        base_delay = 2
        for attempt in range(max_retries):
            try:
                logging.info(
                    f"Requesting audio from Stable Audio v2beta Text-to-Audio API: "
                    f"'{prompt_text}' (duration: {duration_sec}s)"
                )
                response = requests.post(
                    self.api_endpoint,
                    headers=self.headers,
                    files=files,
                    timeout=180,
                )
                response.raise_for_status()

                # Success: response body is JSON with base64 audio
                response_json = response.json()
                audio_data = base64.b64decode(response_json["audio"])
                actual_seed = response_json.get("seed", seed or 0)

                logging.info(f"Successfully generated audio with seed: {actual_seed}")
                return audio_data, actual_seed

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                error_message = e.response.text
                try:
                    # Try to parse JSON error for better logging
                    error_json = e.response.json()
                    error_message = json.dumps(error_json)
                except json.JSONDecodeError:
                    pass  # Keep the raw text if not JSON

                if status_code == 404:
                    logging.error(
                        f"HTTP 404 Not Found: The API endpoint path may be incorrect. "
                        f"Please check the URL: {self.api_endpoint}"
                    )
                    raise  # No retry for 404
                elif status_code == 429 or status_code >= 500:
                    delay = base_delay * (2**attempt)
                    logging.warning(
                        f"Received status {status_code}. Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                else:
                    logging.error(f"HTTP Error: {error_message}")
                    raise
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed: {e}")
                raise

        raise Exception(
            f"Failed to generate audio for prompt '{prompt_text}' after {max_retries} retries."
        )


def main():
    """Main function to parse arguments and run the generation process."""
    # --- Configuration Constants ---
    BASE_URL = "https://api.stability.ai"
    DEFAULT_DURATION = 12
    DEFAULT_SR = 44100

    parser = argparse.ArgumentParser(description="Generate SFX using Stable Audio API.")
    parser.add_argument("--issue-id", type=str, help="Issue ID for metadata.")
    parser.add_argument(
        "--prompts-file",
        type=str,
        help="Path to a text file with one prompt per line.",
        required=True
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="sfx",
        help="Directory to save the generated SFX files and index.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION,
        help="Duration of the audio in seconds.",
    )
    parser.add_argument("--seed", type=int, help="Seed for reproducibility.")
    parser.add_argument(
        "--lang",
        choices=["ja", "en"],
        default="ja",
        help="Language of the prompts ('ja' for Japanese, 'en' for English).",
    )
    parser.add_argument(
        "--max-sfx",
        type=int,
        default=5,
        help="Maximum number of SFX to generate per run (default: 5).",
    )

    args = parser.parse_args()

    # --- Setup ---
    api_key = os.environ.get("STABILITY_API_KEY")
    if not api_key:
        logging.error("STABILITY_API_KEY environment variable not found.")
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(exist_ok=True)

    prompts_file = Path(args.prompts_file)
    if not prompts_file.is_file():
        logging.error(f"Prompts file not found at: {prompts_file}")
        sys.exit(1)

    index_file = outdir / "sfx_index.jsonl"

    generator = SfxGenerator(api_key=api_key, base_url=BASE_URL)

    # --- Process Prompts ---
    with open(prompts_file, "r", encoding="utf-8") as f:
        all_prompts = [line.strip() for line in f if line.strip()]

    sfx_total_in_script = len(all_prompts)
    sfx_limit = args.max_sfx
    prompts_to_process = all_prompts[:sfx_limit]
    sfx_generated_count = len(prompts_to_process)
    sfx_skipped_count = sfx_total_in_script - sfx_generated_count

    if sfx_total_in_script > sfx_limit:
        logging.warning(
            f"prompts-file には {sfx_total_in_script} 件ありますが、上限 {sfx_limit} 件のみ生成します"
            f"（残り {sfx_skipped_count} 件はスキップ）。"
        )

    if sfx_generated_count == 0:
        logging.error("制限適用後に処理対象のプロンプトが 0 件になりました。")
        sys.exit(1)

    generated_metadata = []
    for prompt in prompts_to_process:
        try:
            audio_data, final_seed = generator.generate(
                prompt_text=prompt,
                duration_sec=args.duration,
                seed=args.seed,
                lang=args.lang,
            )

            # Save audio file
            filename = generator._generate_filename(prompt, outdir)
            filepath = outdir / filename
            with open(filepath, "wb") as wav_file:
                wav_file.write(audio_data)
            logging.info(f"Saved audio to {filepath}")

            # Store metadata for later
            metadata = {
                "file": filename,
                "prompt": prompt,
                "duration": args.duration,
                "seed": final_seed,
                "sr": DEFAULT_SR,
                "issue_id": args.issue_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            generated_metadata.append(metadata)

        except Exception as e:
            logging.error(f"Could not process prompt '{prompt}'. Reason: {e}")
            # Continue to the next prompt

    # --- Write Metadata ---
    if generated_metadata:
        run_summary = {
            "type": "run_summary",
            "prompts_file": str(prompts_file),
            "sfx_limit": sfx_limit,
            "sfx_total_in_script": sfx_total_in_script,
            "sfx_generated": len(generated_metadata),
            "sfx_skipped": sfx_total_in_script - len(generated_metadata),
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        old_content = ""
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                old_content = f.read()

        with open(index_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(run_summary, ensure_ascii=False) + "\n")
            for metadata in generated_metadata:
                f.write(json.dumps(metadata, ensure_ascii=False) + "\n")
            if old_content:
                f.write(old_content)

    logging.info("SFX generation process complete.")


if __name__ == "__main__":
    main()
