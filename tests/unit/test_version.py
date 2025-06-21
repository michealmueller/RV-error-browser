from pathlib import Path



def test_version_file_exists():
    """Test that the version file exists."""
    version_file = Path("version.txt")
    assert version_file.exists(), "version.txt not found"


def test_version_format():
    """Test that the version number has the correct format."""
    version_file = Path("version.txt")
    with open(version_file) as f:
        version = f.read().strip()

    # Check version format (e.g., "1.0.0")
    parts = version.split(".")
    assert len(parts) == 3, "Version must have 3 parts (major.minor.patch)"
    assert all(part.isdigit() for part in parts), "All version parts must be numbers"

    # Check version range
    major, minor, patch = map(int, parts)
    assert 0 <= major <= 999, "Major version out of range"
    assert 0 <= minor <= 999, "Minor version out of range"
    assert 0 <= patch <= 999, "Patch version out of range"


def test_version_increment():
    """Test that the version can be incremented."""
    version_file = Path("version.txt")
    with open(version_file) as f:
        original_version = f.read().strip()

    # Increment patch version
    parts = original_version.split(".")
    new_version = f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"

    # Write new version
    with open(version_file, "w") as f:
        f.write(new_version)

    # Verify new version
    with open(version_file) as f:
        assert f.read().strip() == new_version

    # Restore original version
    with open(version_file, "w") as f:
        f.write(original_version)


def test_version_consistency():
    """Test that the version is consistent across files."""
    version_file = Path("version.txt")
    with open(version_file) as f:
        version = f.read().strip()

    # Check version in setup.py
    setup_file = Path("setup.py")
    if setup_file.exists():
        with open(setup_file) as f:
            setup_content = f.read()
            assert f'version="{version}"' in setup_content

    # Check version in README.md
    readme_file = Path("README.md")
    if readme_file.exists():
        with open(readme_file) as f:
            readme_content = f.read()
            assert version in readme_content
