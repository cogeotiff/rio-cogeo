=========
rio-cogeo
=========

CloudOptimized GeoTIFF (COGEO) creation plugin for rasterio

.. image:: https://badge.fury.io/py/rio-cogeo.svg
    :target: https://badge.fury.io/py/rio-cogeo

.. image:: https://circleci.com/gh/mapbox/rio-cogeo.svg?style=svg
   :target: https://circleci.com/gh/mapbox/rio-cogeo

.. image:: https://codecov.io/gh/mapbox/rio-cogeo/branch/master/graph/badge.svg?token=zuHupC20cG
   :target: https://codecov.io/gh/mapbox/rio-cogeo


Install
=======

.. code-block:: console

  $ pip install -U pip
  $ pip install rio-cogeo

Or install from source:

.. code-block:: console

   $ git clone https://github.com/mapbox/rio-cogeo.git
   $ cd rio-cogeo
   $ pip install -U pip
   $ pip install -e .

Usage
=====

.. code-block::

  $ rio cogeo --help
  Usage: rio cogeo [OPTIONS] INPUT OUTPUT

    Create Cloud Optimized Geotiff.

  Options:
    -b, --bidx BIDX                 Band index to copy
    -p, --cog-profile [ycbcr|zstd|lzw|deflate|packbits|raw]
                                    CloudOptimized GeoTIFF profile (default: ycbcr)
    --nodata INTEGER                Force mask creation from a given nodata value
    --alpha INTEGER                 Force mask creation from a given alpha band number
    --overview-level INTEGER        Overview level (default: 6)
    --threads INTEGER
    --co, --profile NAME=VALUE      Driver specific creation options.See the
                                    documentation for the selected output driver
                                    for more information.
    --help                          Show this message and exit.


Examples
========

.. code-block:: console

  # Create a COGEO with YCbCR profile and the first 3 bands of the data
  $ rio cogeo mydataset.tif mydataset_ycbcr.tif -b 1,2,3

  # Create a COGEO without compression and wiht 1024x1024 block size
  $ rio cogeo mydataset.tif mydataset_raw.tif -co BLOCKXSIZE=1024 -co BLOCKXSIZE=1024 --cog-profile raw

Default COGEO profiles
======================

Profiles can be extended by providing '--co' option in command line (e.g: rio cogeo mydataset.tif mydataset_zstd.tif -b 1,2,3 --profile deflate --co "COMPRESS=ZSTD" )

**YCbCr**

- JPEG compression
- PIXEL interleave
- YCbCr colorspace
- limited to uint8 datatype and 3 bands data

**ZSTD**

- ZSTD compression
- PIXEL interleave
- Available for GDAL>=2.3.0

**LZW**

- LZW compression
- PIXEL interleave

**DEFLATE**

- DEFLATE compression
- PIXEL interleave

**PACKBITS**

- PACKBITS compression
- PIXEL interleave

**RAW**

- NO compression
- PIXEL interleave

Default profiles are tiled with 512x512 blocksizes.

Contribution & Devellopement
============================

Issues and pull requests are more than welcome.

**dev install**

.. code-block:: console

  $ git clone https://github.com/mapbox/rio-cogeo.git
  $ cd rio-cogeo
  $ pip install -e .[dev]

**Python3.6 only**

This repo is set to use `pre-commit` to run *flake8*, *pydocstring* and *black* ("uncompromising Python code formatter") when commiting new code.

.. code-block:: console

  $ pre-commit install

Extras
======

Checkout **rio-glui** (https://github.com/mapbox/rio-glui/) rasterio plugin to explore COG locally in your web browser.
