import pytest
import os
import sys
import subprocess
from pathlib import Path

def test_build_script():
    """Test that the build script runs without errors."""
    # Run the build script
    result = subprocess.run([sys.executable, "build.py"], capture_output=True, text=True)
    
    # Check for errors
    assert result.returncode == 0, f"Build failed: {result.stderr}"
    
    # Check that the executable was created
    dist_dir = Path("dist")
    assert dist_dir.exists(), "dist directory not created"
    
    # Check for executable files
    executables = list(dist_dir.glob("QuantumOps*")) + list(dist_dir.glob("RosieVision-Error-Browser*"))
    assert len(executables) > 0, "No executables found in dist directory"

def test_version_file():
    """Test that the version file exists and contains a valid version number."""
    version_file = Path("version.txt")
    assert version_file.exists(), "version.txt not found"
    
    # Read version number
    with open(version_file) as f:
        version = f.read().strip()
    
    # Check version format (e.g., "1.0.0")
    assert len(version.split(".")) == 3, "Invalid version format"
    assert all(part.isdigit() for part in version.split(".")), "Version parts must be numbers"

def test_requirements_file():
    """Test that the requirements file exists and contains all necessary packages."""
    requirements_file = Path("requirements.txt")
    assert requirements_file.exists(), "requirements.txt not found"
    
    # Read requirements
    with open(requirements_file) as f:
        requirements = f.read().splitlines()
    
    # Check for required packages
    required_packages = {
        "PySide6",
        "psycopg2-binary",
        "pytest",
        "pytest-cov",
        "pyinstaller"
    }
    
    installed_packages = {req.split(">=")[0].split("==")[0] for req in requirements}
    assert required_packages.issubset(installed_packages), "Missing required packages"

def test_github_workflow():
    """Test that the GitHub workflow file exists and is valid."""
    workflow_file = Path(".github/workflows/build.yml")
    assert workflow_file.exists(), "GitHub workflow file not found"
    
    # Read workflow file
    with open(workflow_file) as f:
        workflow = f.read()
    
    # Check for required sections
    assert "name: Build QuantumOps" in workflow
    assert "on:" in workflow
    assert "jobs:" in workflow
    assert "build:" in workflow
    assert "Build on ${{ matrix.os }}" in workflow
    assert "pyinstaller quantumops.spec" in workflow 