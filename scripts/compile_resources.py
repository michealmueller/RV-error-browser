import subprocess
from pathlib import Path


def compile_resources():
    """Compile the Qt resource file."""
    qrc_file = Path("icons.qrc")
    output_py_file = Path("resources_rc.py")

    if not qrc_file.exists():
        print(f"Error: Resource file not found at {qrc_file}")
        return

    print(f"Compiling {qrc_file} to {output_py_file}...")
    try:
        subprocess.run(
            ["pyside6-rcc", str(qrc_file), "-o", str(output_py_file)],
            check=True,
            capture_output=True,
            text=True,
        )
        print("Resource file compiled successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error compiling resource file: {e}")
        print(f"Stderr: {e.stderr}")
    except FileNotFoundError:
        print(
            "Error: 'pyside6-rcc' command not found. Make sure PySide6 is installed and in your PATH."
        )


if __name__ == "__main__":
    compile_resources()
