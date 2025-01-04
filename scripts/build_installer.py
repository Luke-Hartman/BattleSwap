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
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    [r'{str(project_root / "src" / "main.py")}'],
    pathex=[r'{str(project_root / "src")}'],
    binaries=[],
    datas=[
        (r'{str(project_root / "assets")}', 'assets'),
        (r'{str(project_root / "data")}', 'data'),
        (r'{str(project_root / "src" / "settings.py")}', '.'),
    ],
    hiddenimports=[],
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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
    zip_path = build_dir.parent / 'build' / 'BattleSwap.zip'
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add executable
        exe_path = build_dir / 'BattleSwap.exe'
        if exe_path.exists():
            zf.write(exe_path, exe_path.name)
        
        # Add assets and data directories
        for dir_name in ['assets', 'data']:
            dir_path = build_dir / dir_name
            if dir_path.exists():
                for file_path in dir_path.rglob('*'):
                    if file_path.is_file():
                        zf.write(file_path, str(file_path.relative_to(build_dir)))

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