# Release Notes

# 3.0.1 (2021-10-27)

* update `test` and `dev` dependencies to `rio-tiler>=3.0.0a0`

# 3.0.0 (2021-09-30)

* no changes since 3.0.0a0

# 3.0.0a0 (2021-09-23)

* update to `morecantile>=3.0`
* raise warning when using incompatible options for GDAL COG driver (https://github.com/cogeotiff/rio-cogeo/pull/212)

# 2.3.1 (2021-07-06)

* update `click` version requirement to `>=7.0` to make sure `click.Choice` supports the `case_sensitive` option.

# 2.3.0 (2021-06-25)

* allow external configuration (GDAL Env) for `cog_validate` (https://github.com/cogeotiff/rio-cogeo/pull/206)

  ```python
  from rio_cogeo import cog_validate

  assert cog_validate("cog.tif", congig={"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR"})[0]
  ```

  In previous version we were forcing `GDAL_DISABLE_READDIR_ON_OPEN=FALSE` in `cog_validate` function to check for external overviews.

  Starting with version 2.3, it's up to the user to set the wanted GDAL configuration (e.g `EMPTY_DIR`: no external file check, `FALSE`: check for external files)


# 2.2.3 (2021-06-18)

* use opened file for click progressbar (https://github.com/cogeotiff/rio-cogeo/pull/204)

# 2.2.2 (2021-06-01)

* Add dictionary access to `Info` model (author @geospatial-jeff, https://github.com/cogeotiff/rio-cogeo/pull/201)
* remove unsupported resampling method for Warping in CLI options (author @drnextgis, https://github.com/cogeotiff/rio-cogeo/pull/202)

# 2.2.1 (2021-05-19)

* replace missing rio-tiler dependencies with a custom BBox type definition (https://github.com/cogeotiff/rio-cogeo/pull/198)

# 2.2.0 (2021-05-18)

* add pydantic models for `info` output (https://github.com/cogeotiff/rio-cogeo/issues/191)
* add `use_cog_driver` option to create COG using new GDAL COG Driver (https://github.com/cogeotiff/rio-cogeo/pull/194)

**Breaking Changes:**

* `rio_cogeo.cogeo.cog_info` now returns a pydantic model

```python
from rio_cogeo.cogeo import cog_info

# before
info = cog_info("my.tif")
assert isinstance(info, dict)
assert info["GEO"]["CRS"]

# now
assert isinstance(info, rio_cogeo.models.Info)
assert info.GEO.CRS
```

* add `TILING SCHEME` in dataset namespaced metadata when creating WebOptimized COG (https://github.com/cogeotiff/rio-cogeo/pull/193)
* add more info in rio cogeo info `Tags` (https://github.com/cogeotiff/rio-cogeo/pull/193)

```python
# before
$ rio cogeo create in.tif out.tif -w
$ rio cogeo info out.tif | jq .Tags

>>> {
  "AREA_OR_POINT": "Area",
  "OVR_RESAMPLING_ALG": "NEAREST"
}

# now
$ rio cogeo create in.tif out.tif -w
$ rio cogeo info out.tif | jq .Tags
>> {
  "Image Metadata": {
    "AREA_OR_POINT": "Area",
    "DataType": "Generic",
    "OVR_RESAMPLING_ALG": "NEAREST"
  },
  "Image Structure": {
    "COMPRESSION": "DEFLATE",
    "INTERLEAVE": "BAND",
    "LAYOUT": "COG"
  },
  "Tiling Scheme": {
    "NAME": "WEBMERCATORQUAD",
    "ZOOM_LEVEL": "17"
  }
}
```

* update `Web-Optimized` configuration to match GDAL COG Driver (https://github.com/cogeotiff/rio-cogeo/pull/193)

  By default only the `raw` data will be aligned to the grid. To align overviews, the `aligned_levels` option can be used (wasn't really working in previous version).

* `rio_cogeo.utils.get_web_optimized_params` has been refactored (https://github.com/cogeotiff/rio-cogeo/pull/193)

* `cog_translate` will now materialize **Nodata or Alpha band** to an internal **mask** automatically for JPEG compresssed output (https://github.com/cogeotiff/rio-cogeo/pull/196)

```python
# before
cog_translate(raster_path_rgba, "cogeo.tif", jpeg_profile)
with rasterio.open("cogeo.tif") as src:
    assert src.count == 4
    assert src.compression.value == "JPEG"
    assert has_alpha_band(src)
    assert not has_mask_band(src)

# now
cog_translate(raster_path_rgba, "cogeo.tif", jpeg_profile)
with rasterio.open("cogeo.tif") as src:
    assert src.count == 3
    assert src.compression.value == "JPEG"
    assert has_mask_band(src)
```

# 2.1.4 (2021-03-31)

* fix issue in validation when BLOCK_OFFSET_0 is None (https://github.com/cogeotiff/rio-cogeo/issues/182)

# 2.1.3 (2021-03-03)

* add **colormap** options in `cog_translate` to allow a user to set or update a colormap

```python
cmap = {0: (0, 0, 0, 0), 1: (1, 2, 3, 255)}
cog_translate("boring.tif", "cogeo.tif", deflate_profile, colormap=cmap)
with rasterio.open("cogeo.tif") as cog:
    print(cog.colormap(1)[1])

>>> (1, 2, 3, 255)
```

* add **additional_cog_metadata** options in `cog_translate` to allow the user to add more dataset metadatas

```python
cog_translate("boring.tif", "cogeo.tif", deflate_profile, additional_cog_metadata={"comments": "I made this tiff with rio-cogeo"})

with rasterio.open("cogeo.tif") as cog:
    print(cog.tags()["comment"])

>>> "I made this tiff with rio-cogeo"
```

# 2.1.2 (2021-02-10)

* remove useless path translation to pathlib and avoid side effect when using a URL (https://github.com/cogeotiff/rio-cogeo/issues/178)

# 2.1.1 (2021-01-27)

* drop support for Python 3.5 (https://github.com/cogeotiff/rio-cogeo/issues/173)
* allow pathlib.PurePath object as input and output (https://github.com/cogeotiff/rio-cogeo/issues/173)
* add top-level exports (https://github.com/cogeotiff/rio-cogeo/issues/169)

```python
# before
from rio_cogeo.cogeo import cog_translate, cog_validate, cog_info
from rio_cogeo.profiles import cog_profiles

# now
from rio_cogeo import cog_translate, cog_validate, cog_info, cog_profiles
```

## 2.1.0 (2020-12-18)

* switch to `morecantile` and update the web-optimized creation method to better match GDAL 3.2.
* add `zoom_level_strategy` options to match GDAL 3.2 COG driver.
* add `aligned_levels` (cli and api) to select the level of overview to align with the TMS grid.

**Breaking Changes:**
* removed `--latitude-adjustment/--global-maxzoom` option in the CLI
* removed `latitude_adjustment` option in `rio_cogeo.cogeo.cog_translate`
* updated **overview blocksize** to match the blocksize of the high resolution data (instead of default to 128)
* for web-optimized COG, the highest overview level will be aligned with the TMS grid.

## 2.0.1 (2020-10-07)

* remove `pkg_resources` (https://github.com/pypa/setuptools/issues/510)

## 2.0.0 (2020-10-05)

There have been no changes since 2.0a9

## 2.0a9 (2020-10-03)

* Update max IFD offset to 300 bytes (https://github.com/cogeotiff/rio-cogeo/issues/158)

## 2.0a8 (2020-09-28)

* Make sure Alpha band isn't considered as an internal mask by `utils.has_mask_band` (#156)

## 2.0a7.post1 (2020-09-23)

* Fix wrong min-zoom calculation in `rio_cogeo.cogeo.cog_info`

## 2.0a7 (2020-09-23)
* remove duplicate `count` information in rio_cogeo.cogeo.cog_info output (#150)
* allow COG with IFD offset up to 200 bytes to accomodate with GDAL 3.1 changes (#151)
* fix zoom level calculation in `rio_cogeo.cogeo.cog_info`

## 2.0a6 (2020-08-18)

* fix bug in cogeo.info when CRS in not set.
* add minzoom/maxzoom in cogeo.info output.

**Breaking Changes:**
* rio_cogeo.utils.get_max_zoom renamed rio_cogeo.utils.get_zooms and now return min/max zoom.

## 2.0a5 (2020-07-31)

* move most of the cogeo info code in rio_cogeo.cogeo.cog_info api
* add cog_validation info in cogeo info result
* cog_validate returns a tuple (is_valid, errors, warnings) (#142, co-author with @geospatial-jeff)
* add scale, offset, image tags and band color interpretation in cog_info (#145, #146 and #147)

## 2.0a4 (2020-06-15)

* Force output width and height (#140)

## 2.0a3 (2020-06-15)

* add `info` CLI (#134)
* use `Deflate` as default temporary compression (#137)

## 2.0a2 (2020-05-20)

* add `--config` CLI option to pass additional GDAL Configuration options (#135)

## 2.0a1 (2020-05-07)

* **Dropping python 2** (#128)
* use new mercantile xy_bounds for better web-optimized file (#126)
* Allow temporary file on disk when using MemoryFile output
* add `--blocksize` option in CLI (#131)
* depreciate `rio_cogeo.utils.get_maximum_overview_level` and use rasterio.rio.overview.get_maximum_overview_level (#132)

## 1.1.10 (2020-02-21)

* Transfer colormap (#121)

## 1.1.9 (2020-02-06)

* Transfer scale and offset values to output COG (#118)

## 1.1.8 (2020-01-08)

* Transfer color interpretation value to output COG (#113) * Thanks @pierotofy
* Cast `dataset_mask` returned by rasterio to uint8 to overcome a bug in rasterio 1.1.2 (#115)

## 1.1.7 (2019-12-02)

* add `strict` option to cog_validate to treat warnings as error (#109) * Thanks @pierotofy
* add documentation examples using MemoryFiles (#108 #107)
* Switch to `PHOTOMETRIC=MINISBLACK` when PHOTOMETRIC is set to YCBCR for 1 band dataset (#41)

## 1.1.6 (2019-11-13)

* add `-forward-band-tags` options (#115)

## 1.1.5 (2019-10-04)

* add `--allow-intermediate-compression` option to reduce the memory/disk footprint (#103)

## 1.1.4 (2019-10-03)

* Fix support for optimizing open datasets, memfiles, and VRTs (#100 from j08lue)

## 1.1.3 (2019-09-16)

* Add lzma/lerc/lerc_deflate/lerc_zstd profiles (#97)
* Add warnings and notes for `non-standard` compression (#97)
* fix THREADS definition for GDAL config

## 1.1.2 (2019-09-12)

* Fix incorrect context behavior closing input Dataset (#94)

## 1.1.1 (2019-09-10)

* add safeguard to keep datatype from input to output files (#85)

**CLI Changes:**
* add `-t, --dtype` datatype option.

**API Changes:**
* add datatype option
* update for rasterio>=1.0.28
* allow rasterio.io.DatasetReader input (#89)

Note: This release was deleted in PyPi.

## 1.1.0 (2019-07-16)

* check internal blocksize and adapt if raster is too small (#80)

## 1.0.0 (2019-04-19)

* add `--web-optimized` option to create a web optimized COG (#10)
* add `--latitude-adjustment/--global-maxzoom` option to adjust MAX_ZOOM for global datasets
* Web-optimized tests needs python3.6 (cogdumper)
* add `--resampling` option to select the resampling algorithm when using `--web-optimized`
* add `--in-memory/--no-in-memory` options to use temporyNamedd file instead of in-memory temp file.

## 1.0b3 (2019-03-30)

**Breaking Changes:**

* remove deprecated YCBCR profile
* 512x512 dataset without internal tiling are valid

## 1.0b2 (2019-03-27)

**Breaking Changes:**

* Switch from JPEG to DEFLATE as default profile in CLI (#66)

## 1.0b1 (2019-03-25)

**Breaking Changes:**

* refactor utils.get_maximum_overview_level to get rasterio dataset
as input and reduce the number of dataset opennings (#61)

## 1.0b0 (2019-03-15)

* add more logging and `--quiet` option (#46)
* add `--overview-blocksize` to set overview's internal tile size (#60)

**Bug fixes:**

* copy tags and description from input to output (#19)
* copy input mask band to output mask

**Breaking Changes:**

* rio cogeo now has subcommands: 'create' and 'validate' (#6).
* internal mask creation is now optional (--add-mask).
* internal nodata or alpha channel can be forwarded to the output dataset.
* removed default overview blocksize to be equal to the raw data blocksize (#60)

## 1.0dev10 (2019-02-12)

* allow non integer nodata value (#51)
* fix GDAL blocksize options casting for overview calculation (#50)

## 1.0dev9 (2019-02-11)

* Renamed "ycbcr" profile's name to "jpeg" to reflect the compression name.
  "ycbcr" profile will raise a "DeprecationWarning" (#44)
* "webp" profile has been added to COG profiles. Exploitation of this new
  compression mode will require GDAL 2.4 (#27)
* Rio-cogeo can calculate the overview level based on the internal tile size
  and the dataset width/height (#37)

## 1.0dev8 (2018-10-02)

* write tags in output file (#31)
* add bilinear, cubic spline, lanczos resampling modes for overviews

## 1.0dev7 (2018-09-12)

* add resampling option for overviews (#28)

## 1.0dev6 (2018-08-23)

* Remove unnecessary compression for in-memory step (reduce runtime and memory usage) (#25)

## 1.0dev4 (2018-07-16)

* rasterio 1.0

## 1.0dev3 (2018-07-05)

* remove default bidx in cli (#17)

## 1.0dev2 (2018-06-28)

* Add ZSTD compressed COG profile (#14)
* Fix warnings for useless boundless=True option (#13)
* add BIGTIFF=IF_SAFER to COG profile (if BIGTIFF not set otherwise in the env)

**Breaking Changes:**
* replace "BAND" by "PIXEL" interleave in PACKBITS profile (#16)

## 1.0dev1(2018-16-13)

* Initial release. Requires Rasterio >= 1.0b1.
