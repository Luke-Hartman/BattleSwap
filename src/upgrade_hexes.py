"""Module for handling upgrade hexes persistence."""

import json
import os
import sys
from pathlib import Path
from typing import List, Tuple


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return Path(base_path) / relative_path


_upgrade_hexes: List[Tuple[int, int]] = []


def load_upgrade_hexes() -> None:
    """Load upgrade hexes from JSON file."""
    global _upgrade_hexes
    file_path = get_resource_path('data/upgrade_hexes.json')
    if not file_path.exists():
        _upgrade_hexes = []
        return
    
    try:
        with open(file_path, 'r') as file:
            hex_data = json.load(file)
            _upgrade_hexes = [tuple(coords) for coords in hex_data]
    except (json.JSONDecodeError, FileNotFoundError):
        _upgrade_hexes = []


def _save_upgrade_hexes() -> None:
    """Save upgrade hexes to JSON file."""
    file_path = get_resource_path('data/upgrade_hexes.json')
    hex_data = [list(coords) for coords in _upgrade_hexes]
    
    with open(file_path, 'w') as file:
        json.dump(hex_data, file, indent=2)


def get_upgrade_hexes() -> List[Tuple[int, int]]:
    """Get all upgrade hexes."""
    return _upgrade_hexes.copy()


def add_upgrade_hex(coords: Tuple[int, int]) -> None:
    """Add an upgrade hex."""
    if coords not in _upgrade_hexes:
        _upgrade_hexes.append(coords)
        _save_upgrade_hexes()


def remove_upgrade_hex(coords: Tuple[int, int]) -> None:
    """Remove an upgrade hex."""
    if coords in _upgrade_hexes:
        _upgrade_hexes.remove(coords)
        _save_upgrade_hexes()


def is_upgrade_hex(coords: Tuple[int, int]) -> bool:
    """Check if coordinates represent an upgrade hex."""
    return coords in _upgrade_hexes


# Load upgrade hexes on module import
load_upgrade_hexes() 