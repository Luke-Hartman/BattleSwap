import os
import sys
import platform

from steamworks import STEAMWORKS
from steamworks.exceptions import SteamNotRunningException

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def init_steam():
    # Store the original working directory and change it only on MacOS
    if platform.system() == "Darwin":
        os.chdir(get_resource_path("."))

    # Add DLL directory to path only on Windows
    if platform.system() == "Windows":
        dll_dir = get_resource_path(".")
        os.add_dll_directory(dll_dir)
        
    # Initialize Steam

    steamworks = STEAMWORKS()   
    try:
        steamworks.initialize()
    except OSError as e:
        print(f"Failed to initialize Steamworks: {e}")
        exit()
    except SteamNotRunningException:
        print("Steam is not running")
        exit()

# # Example API usage
# steam_id = steamworks.Users.GetSteamID()
# print(f"Steam ID: {steam_id}")