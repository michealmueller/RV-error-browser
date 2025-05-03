from setuptools import setup, find_packages

setup(
    name="RosieVision-Error-Browser",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyside6",
        "psycopg2-binary",
        "pyinstaller"
    ],
    entry_points={
        'console_scripts': [
            'rosievision-error-browser=main:main',
        ],
    },
    author="Micheal Mueller",
    author_email="msquared86@gmail.commichealmueller",
    description="A modern PySide6-based application for viewing RosieVision error logs",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/msquared86/RV-error-browser",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 