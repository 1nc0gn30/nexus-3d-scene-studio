#!/usr/bin/env python3
"""Setup script for nexus-3d-scene-studio."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8", errors="replace") as f:
    long_description = f.read() if f else ""

setup(
    name="nexus-3d-scene-studio",
    version="1.0.0",
    author="Nexus 3D Scene Studio Contributors",
    description="Pure Python stdlib 3D graphics studio, parametric geometry engine, MCP server, and WebGL scene exporter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nexus-3d/nexus-3d-scene-studio",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={
        "": ["public/**/*", "public/*"],
    },
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "nexus-3d=nexus_3d_scene_studio.cli:main",
            "scene-studio=nexus_3d_scene_studio.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
        "Topic :: Multimedia :: Graphics :: 3D Rendering",
    ],
)
