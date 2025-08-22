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
            "Accept": "audio/*",  # Request audio content
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

        data_payload = {
            "prompt": prompt_text,
            "duration": str(duration_sec),
            "format": "wav",
        }
        if seed:
            data_payload["seed"] = str(seed)

        # Format for multipart/form-data without sending filenames
        files_payload = {k: (None, v) for k, v in data_payload.items()}

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
                    files=files_payload,  # Send as multipart/form-data
                    timeout=180,
                )
                response.raise_for_status()

                # Success: response body is the raw audio data
                audio_data = response.content
                actual_seed = int(response.headers.get("seed", seed or 0))

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
                    pass # Keep the raw text if not JSON

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
        prompts = [line.strip() for line in f if line.strip()]

    for prompt in prompts:
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

            # Append metadata to index
            metadata = {
                "file": filename,
                "prompt": prompt,
                "duration": args.duration,
                "seed": final_seed,
                "sr": DEFAULT_SR,
                "issue_id": args.issue_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            with open(index_file, "a", encoding="utf-8") as idx:
                idx.write(json.dumps(metadata, ensure_ascii=False) + "\n")

        except Exception as e:
            logging.error(f"Could not process prompt '{prompt}'. Reason: {e}")
            # Continue to the next prompt

    logging.info("SFX generation process complete.")


if __name__ == "__main__":
    main()
