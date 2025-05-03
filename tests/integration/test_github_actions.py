import pytest
import os
import yaml
from pathlib import Path

def test_workflow_file_exists():
    """Test that the GitHub workflow file exists."""
    workflow_file = Path(".github/workflows/build-release.yml")
    assert workflow_file.exists(), "GitHub workflow file not found"

def test_workflow_structure():
    """Test that the GitHub workflow has the correct structure."""
    workflow_file = Path(".github/workflows/build-release.yml")
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)
    
    # Check workflow name
    assert workflow["name"] == "Build and Release"
    
    # Check triggers
    assert "on" in workflow
    assert "push" in workflow["on"]
    assert "branches" in workflow["on"]["push"]
    assert "main" in workflow["on"]["push"]["branches"]
    assert "pull_request" in workflow["on"]
    assert "branches" in workflow["on"]["pull_request"]
    assert "main" in workflow["on"]["pull_request"]["branches"]
    
    # Check jobs
    assert "jobs" in workflow
    assert "build" in workflow["jobs"]
    
    # Check build job
    build_job = workflow["jobs"]["build"]
    assert build_job["runs-on"] == "ubuntu-latest"
    
    # Check steps
    steps = build_job["steps"]
    step_names = [step["name"] for step in steps]
    assert "Set up Python" in step_names
    assert "Install dependencies" in step_names
    assert "Run tests" in step_names
    assert "Build executable" in step_names
    assert "Upload artifact" in step_names

def test_workflow_dependencies():
    """Test that the GitHub workflow installs all necessary dependencies."""
    workflow_file = Path(".github/workflows/build-release.yml")
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)
    
    # Find the install dependencies step
    steps = workflow["jobs"]["build"]["steps"]
    install_step = next(step for step in steps if step["name"] == "Install dependencies")
    
    # Check that all required packages are installed
    install_commands = install_step["run"].split("\n")
    assert any("pip install -r requirements.txt" in cmd for cmd in install_commands)
    assert any("pip install pytest pytest-cov" in cmd for cmd in install_commands)

def test_workflow_artifacts():
    """Test that the GitHub workflow uploads the correct artifacts."""
    workflow_file = Path(".github/workflows/build-release.yml")
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)
    
    # Find the upload artifact step
    steps = workflow["jobs"]["build"]["steps"]
    upload_step = next(step for step in steps if step["name"] == "Upload artifact")
    
    # Check artifact configuration
    assert upload_step["uses"] == "actions/upload-artifact@v4"
    assert upload_step["with"]["name"] == "postgresql-viewer"
    assert upload_step["with"]["path"] == "dist/"
    assert upload_step["with"]["if-no-files-found"] == "error" 