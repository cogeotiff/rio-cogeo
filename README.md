# rio-cogeo

Cloud Optimized GeoTIFF (COG) creation and validation plugin for Rasterio


[![Packaging status](https://badge.fury.io/py/rio-cogeo.svg)](https://badge.fury.io/py/rio-cogeo)
[![CircleCI](https://circleci.com/gh/cogeotiff/rio-cogeo.svg?style=svg)](https://circleci.com/gh/cogeotiff/rio-cogeo)
[![codecov](https://codecov.io/gh/cogeotiff/rio-cogeo/branch/master/graph/badge.svg)](https://codecov.io/gh/cogeotiff/rio-cogeo)

## Cloud Optimized GeoTIFF

This plugin aim to facilitate the creation and validation of Cloud Optimized
GeoTIFF (COG or COGEO). While it respects the
[COG specifications](https://github.com/cogeotiff/cog-spec/blob/master/spec.md), this plugin also
enforce several features:

- **Internal overviews** (User can remove overview with option `--overview-level 0`)
- **Internal tiles** (default profiles have 512x512 internal tiles)

**Important**: Starting from GDAL 3.1 a new COG generator driver will be added ([doc](https://gdal.org/drivers/raster/cog.html), [discussion](https://lists.osgeo.org/pipermail/gdal-dev/2019-May/050169.html)) and will make `rio-cogeo` kinda obsolete.

## Install

```bash
$ pip install -U pip
$ pip install rio-cogeo
```

Or install from source:

```
$ git clone https://github.com/cogeotiff/rio-cogeo.git
$ cd rio-cogeo
$ pip install -U pip
$ pip install -e .
```

## CLI


```
$ rio cogeo --help
  Usage: rio cogeo [OPTIONS] COMMAND [ARGS]...

  Rasterio cogeo subcommands.

  Options:
    --help  Show this message and exit.

  Commands:
    create    Create COGEO
    validate  Validate COGEO
```

- Create a Cloud Optimized Geotiff.

```
$ rio cogeo create --help
  Usage: rio cogeo create [OPTIONS] INPUT OUTPUT

  Create Cloud Optimized Geotiff.

  Options:
    -b, --bidx BIDX                 Band indexes to copy.
    -p, --cog-profile [jpeg|webp|zstd|lzw|deflate|packbits|lzma|lerc|lerc_deflate|lerc_zstd|raw]
                                    CloudOptimized GeoTIFF profile (default: deflate).
    --nodata NUMBER|nan             Set nodata masking values for input dataset.
    --add-mask                      Force output dataset creation with an internal mask (convert alpha band or nodata to mask).
    -t, --dtype [ubyte|uint8|uint16|int16|uint32|int32|float32|float64]
                                    Output data type.
    --overview-level INTEGER        Overview level (if not provided, appropriate overview level will be selected
                                    until the smallest overview is smaller than the value of the internal blocksize)
    --overview-resampling [nearest|bilinear|cubic|cubic_spline|lanczos|average|mode|gauss] Overview creation resampling algorithm.
    --overview-blocksize TEXT       Overview's internal tile size (default defined by GDAL_TIFF_OVR_BLOCKSIZE env or 128)
    -w, --web-optimized             Create COGEO optimized for Web.
    --latitude-adjustment / --global-maxzoom
                                    Use dataset native mercator resolution for MAX_ZOOM calculation (linked to dataset center latitude, default)
                                    or ensure MAX_ZOOM equality for multiple dataset accross latitudes.
    -r, --resampling [nearest|bilinear|cubic|cubic_spline|lanczos|average|mode|gauss] Resampling algorithm.
    --in-memory / --no-in-memory    Force processing raster in memory / not in memory (default: process in memory if smaller than 120 million pixels)
    --allow-intermediate-compression
                                    Allow intermediate file compression to reduce memory/disk footprint.
    --forward-band-tags             Forward band tags to output bands.
    --threads THREADS               Number of worker threads for multi-threaded compression (default: ALL_CPUS)
    --co, --profile NAME=VALUE      Driver specific creation options. See the documentation for the selected GTiff driver for more information.
    -q, --quiet                     Remove progressbar and other non-error output.
    --help                          Show this message and exit.
```

- Check if a Cloud Optimized Geotiff is valid.

```
$ rio cogeo validate --help
Usage: rio cogeo validate [OPTIONS] INPUT

  Validate Cloud Optimized Geotiff.

Options:
  --strict  Treat warnings as errors.
  --help    Show this message and exit.
```

The `strict` options will treat warnings (e.g missing overviews) as errors.

### Examples

```bash
# Create a COGEO with DEFLATE compression (Using default `Deflate` profile)
$ rio cogeo create mydataset.tif mydataset_jpeg.tif

# Validate COGEO
$ rio cogeo validate mydataset_jpeg.tif

# Create a COGEO with JPEG profile and the first 3 bands of the data and add internal mask
$ rio cogeo create mydataset.tif mydataset_jpeg.tif -b 1,2,3 --add-mask --cog-profile jpeg
```

## Default COGEO profiles

Default profiles are tiled with 512x512 blocksizes.

**JPEG**

- JPEG compression
- PIXEL interleave
- YCbCr (3 bands) colorspace or MINISBLACK (1 band)
- limited to uint8 datatype and 3 bands data

**WEBP**

- WEBP compression
- PIXEL interleave
- limited to uint8 datatype and 3 or 4 bands data
- Non-Standard, might not be supported by software not build against GDAL+internal libtiff + libwebp
- Available for GDAL>=2.4.0

**ZSTD**

- ZSTD compression
- PIXEL interleave
- Non-Standard, might not be supported by software not build against GDAL + internal libtiff + libzstd
- Available for GDAL>=2.3.0

*Note* in Nov 2018, there was a change in libtiff's ZSTD tags which create incompatibility for old ZSTD compressed GeoTIFF [(link)](https://lists.osgeo.org/pipermail/gdal-dev/2018-November/049289.html)

**LZW**

- LZW compression
- PIXEL interleave

**DEFLATE**

- DEFLATE compression
- PIXEL interleave

**PACKBITS**

- PACKBITS compression
- PIXEL interleave

**LZMA**

- LZMA compression
- PIXEL interleave

**LERC**

- LERC compression
- PIXEL interleave
- Default MAX_Z_ERROR=0 (lossless)
- Non-Standard, might not be supported by software not build against GDAL + internal libtiff
- Available for GDAL>=2.4.0

**LERC_DEFLATE**

- LERC_DEFLATE compression
- PIXEL interleave
- Default MAX_Z_ERROR=0 (lossless)
- Non-Standard, might not be supported by software not build against GDAL + internal libtiff + libzstd
- Available for GDAL>=2.4.0

**LERC_ZSTD**

- LERC_ZSTD compression
- PIXEL interleave
- Default MAX_Z_ERROR=0 (lossless)
- Non-Standard, might not be supported by software not build against GDAL + internal libtiff + libzstd
- Available for GDAL>=2.4.0

**RAW**

- NO compression
- PIXEL interleave

**Profiles can be extended by providing '--co' option in command line**


```bash
# Create a COGEO without compression and with 1024x1024 block size and 256 overview blocksize
$ rio cogeo create mydataset.tif mydataset_raw.tif --co BLOCKXSIZE=1024 --co BLOCKYSIZE=1024 --cog-profile raw --overview-blocksize 256
```

See https://gdal.org/drivers/raster/gtiff.html#creation-options for full details of creation options.

## API

Rio-cogeo can also be integrated directly in your custom script. See [rio_cogeo.cogeo.cog_translate](https://github.com/cogeotiff/rio-cogeo/blob/master/rio_cogeo/cogeo.py#L53-L108) function.

e.g:

```python
from rio_cogeo.cogeo import cog_translate

def _translate(src_path, dst_path, profile="webp", profile_options={}, **options):
    """Convert image to COG."""
    # Format creation option (see gdalwarp `-co` option)
    output_profile = cog_profiles.get(profile)
    output_profile.update(dict(BIGTIFF="IF_SAFER"))
    output_profile.update(profile_options)

    # Dataset Open option (see gdalwarp `-oo` option)
    config = dict(
        GDAL_NUM_THREADS="ALL_CPUS",
        GDAL_TIFF_INTERNAL_MASK=True,
        GDAL_TIFF_OVR_BLOCKSIZE="128",
    )

    cog_translate(
        src_path,
        dst_path,
        output_profile,
        config=config,
        in_memory=False,
        quiet=True,
        **options,
    )
    return True
```
ref: https://github.com/developmentseed/cogeo-watchbot/blob/81df27470dd2eb7032d512c35af853b006d1c035/app/translator.py#L34-L56


### Using the API with in MemoryFile

1. Create COG from numpy array
```python
import numpy

import mercantile

from rasterio.io import MemoryFile
from rasterio.transform import from_bounds

from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

# Create GeoTIFF profile
bounds = mercantile.bounds(mercantile.Tile(0,0,0))
src_transform = from_bounds(*bounds, 1024 1024)

src_profile = dict(
    driver="GTiff",
    dtype="float32",
    count=3,
    height=1024,
    width=1024,
    crs="epsg:4326",
    transform=dst_transform,
)

img_array = tile = numpy.random.rand(3, 1024, 1024)

with MemoryFile() as memfile:
    with memfile.open(**src_profile) as mem:
        # Populate the input file with numpy array
        mem.write(img_array)
        
        dst_profile = cog_profiles.get("deflate")        
        cog_translate(
            mem,
            "my-output-cog.tif",
            dst_profile,
            in_memory=True,
            quiet=True,
        )
```
2. Create output COG in Memory

```python
from rasterio.io import MemoryFile

from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

from boto3.session import Session as boto3_session

dst_profile = cog_profiles.get("deflate")

with MemoryFile() as mem_dst:
    # Important, we pass `mem_dst.name` as output dataset path
    cog_translate("my-input-file.tif", mem_dst.name, profile, in_memory=True)

    # You can then use the memoryfile to do something else like
    # upload to AWS S3
    client = boto3_session.client("s3")
    client.upload_fileobj(mem_dst, "my-bucket", "my-key")
```


## Web-Optimized COG

rio-cogeo provide a *--web-optimized* option which aims to create a web-tiling friendly COG.

Output dataset features:

- bounds and internal tiles aligned with web-mercator grid.
- raw data and overviews resolution match mercator zoom level resolution.

**Important**

Because the mercator projection does not respect the distance, when working with
multiple images covering different latitudes, you may want to use the *--global-maxzoom* option
to create output dataset having the same MAX_ZOOM (raw data resolution).

Because it will certainly create a larger file, a nodata value or alpha band should
be present in the input dataset. If not the original data will be surrounded by black (0) data.


## Internal tile size

By default rio cogeo will create a dataset with 512x512 internal tile size.
This can be updated by passing `--co BLOCKXSIZE=64 --co BLOCKYSIZE=64` options.

**Web tiling optimization**

if the input dataset is aligned to web mercator grid, the internal tile size
should be equal to the web map tile size (256 or 512px). Dataset should be compressed.

if the input dataset is not aligned to web mercator grid, the tiler will need
to fetch multiple internal tiles. Because GDAL can merge range request, using
small internal tiles (e.g 128) will reduce the number of byte transfered and
minimized the useless bytes transfered.


GDAL configuration to merge consecutive range requests

```
GDAL_HTTP_MERGE_CONSECUTIVE_RANGES=YES
GDAL_HTTP_MULTIPLEX=YES
GDAL_HTTP_VERSION=2
```

## Overview levels

By default rio cogeo will calculate the optimal overview level based on dataset
size and internal tile size (overview should not be smaller than internal tile
size (e.g 512px). Overview level will be translated to decimation level of
power of two:

```python
overview_level = 3
overviews = [2 ** j for j in range(1, overview_level + 1)]
print(overviews)
[2, 4, 8]
```

## GDAL Version

It is recommanded to use GDAL > 2.3.2. Previous version might not be able to
create proper COGs (ref: https://github.com/OSGeo/gdal/issues/754).


More info in https://github.com/cogeotiff/rio-cogeo/issues/55


## Nodata, Alpha and Mask

By default rio-cogeo will forward any nodata value or alpha channel to the
output COG.

If your dataset type is **Byte** or **Unit16**, you could use internal bit mask
(with the `--add-mask` option) to replace the Nodata value or Alpha band in
output dataset (supported by most GDAL based backends).

Note: when adding a `mask` with an input dataset having an alpha band you'll
need to use the `bidx` options to remove it from the output dataset.

```bash
# Replace the alpha band by an internal mask
$ rio cogeo mydataset_withalpha.tif mydataset_withmask.tif --cog-profile raw --add-mask --bidx 1,2,3
```

**Important**

Using internal nodata value with lossy compression (`webp`, `jpeg`) is not
recommanded. Please use internal masking (or alpha band if using webp).

## Contribution & Development

The rio-cogeo project was begun at Mapbox and has been transferred to the
CogeoTIFF organization in January 2019.

Issues and pull requests are more than welcome.

**dev install**

```bash
$ git clone https://github.com/cogeotiff/rio-cogeo.git
$ cd rio-cogeo
$ pip install -e .[dev]
```

**Python3.6 only**

This repo is set to use `pre-commit` to run *flake8*, *pydocstring* and *black*
("uncompromising Python code formatter") when commiting new code.

```bash
$ pre-commit install
```

## Extras

Blog post on good and bad COG formats: https://medium.com/@_VincentS_/do-you-really-want-people-using-your-data-ec94cd94dc3f

Checkout [rio-glui](https://github.com/mapbox/rio-glui/) or [rio-viz](https://github.com/developmentseed/rio-viz) rasterio plugins to explore COG locally in your web browser.
