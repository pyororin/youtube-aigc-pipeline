import json
import os
from datetime import datetime

def main():
    issue_id = "3"
    assets_dir = f"assets/issues/{issue_id}"
    metadata_file = f"{assets_dir}/metadata.json"

    # Read existing metadata
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Add info for other assets
    assets_to_add = {
        "title": "text/title.txt",
        "summary": "text/summary.txt",
        "audio": "audio/ambience.mp3",
        "thumbnail": "thumbnail/thumbnail.jpg"
    }

    for key, path in assets_to_add.items():
        full_path = os.path.join(assets_dir, path)
        if os.path.exists(full_path):
            metadata[key] = {
                "path": full_path,
                "size_bytes": os.path.getsize(full_path),
                "created_at": datetime.now().isoformat() + "Z"
            }

    # Write updated metadata
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"Metadata updated successfully at {metadata_file}")

if __name__ == "__main__":
    main()
