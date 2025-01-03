import os


from steamworks import STEAMWORKS
from steamworks.exceptions import SteamNotRunningException

steamworks = STEAMWORKS()

def init_steam():
    os.add_dll_directory(os.getcwd() )
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