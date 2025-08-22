import os
import sys
import json
import time
import argparse
import logging
import re
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
    Generates SFX using the Stable Audio API.
    """

    def __init__(self, api_key: str, base_url: str):
        if not api_key:
            raise ValueError("STABILITY_API_KEY cannot be empty.")
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "audio/*", # Request audio content
        }
        # TODO: Confirm the endpoint from the v2beta API reference.
        # As per the prompt, using /v2beta/audio/generate
        self.api_endpoint = f"{self.base_url}/v2beta/audio/generate"

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
        Makes a request to the Stable Audio API to generate audio.
        Implements exponential backoff for retries.
        """
        if lang == "ja":
            prompt_text = self._translate_prompt(prompt_text)

        payload = {
            "prompt": prompt_text,
            "duration": str(duration_sec),
            "format": "wav",
            # TODO: Confirm parameter names from the API reference.
            # "sample_rate" might not be a parameter if format implies it.
        }
        if seed:
            payload["seed"] = seed

        max_retries = 5
        base_delay = 2
        for attempt in range(max_retries):
            try:
                logging.info(f"Requesting audio for prompt: '{prompt_text}' (duration: {duration_sec}s)")
                response = requests.post(
                    self.api_endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=180, # Generous timeout for audio generation
                )
                response.raise_for_status()

                # Assuming the response body is the raw audio data.
                # TODO: Confirm the response format from the API reference.
                # It could be `response.json()["audio"]` and base64 encoded.
                audio_data = response.content
                actual_seed = int(response.headers.get("seed", seed or 0))

                logging.info(f"Successfully generated audio with seed: {actual_seed}")
                return audio_data, actual_seed

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                if status_code == 429 or status_code >= 500:
                    delay = base_delay * (2 ** attempt)
                    logging.warning(
                        f"Received status {status_code}. Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                else:
                    logging.error(f"HTTP Error: {e.response.text}")
                    raise
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed: {e}")
                raise

        raise Exception(f"Failed to generate audio for prompt '{prompt_text}' after {max_retries} retries.")


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
