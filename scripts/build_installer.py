"""Build script for creating game installers.

This script handles:
1. Creating an executable using PyInstaller
2. Packaging assets and dependencies
3. Creating an installer
4. Creating a distributable zip file
"""

import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import List, Optional, Set
import sys
import platform

REQUIRED_ASSETS = {
    'directories': {
        'units',
        'icons',
        'sounds',
        'voices',
        'music',
        'effects',
    },
    'data_files': {
        'game_constants.json',
        'battles.json',
    }
}

EXCLUDED_PATTERNS = {
    '*.zip',  # Source asset zip files
    '__pycache__',
    '.git',
    '.DS_Store',
    'Thumbs.db',
    '*.psd',  # Source art files
    '*.aseprite',
    '*.spec',
    '*.pyc',
    '*.pyo',
    '*.pyd',
}

STEAM_LIBRARIES = {
    'windows': [
        ('steam_api64.dll', '.'),
        ('SteamworksPy64.dll', '.'),
        ('steam_api64.dll', 'steamworks'),
        ('SteamworksPy64.dll', 'steamworks'),
    ],
    'darwin': [  # MacOS
        ('libsteam_api.dylib', '.'),
        ('SteamworksPy.dylib', '.'),
        ('libsteam_api.dylib', 'steamworks'),
        ('SteamworksPy.dylib', 'steamworks'),
    ]
}

def validate_project_structure(asset_dir: Path, data_dir: Path) -> None:
    """Validate that all required assets and data files exist and are valid.
    
    Args:
        asset_dir: Path to the assets directory
        data_dir: Path to the data directory
        
    Raises:
        FileNotFoundError: If any required files or directories are missing
        json.JSONDecodeError: If any JSON file is invalid
    """
    missing_items: List[str] = []
    
    # Check asset directories
    for dir_name in REQUIRED_ASSETS['directories']:
        if not (asset_dir / dir_name).is_dir():
            missing_items.append(f"assets/{dir_name}")
    
    # Check and validate data files
    for file_name in REQUIRED_ASSETS['data_files']:
        file_path = data_dir / file_name
        if not file_path.is_file():
            missing_items.append(f"data/{file_name}")
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)  # Validates JSON format
    
    if missing_items:
        raise FileNotFoundError(
            f"Missing required files/directories:\n" + "\n".join(missing_items)
        )

def copy_project_files(src_dir: Path, dest_dir: Path) -> None:
    """Copy project files to the build directory, excluding unnecessary files.
    
    Args:
        src_dir: Source directory
        dest_dir: Destination directory
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    for item in src_dir.rglob('*'):
        if not item.is_file() or any(item.match(pattern) for pattern in EXCLUDED_PATTERNS):
            continue
            
        rel_path = item.relative_to(src_dir)
        dest_path = dest_dir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest_path)

def create_executable(project_root: Path, build_dir: Path) -> None:
    """Create executable using PyInstaller.
    
    Args:
        project_root: Root directory of the project
        build_dir: Directory where the executable should be created
    """
    # Copy steam_appid.txt to build directory
    shutil.copy2(project_root / 'steam_appid.txt', build_dir / 'steam_appid.txt')
    
    # Determine platform-specific settings
    platform_name = 'darwin' if sys.platform == 'darwin' else 'windows'
    steam_libs = STEAM_LIBRARIES[platform_name]
    
    # Convert steam library paths to actual file paths
    binary_paths = []
    for lib_file, dest in steam_libs:
        lib_path = project_root / lib_file
        if lib_path.exists():
            binary_paths.append((str(lib_path), dest))
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    [r'{str(project_root / "src" / "main.py")}'],
    pathex=[r'{str(project_root / "src")}'],
    binaries={binary_paths},
    datas=[
        (r'{str(project_root / "assets")}', 'assets'),
        (r'{str(project_root / "data")}', 'data'),
        (r'{str(project_root / "src" / "settings.py")}', '.'),
        (r'{str(project_root / "steam_appid.txt")}', '.'),
    ],
    hiddenimports=['steamworks', 'steamworks.util', 'steamworks.interfaces'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BattleSwap',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

    if platform.system() == 'Darwin':
        # Add MacOS-specific app bundle configuration
        spec_content += '''
app = BUNDLE(
    exe,
    name='BattleSwap.app',
    icon=None,  # You can specify an .icns file here
    bundle_identifier='com.yourgame.battleswap',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleName': 'BattleSwap',
        'NSHighResolutionCapable': 'True',
    },
)
'''
    
    spec_path = project_root / 'BattleSwap.spec'
    with open(spec_path, 'w') as f:
        f.write(spec_content)
    
    try:
        subprocess.run(
            [
                'pyinstaller',
                '--clean',
                '--noconfirm',
                f'--distpath={build_dir}',
                '--workpath=build/temp',
                str(spec_path)
            ],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed:\n{e.stdout}\n{e.stderr}")
        raise
    finally:
        spec_path.unlink(missing_ok=True)

def cleanup_build_artifacts(project_root: Path, preserve_build: bool = True) -> None:
    """Clean up build artifacts and temporary files.
    
    Args:
        project_root: Root directory of the project
        preserve_build: Whether to preserve the main build directory
    """
    cleanup_dirs = {'build/temp', 'dist', '__pycache__', '.pytest_cache'}
    if not preserve_build:
        cleanup_dirs.add('build')
    
    for dir_name in cleanup_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path, ignore_errors=True)
    
    for pattern in EXCLUDED_PATTERNS:
        if not pattern.startswith('*'):
            continue
        for file_path in project_root.rglob(pattern):
            file_path.unlink(missing_ok=True)

def create_distribution_zip(build_dir: Path) -> None:
    """Create a zip file containing the game executable and required files.
    
    Args:
        build_dir: Directory containing the built files
    """
    # Create zip file in temp location first
    temp_zip_path = build_dir.parent / 'temp_BattleSwap.zip'
    final_zip_path = build_dir / 'BattleSwap.zip'
    
    try:
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add all files from build directory
            for file_path in build_dir.rglob('*'):
                if file_path.is_file():
                    zf.write(file_path, str(file_path.relative_to(build_dir)))
        
        # Move zip file to build directory
        if final_zip_path.exists():
            final_zip_path.unlink()
        shutil.move(temp_zip_path, final_zip_path)
    finally:
        # Clean up temp file if something went wrong
        if temp_zip_path.exists():
            temp_zip_path.unlink()

def main() -> None:
    project_root = Path(__file__).parent.parent
    build_dir = project_root / 'build'
    assets_dir = project_root / 'assets'
    data_dir = project_root / 'data'
    
    print("Cleaning up previous build artifacts...")
    cleanup_build_artifacts(project_root)
    
    print("Validating project structure...")
    validate_project_structure(assets_dir, data_dir)
    
    print("Copying project files...")
    copy_project_files(assets_dir, build_dir / 'assets')
    copy_project_files(data_dir, build_dir / 'data')
    
    print("Creating executable...")
    create_executable(project_root, build_dir)
    
    print("Cleaning up temporary files...")
    cleanup_build_artifacts(project_root, preserve_build=True)
    
    print("Creating distribution zip file...")
    create_distribution_zip(build_dir)
    
    print("Build complete!")

if __name__ == '__main__':
    main()