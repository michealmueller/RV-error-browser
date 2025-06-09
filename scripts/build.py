"""Build script for QuantumOps."""

import os
import sys
import shutil
from pathlib import Path
import subprocess

def build_app():
    """Build the QuantumOps application."""
    try:
        # Create build directory
        build_dir = Path("build")
        if build_dir.exists():
            shutil.rmtree(build_dir)
        build_dir.mkdir()
        
        # Copy source files
        src_dir = Path("quantumops")
        if not src_dir.exists():
            raise FileNotFoundError("Source directory not found")
            
        shutil.copytree(src_dir, build_dir / "quantumops")
        
        # Copy configuration files
        config_files = ["requirements.txt", "README.md", "LICENSE"]
        for file in config_files:
            if Path(file).exists():
                shutil.copy2(file, build_dir)
                
        # Create version file
        version = "1.0.0"  # TODO: Get from config
        with open(build_dir / "version.txt", "w") as f:
            f.write(version)
            
        print("Build completed successfully")
        return 0
        
    except Exception as e:
        print(f"Build failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(build_app()) 