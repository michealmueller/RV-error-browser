import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def build_executable():
    """Build the executable for the current platform"""
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Ensure UPX is installed (for compression)
    if not shutil.which("upx"):
        print("UPX not found. Please install UPX for better compression.")
        print("Windows: Download from https://upx.github.io/")
        print("macOS: brew install upx")
        print("Linux: sudo apt-get install upx")
    
    # Get the current platform
    current_platform = platform.system().lower()
    
    # Create build directory
    build_dir = Path("build")
    dist_dir = Path("dist")
    build_dir.mkdir(exist_ok=True)
    dist_dir.mkdir(exist_ok=True)
    
    # Build command
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "postgresql_viewer.spec"
    ]
    
    # Platform-specific options
    if current_platform == "windows":
        cmd.extend(["--icon", "icon.ico"])
    elif current_platform == "darwin":  # macOS
        cmd.extend(["--osx-bundle-identifier", "com.postgresqlviewer.app"])
    
    # Run the build
    print(f"Building for {current_platform}...")
    subprocess.check_call(cmd)
    
    # Create a zip file of the distribution
    print("Creating distribution package...")
    dist_name = f"PostgreSQL_Viewer_{current_platform}_{platform.machine()}"
    shutil.make_archive(dist_name, 'zip', dist_dir)
    
    print(f"\nBuild complete! Executable is in the 'dist' directory.")
    print(f"Distribution package: {dist_name}.zip")

if __name__ == "__main__":
    build_executable() 