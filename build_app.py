#!/usr/bin/env python3
"""
Build script for creating distributable packages of Pashto AI.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def build_windows_installer():
    """Build Windows installer using PyInstaller."""
    print("Building Windows installer...")
    
    # Clean up previous builds
    build_dir = Path("build")
    dist_dir = Path("dist")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # Create the executable
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=PashtoAI",
        "--windowed",
        "--onefile",
        "--icon=assets/icon.ico",
        "--add-data=assets;assets",
        "--noconsole",
        "main.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Build successful!")
        print(f"Executable created at: {dist_dir / 'PashtoAI.exe'}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error: {e}")
        return False

def package_application():
    """Package the application for distribution."""
    # Create distribution directory
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    # Copy necessary files
    files_to_copy = [
        "README.md",
        "LICENSE",
        "requirements_light.txt",
    ]
    
    for file in files_to_copy:
        if Path(file).exists():
            shutil.copy2(file, dist_dir / file)
    
    # Create a zip archive
    print("\nCreating distribution package...")
    shutil.make_archive("PashtoAI", 'zip', dist_dir)
    print(f"✅ Distribution package created: PashtoAI.zip")

def main():
    """Main function to build the application."""
    print("🚀 Pashto AI Build Tool")
    print("======================")
    
    if sys.platform.startswith('win'):
        if build_windows_installer():
            package_application()
    else:
        print("\n⚠️  This build script currently only supports Windows.")
        print("For other platforms, please build manually using PyInstaller.")
        print("Example command:")
        print("  pyinstaller --name=PashtoAI --windowed --onefile main.py")

if __name__ == "__main__":
    main()
