from pathlib import Path


def test_workflow_file_exists():
    """Test that the GitHub workflow file exists."""
    workflow_file = Path(".github/workflows/build.yml")
    assert workflow_file.exists(), "GitHub workflow file not found"


def test_workflow_structure():
    """Test that the GitHub workflow has the correct structure."""
    workflow_file = Path(".github/workflows/build.yml")
    with open(workflow_file) as f:
        workflow = f.read()
    assert "name: Build QuantumOps" in workflow
    assert "on:" in workflow
    assert "jobs:" in workflow
    assert "build:" in workflow
    assert "Build on ${{ matrix.os }}" in workflow
    assert "pyinstaller quantumops.spec" in workflow


def test_workflow_dependencies():
    """Test that the GitHub workflow installs all necessary dependencies."""
    workflow_file = Path(".github/workflows/build.yml")
    with open(workflow_file) as f:
        workflow = f.read()
    assert "pip install -r requirements.txt" in workflow
    assert "pip install pyinstaller" in workflow


def test_workflow_artifacts():
    """Test that the GitHub workflow uploads the correct artifacts."""
    workflow_file = Path(".github/workflows/build.yml")
    with open(workflow_file) as f:
        workflow = f.read()
    assert "actions/upload-artifact@v4" in workflow
    assert (
        "dist/QuantumOps*" in workflow or "dist/RosieVision-Error-Browser*" in workflow
    )
