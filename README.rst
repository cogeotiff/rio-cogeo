=========
rio-cogeo
=========

CloudOptimized GeoTIFF (COGEO) creation plugin for rasterio


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

.. code-block:: console

  $ rio cogeo --help
  Usage: rio cogeo [OPTIONS] COMMAND [ARGS]...

    Rasterio cogeo subcommands.

  Options:
    --help  Show this message and exit.

  Commands:
    create    Create a COGEO
    validate  Validate COGEO

- Create a Cloud Optimized Geotiff.

.. code-block::

  $ rio cogeo --help
  Usage: rio cogeo [OPTIONS] INPUT OUTPUT

    Create Cloud Optimized Geotiff.

  Options:
    -b, --bidx BIDX                 Band index to copy (default: 1,2,3)
    -p, --cog-profile [ycbcr|lzw|deflate|packbits|raw]
                                    CloudOptimized GeoTIFF profile (default: ycbcr)
    --nodata INTEGER                Force mask creation from a given nodata value
    --alpha INTEGER                 Force mask creation from a given alpha band number
    --overview-level INTEGER        Overview level (default: 6)
    --threads INTEGER
    --co, --profile NAME=VALUE      Driver specific creation options.See the
                                    documentation for the selected output driver
                                    for more information.
    --help                          Show this message and exit.

- Check if a Cloud Optimized Geotiff is valid.

.. code-block::

  $ rio cogeo validate --help
  Usage: rio cogeo validate [OPTIONS] INPUT

    Validate Cloud Optimized Geotiff.

  Options:
    --help  Show this message and exit.


Examples
========

.. code-block:: console

  # Create a COGEO with YCbCR profile and the first 3 bands of the data
  $ rio cogeo create mydataset.tif mydataset_ycbcr.tif -b 1,2,3

  # Create a COGEO without compression and wiht 1024x1024 block size
  $ rio cogeo create mydataset.tif mydataset_raw.tif -co BLOCKXSIZE=1024 -co BLOCKXSIZE=1024 --cog-profile raw

  # Check if mydataset_ycbcr.tif is a valid COGEO
  $ rio cogeo validate mydataset_ycbcr.tif


Defaults COGEO profiles
=======================

Disclaimer: The defaults profiles provided by `rio-cogeo` stands for example and are might not fit your use case.

**YCbCr**

- JPEG compression
- PIXEL interleave
- YCbCr colorspace
- limited to uint8 datatype and 3 bands data

**LZW**

- LZW compression
- PIXEL interleave

**DEFLATE**

- DEFLATE compression
- PIXEL interleave

**PACKBITS**

- PACKBITS compression
- BAND interleave


**RAW**

- NO compression
- PIXEL interleave

Defaults profiles are tiled with 512x512 blocksizes
