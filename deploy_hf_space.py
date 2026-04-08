from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import HfApi, create_repo, upload_folder


def main() -> None:
    token = os.getenv("HF_TOKEN")
    if not token:
        raise EnvironmentError("HF_TOKEN is missing. Set HF_TOKEN to deploy to Hugging Face Spaces.")

    api = HfApi(token=token)
    who = api.whoami()
    username = who.get("name") or who.get("fullname")
    if not username:
        raise RuntimeError("Could not resolve Hugging Face username from token.")

    default_space_id = f"{username}/hackthon-openenv"
    space_id = os.getenv("HF_SPACE_ID", default_space_id)

    create_repo(
        repo_id=space_id,
        repo_type="space",
        space_sdk="docker",
        exist_ok=True,
        token=token,
    )

    root = Path(__file__).resolve().parent
    upload_folder(
        repo_id=space_id,
        repo_type="space",
        folder_path=str(root),
        token=token,
        ignore_patterns=[
            ".git/*",
            ".venv/*",
            ".venv313/*",
            "__pycache__/*",
            "*.pyc",
            "*.pyo",
            "*.pyd",
        ],
    )

    print(f"DEPLOYED_SPACE={space_id}")
    print(f"SPACE_URL=https://huggingface.co/spaces/{space_id}")


if __name__ == "__main__":
    main()
