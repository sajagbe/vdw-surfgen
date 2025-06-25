from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="vdw-surfgen",
    version="0.4.2", 
    license="MIT",
    include_package_data=False,
    packages=find_packages(),
    install_requires=["numpy", "matplotlib", "tqdm", "colorama"],
    entry_points={
        "console_scripts": [
            "vsg=vdw_surfgen.cli:cli_entry",
        ]
    },
    author="Stephen O. Ajagbe",
    description="Generate van der Waals surface points from XYZ files.",
    long_description=long_description,
    long_description_content_type="text/markdown", 
    url="https://github.com/sajagbe/vdw-surfgen",
    python_requires=">=3.7"
)
