"""Script for deploying game builds to Steam.

This script handles:
1. Building the game using build_installer.py
2. Deploying the build to Steam using SteamCMD
3. Setting the appropriate depot content and publishing the build

This should be run in a CI environment when a new tag is created.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import build_installer

def download_steamcmd(dest_dir: Path) -> Path:
    """Download and extract SteamCMD to the specified directory.
    
    Args:
        dest_dir: Directory to install SteamCMD
        
    Returns:
        Path to the steamcmd executable
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    steamcmd_zip = dest_dir / "steamcmd.zip"
    
    # Download SteamCMD
    subprocess.run(
        [
            "curl",
            "-L",
            "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip",
            "-o",
            str(steamcmd_zip)
        ],
        check=True
    )
    
    # Extract it
    subprocess.run(
        ["powershell", "Expand-Archive", str(steamcmd_zip), str(dest_dir)],
        check=True
    )
    
    steamcmd_exe = dest_dir / "steamcmd.exe"
    if not steamcmd_exe.exists():
        raise FileNotFoundError("Failed to find steamcmd.exe after extraction")
        
    return steamcmd_exe

def create_app_build_vdf(
    project_root: Path,
    app_id: str,
    depot_id: str,
    branch: str = "beta"
) -> Path:
    """Create the app build configuration file for Steam.
    
    Args:
        project_root: Root directory of the project
        app_id: Steam App ID
        depot_id: Steam Depot ID
        branch: Steam branch to deploy to
        
    Returns:
        Path to the created VDF file
    """
    vdf_content = f'''
"AppBuild"
{{
    "AppID" "{app_id}"
    "Desc" "Build created from tag {os.environ.get('GITHUB_REF_NAME', 'unknown')}"
    "BuildOutput" "build_output/"
    "ContentRoot" "{project_root / 'build'}"
    "SetLive" "{branch}"
    
    "Depots"
    {{
        "{depot_id}"
        {{
            "FileMapping"
            {{
                "LocalPath" "*"
                "DepotPath" "."
                "recursive" "1"
            }}
        }}
    }}
}}
'''
    
    vdf_path = project_root / "scripts" / "app_build.vdf"
    with open(vdf_path, "w") as f:
        f.write(vdf_content)
    
    return vdf_path

def deploy_to_steam(
    project_root: Path,
    app_id: str,
    depot_id: str,
    username: str,
    password: str,
    branch: str = "beta"
) -> None:
    """Deploy the game build to Steam.
    
    Args:
        project_root: Root directory of the project
        app_id: Steam App ID
        depot_id: Steam Depot ID
        username: Steam username
        password: Steam password
        branch: Steam branch to deploy to
    """
    # First build the game
    build_installer.main()
    
    # Setup SteamCMD
    tools_dir = project_root / "build" / "tools"
    steamcmd = download_steamcmd(tools_dir)
    
    # Create build configuration
    vdf_path = create_app_build_vdf(project_root, app_id, depot_id, branch)
    
    # Run SteamCMD to upload build
    subprocess.run(
        [
            str(steamcmd),
            "+login", username, password,
            "+run_app_build", str(vdf_path),
            "+quit"
        ],
        check=True
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy game build to Steam")
    parser.add_argument("--app-id", required=True, help="Steam App ID")
    parser.add_argument("--depot-id", required=True, help="Steam Depot ID")
    parser.add_argument("--username", required=True, help="Steam username")
    parser.add_argument("--branch", default="beta", help="Steam branch to deploy to")
    args = parser.parse_args()
    
    # Password should be passed via environment variable for security
    password = os.environ.get("STEAM_PASSWORD")
    if not password:
        print("Error: STEAM_PASSWORD environment variable must be set")
        sys.exit(1)
    
    project_root = Path(__file__).parent.parent
    
    deploy_to_steam(
        project_root=project_root,
        app_id=args.app_id,
        depot_id=args.depot_id,
        username=args.username,
        password=password,
        branch=args.branch
    )

if __name__ == "__main__":
    main() 