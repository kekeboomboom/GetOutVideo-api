#!/usr/bin/env python3
"""
Setup script for GetOutVideo API package.

This setup.py is provided for backward compatibility with older pip versions.
The main package configuration is in pyproject.toml.
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="getoutvideo",
    version="1.0.0",
    author="GetOutVideo API",
    author_email="keboom.dev@gmail.com",
    description="Extract and process YouTube video transcripts with AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/keboom/GetOutVideo-api",
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
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pytubefix",
        "youtube-transcript-api",
        "openai>=1.75.0",
        "python-dotenv",
        "yt-dlp",
        "pydub",
        "ffmpeg-python",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "black", "flake8", "mypy", "twine", "build"],
        "test": ["pytest>=7.0", "pytest-cov"],
    },
    keywords="youtube transcript ai openai video-processing gpt",
    project_urls={
        "Documentation": "https://getoutvideo.readthedocs.io",
        "Bug Reports": "https://github.com/keboom/GetOutVideo-api/issues",
        "Source": "https://github.com/keboom/GetOutVideo-api",
    },
)