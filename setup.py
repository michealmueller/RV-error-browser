"""
Setup script for QuantumOps package.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read version from config file
version_file = Path("config") / "version.txt"
with open(version_file, "r") as f:
    version = f.read().strip()

# Read requirements from requirements.txt
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="quantumops",
    version=version,
    description="Mobile build management and deployment tool",
    author="RosieVision",
    author_email="info@rosievision.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "quantumops=main:main",
        ],
    },
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Build Tools",
    ],
) 