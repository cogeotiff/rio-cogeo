

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

## Band metadata
By default rio cogeo DO NOT forward **band** metadata (e.g statistics) to the output dataset.

```
$ gdalinfo my_file.tif
...
Band 1 Block=576x1 Type=Float64, ColorInterp=Gray
  NoData Value=999999986991104
  Unit Type: mol mol-1
  Metadata:
    long_name=CO2 Dry-Air Column Average
    missing_value=9.9999999e+14
    NETCDF_DIM_time=0
    NETCDF_VARNAME=XCO2MEAN
    units=mol mol-1
    _FillValue=9.9999999e+14

$ rio cogeo my_file.tif my_cog.tif --blocksize 256

$ gdalinfo my_cog.tif
...
Band 1 Block=256x256 Type=Float64, ColorInterp=Gray
  NoData Value=999999986991104
  Overviews: 288x181
```

You can use `--forward-band-tags` to forwards the band metadata to output dataset.

```
$ rio cogeo create my_file.tif my_cog.tif --blocksize 256 --forward-band-tags
$ gdalinfo my_cog.tif
...
Band 1 Block=256x256 Type=Float64, ColorInterp=Gray
  NoData Value=999999986991104
  Overviews: 288x181
  Metadata:
    long_name=CO2 Dry-Air Column Average
    missing_value=9.9999999e+14
    NETCDF_DIM_time=0
    NETCDF_VARNAME=XCO2MEAN
    units=mol mol-1
    _FillValue=9.9999999e+14
```

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
