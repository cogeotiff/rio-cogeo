"""Setup."""

from setuptools import find_packages, setup

with open("README.md") as f:
    readme = f.read()

# Runtime requirements.
inst_reqs = [
    "click>=7.0",
    "rasterio>=1.1",
    "numpy~=1.15",
    "morecantile>=2.1,<2.2",
    "pydantic",
]

extra_reqs = {
    "test": ["pytest", "pytest-cov", "rio-tiler~=2.0", "cogdumper"],
    "dev": ["pytest", "pytest-cov", "rio-tiler~=2.0", "pre-commit", "cogdumper"],
    "docs": ["mkdocs", "mkdocs-material"],
}

setup(
    name="rio-cogeo",
    version="2.3.1",
    python_requires=">=3.6",
    description=u"Cloud Optimized GeoTIFF (COGEO) creation plugin for rasterio",
    long_description=readme,
    long_description_content_type="text/markdown",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
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
