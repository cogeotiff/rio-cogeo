

## Web-Optimized COG

rio-cogeo provide a *--web-optimized* option which aims to create a web-tiling friendly COG.

Output dataset features:

- bounds and internal tiles aligned with web-mercator grid (or to a given TMS grid).
- raw data and overviews resolution match the TMS zoom level resolution.

**Important**

Because it will certainly create a larger file (with padding tiles on the side of the file), a nodata value, an alpha band or an internal mask should
be present in the input dataset. If not the original data will be surrounded by black (0) data.


## Internal tile size

By default rio cogeo will create a dataset with 512x512 internal tile size.
This can be updated by passing `--co BLOCKXSIZE=64 --co BLOCKYSIZE=64` options.

**Web tiling optimization**

Creating a Web-Optimized COG, means you'll get a file which is perfectly aligned (bounds and internal tiles) with the mercator grid and with resolution (for the raw data and overview) which map the mercator zoom level resolution. This enable to reduce the number of GET request a dynamic tiling service needs to do to create a map tile from your COG.

if the input dataset is not aligned to web mercator grid, the tiler will need
to fetch multiple internal tiles.

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

### Decimation Base

As described above, a decimation base of 2 is used by default. However you can provide a custom base, N > 1, with *--decimation-base N*. Optimal overviews are computed assuming a base 2 is used, so using *--decimation-base* also requires that *--overview-level* is provided. Similar to the default example, here are the overviews for base 3:

```python
overview_level = 3
decimation_base = 3
overviews = [decimation_base ** j for j in range(1, overview_level + 1)]
print(overviews)
[3, 9, 27]
```

This is primarily useful when working with [custom TileMatrixSets](https://developmentseed.org/morecantile/usage/#define-custom-grid) that also use a non-default decimation base.

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
recommended. Please use internal masking (or alpha band if using webp).
