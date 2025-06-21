from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="vdw-surfgen",
    version="0.2",
    packages=find_packages(),
    install_requires=["numpy", "matplotlib"],
    entry_points={
        "console_scripts": [
            "vsg=vdw_surfgen.cli:cli_entry",
        ]
    },
    author="Stephen O. Ajagbe",
    description="Generate van der Waals surface points from XYZ molecules",
    long_description=long_description,                 # <-- add this
    long_description_content_type="text/markdown",    # <-- and this
    python_requires=">=3.7",
)
