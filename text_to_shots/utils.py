"""Utility functions for the text_to_shots package."""

import os


def validate_api_key(api_key: str) -> bool:
    """Validate if the provided API key format is correct."""
    return api_key and api_key.startswith("sk-") and len(api_key) > 20


def create_references_folder(folder_path: str) -> bool:
    """Create references folder if it doesn't exist."""
    try:
        os.makedirs(folder_path, exist_ok=True)
        return True
    except Exception:
        return False

