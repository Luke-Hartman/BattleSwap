"""
Settings configuration model.

This module defines the Pydantic model used to load and validate user settings
from JSON configuration.
"""

import json
from pathlib import Path
from pydantic import BaseModel
from platformdirs import user_config_dir

class Settings(BaseModel):
    # Sound Settings
    SOUND_VOLUME: float = 0.5
    MUSIC_VOLUME: float = 0.5
    VOICE_VOLUME: float = 0.5

    class Config:
        frozen = False

settings = None

def get_settings_path() -> Path:
    """Get the path to the settings file."""
    # Use platformdirs to get the appropriate config directory
    settings_dir = Path(user_config_dir("battleswap"))
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir / "settings.json"

def save_settings() -> None:
    """Save the settings to the JSON file."""
    global settings
    if settings is None:
        return
    
    settings_path = get_settings_path()
    with open(settings_path, "w") as file:
        json.dump(settings.model_dump(), file, indent=4)

def load_settings() -> None:
    """Load the settings from the JSON file or create default settings if the file doesn't exist."""
    global settings
    settings_path = get_settings_path()
    
    if settings_path.exists():
        with open(settings_path, "r") as file:
            new_settings = Settings.model_validate_json(file.read())
    else:
        new_settings = Settings()
        # Save default settings
        with open(settings_path, "w") as file:
            json.dump(new_settings.model_dump(), file, indent=4)
    
    if settings is None:
        settings = new_settings
    else:
        for field in settings.model_fields:
            setattr(settings, field, getattr(new_settings, field))

# Initialize settings on module import
load_settings() 