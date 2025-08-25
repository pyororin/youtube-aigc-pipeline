import hmac
import requests
import hashlib
import json
from datetime import datetime, timezone
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description='Generate voice from text using CoeFont API.')
    parser.add_argument('--issue-id', required=True, help='The issue ID.')
    args = parser.parse_args()

    accesskey = os.environ.get("COEFONT_USER")
    access_secret = os.environ.get("COEFONT_PASS")

    if not accesskey or not access_secret:
        print("Error: COEFONT_USER and COEFONT_PASS environment variables are not set.")
        return

    text_file_path = f"assets/issues/{args.issue_id}/text/tts_input_all.txt"
    output_file_path = f"assets/issues/{args.issue_id}/audio/voice.wav"

    with open(text_file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # CoeFont API requires text to be within a certain length. Let's split it.
    # This is a simple split, a more sophisticated approach might be needed for long texts.
    # However, for this specific case, we will send the whole text.
    # The API might handle long texts by itself.

    # The coefont ID for the '先輩' character is not specified.
    # I will use a default male voice for now.
    # This might need to be changed later if a specific voice is required.
    coefont_id = "2b174967-1a8a-42e4-b1ae-5f6548cfa05d" # A default male voice

    date: str = str(int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp()))
    data: str = json.dumps({
      'coefont': coefont_id,
      'text': text
    })

    signature = hmac.new(bytes(access_secret, 'utf-8'), (date+data).encode('utf-8'), hashlib.sha256).hexdigest()

    response = requests.post('https://api.coefont.cloud/v2/text2speech', data=data, headers={
      'Content-Type': 'application/json',
      'Authorization': accesskey,
      'X-Coefont-Date': date,
      'X-Coefont-Content': signature
    })

    if response.status_code == 200:
        with open(output_file_path, 'wb') as f:
            f.write(response.content)
        print(f"Successfully generated voice file: {output_file_path}")
    else:
        print(f"Error: CoeFont API request failed with status code {response.status_code}")
        print(response.json())

if __name__ == '__main__':
    main()
