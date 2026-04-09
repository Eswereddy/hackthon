#!/usr/bin/env python3
"""Quick deployment to Hugging Face Spaces without dependency installation."""
from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import HfApi, create_repo, upload_folder


def main() -> None:
    token = os.getenv("HF_TOKEN")
    if not token:
        print("ERROR: HF_TOKEN is not set")
        print("Please set HF_TOKEN environment variable before running this script")
        return

    try:
        api = HfApi(token=token)
        who = api.whoami()
        username = who.get("name") or who.get("fullname")
        if not username:
            print("ERROR: Could not resolve Hugging Face username from token")
            return

        default_space_id = f"{username}/hackthon-openenv"
        space_id = os.getenv("HF_SPACE_ID", default_space_id)

        print(f"Creating/updating space: {space_id}")
        create_repo(
            repo_id=space_id,
            repo_type="space",
            space_sdk="docker",
            exist_ok=True,
            token=token,
        )

        root = Path(__file__).resolve().parent
        print(f"Uploading files from: {root}")
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

        print(f"✓ DEPLOYMENT SUCCESSFUL")
        print(f"Space ID: {space_id}")
        print(f"Space URL: https://huggingface.co/spaces/{space_id}")

    except Exception as e:
        print(f"ERROR: Deployment failed - {e}")
        raise


if __name__ == "__main__":
    main()
