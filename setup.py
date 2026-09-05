"""
WebFrame - A lightweight Python web framework library.

WebFrame provides core data processing, filtering, transformation,
and utility functions for building web applications.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="webframe",
    version="1.0.0",
    author="Mariusz Marzec",
    author_email="mariuszmarzec@gmail.com",
    description="A lightweight Python web framework library with data processing, filtering, and transformation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mariuszmarzec/test-manul-e2e",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "test": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ],
    },
)
