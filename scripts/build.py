import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_for_platform(target_platform):
    """Build the executable for a specific platform"""
    print(f"\nBuilding for {target_platform}...")
    
    # Platform-specific setup
    if target_platform == "linux":
        if not shutil.which("upx"):
            print("Installing UPX for Linux...")
            subprocess.check_call(["sudo", "apt-get", "install", "-y", "upx"])
    elif target_platform == "darwin":
        if not shutil.which("upx"):
            print("Installing UPX for macOS...")
            subprocess.check_call(["brew", "install", "upx"])
    
    # Build command
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "rosievision_error_browser.spec"
    ]
    
    # Run the build
    subprocess.check_call(cmd)
    
    # Create a zip file of the distribution
    print("Creating distribution package...")
    dist_name = f"RosieVision_Error_Browser_{target_platform}_{platform.machine()}"
    shutil.make_archive(dist_name, 'zip', "dist")
    
    print(f"Build complete for {target_platform}!")
    print(f"Distribution package: {dist_name}.zip")

def main():
    """Main build function"""
    # Install dependencies
    install_dependencies()
    
    # Build for all platforms
    platforms = ["linux"] #["windows", "linux", "darwin"]
    for platform_name in platforms:
        build_for_platform(platform_name)

if __name__ == "__main__":
    main() 