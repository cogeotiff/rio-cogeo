"""Setup."""

import sys
from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()

# Runtime requirements.
inst_reqs = [
    "click",
    "rasterio[s3]>=1.0.1",
    "numpy~=1.15",
    "supermercado",
    "mercantile",
]

if sys.version_info < (3, 3):
    inst_reqs.append("contextlib2")

extra_reqs = {
    "test": ["pytest", "pytest-cov", "rio-tiler"],
    "dev": ["pytest", "pytest-cov", "rio-tiler", "pre-commit"],
}

if sys.version_info >= (3, 6):
    extra_reqs["test"].append("cogdumper")
    extra_reqs["dev"].append("cogdumper")

setup(
    name="rio-cogeo",
    version="1.1.0",
    description=u"CloudOptimized GeoTIFF (COGEO) creation plugin for rasterio",
    long_description=readme,
    long_description_content_type="text/markdown",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    keywords="COGEO CloudOptimized Geotiff rasterio",
    author=u"Vincent Sarago",
    author_email="vincent@developmentseed.com",
    url="https://github.com/cogeotiff/rio-cogeo",
    license="BSD-3",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    install_requires=inst_reqs,
    extras_require=extra_reqs,
    entry_points="""
      [rasterio.rio_plugins]
      cogeo=rio_cogeo.scripts.cli:cogeo
      """,
)
