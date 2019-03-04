"""Setup."""
from setuptools import setup, find_packages

with open("rio_cogeo/__init__.py") as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            continue


with open("README.rst") as f:
    readme = f.read()

# Runtime requirements.
inst_reqs = ["click", "rasterio[s3]>=1.0.9", "numpy~=1.15"]

extra_reqs = {
    "test": ["mock", "pytest", "pytest-cov"],
    "dev": ["mock", "pytest", "pytest-cov", "pre-commit"],
}

setup(
    name="rio-cogeo",
    version=version,
    description=u"CloudOptimized GeoTIFF (COGEO) creation plugin for rasterio",
    long_description=readme,
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    keywords="COGEO CloudOptimized Geotiff rasterio",
    author=u"Vincent Sarago",
    author_email="vincent@mapbox.com",
    url="https://github.com/mapbox/rio-cogeo",
    license="BSD-3",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    install_requires=inst_reqs,
    extras_require=extra_reqs,
    entry_points="""
      [rasterio.rio_plugins]
      cogeo=rio_cogeo.scripts.cli:cogeo
      """,
)
