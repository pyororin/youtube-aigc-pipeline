import argparse
import re
import sys
import os

def extract_dialogues_from_line(line):
    """
    Extracts dialogues from a single line based on refined logic.
    - If a speaker tag 【...】 is present, extract content between the first「 and the last 」.
    - Otherwise, extract all balanced 「...」 pairs.
    - Returns a list of dialogues and a potential warning message.
    """
    line = line.strip()
    dialogues = []
    warning_msg = None

    if not line or line.startswith('SFX:'):
        return dialogues, warning_msg

    if line.count('「') != line.count('」'):
        warning_msg = f"Skipped due to unbalanced quotes: {line}"
        return dialogues, warning_msg

    if '「' not in line:
        if not re.match(r'^【[^】]+】$', line.strip()):
             warning_msg = f"Skipped due to missing quotes: {line}"
        return dialogues, warning_msg

    speaker_match = re.match(r'^(【[^】]+】)', line)
    text_to_process = line

    if speaker_match:
        text_to_process = line[len(speaker_match.group(1)):].strip()
        start_quote = text_to_process.find('「')
        end_quote = text_to_process.rfind('」')

        if start_quote != -1 and end_quote != -1 and start_quote < end_quote:
            dialogue = text_to_process[start_quote+1:end_quote]
            dialogues.append(dialogue)
    else:
        # No speaker tag, find all individual dialogues using the manual parser
        balance = 0
        start_index = -1
        for i, char in enumerate(text_to_process):
            if char == '「':
                if balance == 0:
                    start_index = i
                balance += 1
            elif char == '」':
                if balance > 0:
                    balance -= 1
                    if balance == 0 and start_index != -1:
                        dialogues.append(text_to_process[start_index+1:i])
                        start_index = -1

    if not dialogues and '「' in line:
        warning_msg = f"Could not extract dialogue despite presence of quotes: {line}"

    return dialogues, warning_msg


def main():
    parser = argparse.ArgumentParser(description='Extract dialogues from a script file.')
    parser.add_argument('--issue-id', required=True, help='The issue ID.')
    parser.add_argument('--dry-run', action='store_true', help='Print to stdout instead of writing to a file.')
    args = parser.parse_args()

    issue_id = args.issue_id
    dry_run = args.dry_run

    input_path = f'assets/issues/{issue_id}/text/script.md'
    output_path = f'assets/issues/{issue_id}/text/tts_input_all.txt'

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}", file=sys.stderr)
        sys.exit(1)

    all_dialogues = []
    warnings = 0
    extraction_count = 0

    for i, line in enumerate(lines):
        line_num = i + 1

        dialogues, warning_msg = extract_dialogues_from_line(line)

        if warning_msg:
            print(f"Warning: Line {line_num} {warning_msg}", file=sys.stderr)
            warnings += 1
            continue

        for dialogue in dialogues:
            # Trim leading/trailing whitespace (including full-width spaces)
            dialogue = dialogue.strip(' \u3000')
            # Normalize multiple whitespace characters into a single space
            dialogue = re.sub(r'\s+', ' ', dialogue)
            if dialogue:
                all_dialogues.append(dialogue)
                extraction_count += 1

    if extraction_count == 0:
        print("Error: No dialogues were extracted.", file=sys.stderr)
        sys.exit(2)

    # Join dialogues with newlines, ensure single trailing newline
    output_content = "\n".join(all_dialogues)
    # Remove multiple blank lines that might have been created
    output_content = re.sub(r'\n{2,}', '\n', output_content.strip()) + '\n'

    if dry_run:
        print("--- Dry Run Output ---")
        print(output_content, end='')
        print("--- End Dry Run ---")
    else:
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"Successfully wrote {extraction_count} dialogues to {output_path}")
        print(f"File size: {len(output_content.encode('utf-8'))} bytes")

    if warnings > 0:
        print(f"\nCompleted with {warnings} warnings.", file=sys.stderr)

    sys.exit(0)

if __name__ == '__main__':
    main()
