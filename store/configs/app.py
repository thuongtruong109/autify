import json
import os
import sys
from typing import Dict, Any

def get_config_path():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, "env.json")

    return os.path.join(root_dir, "env.json")

CRED_PATH = get_config_path()

def load_config_json() -> Dict[str, Any]:
    print(f"Attempting to load credentials from: {CRED_PATH}")
    if not os.path.exists(CRED_PATH):
        print(f"Error: {CRED_PATH} not found.")
        return {}

    with open(CRED_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error: JSON parse error in env.json: {e}")
        return {}

    if not isinstance(data, dict):
        print(f"Error: env.json must be a single object, not an array or other type.")
        return {}

    return data

def get_config_json(*keys):
    data = load_config_json()
    for k in keys:
        if isinstance(data, dict):
            data = data.get(k)
        else:
            return None
    return data


def load_credentials(use_sheet: bool = True, row_index: int = 0) -> Dict[str, Any]:
    """
    Load credentials from Google Sheet or JSON config file.
    Args:
        use_sheet: If True, load from Google Sheet; if False, load from env.json
        row_index: Row index to load from Google Sheet (default: 0 = first row)
    """
    if use_sheet:
        try:
            from libs.sheet import get_credentials_from_sheet
            print("📊 Loading credentials from Google Sheet...")
            credentials = get_credentials_from_sheet(row_index)
            if credentials:
                return credentials
            print("⚠️ Failed to load from Google Sheet. Falling back to env.json...")
        except ImportError:
            print("⚠️ sheet.py not found. Falling back to env.json...")
        except Exception as e:
            print(f"⚠️ Error loading from Google Sheet: {e}. Falling back to env.json...")
    return load_config_json()