"""
Setup script for Scale API Compose Pilot.
"""

from setuptools import setup, find_packages

setup(
    name="scale-api-compose-pilot",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "scale-compose=scale_api_compose_pilot.cli:main",
        ],
    },
)