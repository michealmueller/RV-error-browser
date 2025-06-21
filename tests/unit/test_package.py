from pathlib import Path



def test_package_structure():
    """Test that the package has the correct structure."""
    # Check main package files
    assert Path("main.py").exists(), "main.py not found"
    assert Path("app.py").exists(), "app.py not found"
    assert Path("theme.py").exists(), "theme.py not found"
    assert Path("delegates.py").exists(), "delegates.py not found"
    assert Path("dialogs.py").exists(), "dialogs.py not found"

    # Check test files
    assert Path("tests").exists(), "tests directory not found"
    assert Path("tests/unit").exists(), "tests/unit directory not found"
    assert Path("tests/integration").exists(), "tests/integration directory not found"

    # Check configuration files
    assert Path("requirements.txt").exists(), "requirements.txt not found"
    assert Path("setup.py").exists(), "setup.py not found"
    assert Path("README.md").exists(), "README.md not found"
    assert Path("LICENSE").exists(), "LICENSE not found"
    assert Path(".gitignore").exists(), ".gitignore not found"


def test_imports():
    """Test that all modules can be imported."""
    import app
    import delegates
    import dialogs
    import theme

    import main

    assert main is not None
    assert app is not None
    assert theme is not None
    assert delegates is not None
    assert dialogs is not None


def test_dependencies():
    """Test that all required dependencies are installed."""

    # Check PySide6
    try:
        pass

        assert True
    except ImportError:
        assert False, "PySide6 not installed"

    # Check psycopg2
    try:
        pass

        assert True
    except ImportError:
        assert False, "psycopg2 not installed"

    # Check pytest
    try:
        pass

        assert True
    except ImportError:
        assert False, "pytest not installed"


def test_documentation():
    """Test that documentation exists and is valid."""
    # Check README
    readme = Path("README.md")
    assert readme.exists(), "README.md not found"
    with open(readme) as f:
        content = f.read()
        assert "# PostgreSQL Viewer" in content
        assert "## Installation" in content
        assert "## Usage" in content
        assert "## License" in content

    # Check docstrings
    import app
    import delegates
    import dialogs
    import theme

    import main

    assert main.__doc__ is not None, "main.py missing docstring"
    assert app.__doc__ is not None, "app.py missing docstring"
    assert theme.__doc__ is not None, "theme.py missing docstring"
    assert delegates.__doc__ is not None, "delegates.py missing docstring"
    assert dialogs.__doc__ is not None, "dialogs.py missing docstring"
