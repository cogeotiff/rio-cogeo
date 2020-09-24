
rio-cogeo defines default Cloud Optimized GeoTIFF profiles which user can use with the CLI or directly with the API.

Default profiles are **tiled** (`tiled=True`) with **512x512 blocksizes**.

```python
from rio_cogeo.profiles import cog_profiles

cog_profiles
> {
    'jpeg': {'driver': 'GTiff', 'interleave': 'pixel', 'tiled': True, 'blockxsize': 512, 'blockysize': 512, 'compress': 'JPEG', 'photometric': 'YCbCr'},
    'webp': {'driver': 'GTiff', 'interleave': 'pixel', 'tiled': True, 'blockxsize': 512, 'blockysize': 512, 'compress': 'WEBP'},
    'zstd': {'driver': 'GTiff', 'interleave': 'pixel', 'tiled': True, 'blockxsize': 512, 'blockysize': 512, 'compress': 'ZSTD'},
    'lzw': {'driver': 'GTiff', 'interleave': 'pixel', 'tiled': True, 'blockxsize': 512, 'blockysize': 512, 'compress': 'LZW'},
    'deflate': {'driver': 'GTiff', 'interleave': 'pixel', 'tiled': True, 'blockxsize': 512, 'blockysize': 512, 'compress': 'DEFLATE'}
    'packbits': {'driver': 'GTiff', 'interleave': 'pixel', 'tiled': True, 'blockxsize': 512, 'blockysize': 512, 'compress': 'PACKBITS'},
    'lzma': {'driver': 'GTiff', 'interleave': 'pixel', 'tiled': True, 'blockxsize': 512, 'blockysize': 512, 'compress': 'LZMA'},
    'lerc': {'driver': 'GTiff', 'interleave': 'pixel', 'tiled': True, 'blockxsize': 512, 'blockysize': 512, 'compress': 'LERC'},
    'lerc_deflate': {'driver': 'GTiff', 'interleave': 'pixel', 'tiled': True, 'blockxsize': 512, 'blockysize': 512, 'compress': 'LERC_DEFLATE'},
    'lerc_zstd': {'driver': 'GTiff', 'interleave': 'pixel', 'tiled': True, 'blockxsize': 512, 'blockysize': 512, 'compress': 'LERC_ZSTD'},
    'raw': {'driver': 'GTiff', 'interleave': 'pixel', 'tiled': True, 'blockxsize': 512, 'blockysize': 512}
}
```

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


## Custom

Profiles can be extended by providing '--co' option in command line

```bash
# Create a COGEO without compression and with 1024x1024 block size and 256 overview blocksize
$ rio cogeo create mydataset.tif mydataset_raw.tif --co BLOCKXSIZE=1024 --co BLOCKYSIZE=1024 --cog-profile raw --overview-blocksize 256
```

See https://gdal.org/drivers/raster/gtiff.html#creation-options for full details of creation options.
