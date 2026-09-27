# config/config.py
# This module loads settings from settings.yaml so the application has a single source of truth for rules.

import os
import yaml
from typing import Dict, Any

# Locate the configuration YAML file relative to this file's directory
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.yaml")

def load_settings() -> Dict[str, Any]:
    """
    Reads the settings.yaml file and returns it as a Python dictionary.
    If the file is missing or invalid, returns fallback defaults.
    """
    if not os.path.exists(SETTINGS_FILE):
        raise FileNotFoundError(f"Configuration file not found at: {SETTINGS_FILE}")
    
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    return config_data

# Global instance of settings loaded at runtime
SETTINGS = load_settings()

def get_setting(key_path: str, default: Any = None) -> Any:
    """
    Utility function to retrieve nested settings using dot-notation.
    Example: get_setting('llm.default_model', 'llama-3.3-70b-versatile')
    """
    keys = key_path.split(".")
    val = SETTINGS
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return default
    return val
