# rio-cogeo

<p align="center">
  <img src="https://www.cogeo.org/images/logo/Cog-02.png" style="width: 200px;" alt="COG"></a>
</p>
<p align="center">
  <em>Cloud Optimized GeoTIFF (COG) creation and validation plugin for Rasterio.</em>
</p>
<p align="center">
  <a href="https://github.com/cogeotiff/rio-cogeo/actions?query=workflow%3ACI" target="_blank">
      <img src="https://github.com/cogeotiff/rio-cogeo/workflows/CI/badge.svg" alt="Test">
  </a>
  <a href="https://codecov.io/gh/cogeotiff/rio-cogeo" target="_blank">
      <img src="https://codecov.io/gh/cogeotiff/rio-cogeo/branch/main/graph/badge.svg" alt="Coverage">
  </a>
  <a href="https://pypi.org/project/rio-cogeo" target="_blank">
      <img src="https://img.shields.io/pypi/v/rio-cogeo?color=%2334D058&label=pypi%20package" alt="Package version">
  </a>
  <a href="https://anaconda.org/conda-forge/rio-cogeo" target="_blank">
      <img src="https://img.shields.io/conda/v/conda-forge/rio-cogeo.svg" alt="Conda Forge">
  </a>
  <a href="https://pypistats.org/packages/rio-cogeo" target="_blank">
      <img src="https://img.shields.io/pypi/dm/rio-cogeo.svg" alt="Downloads">
  </a>
  <a href="https://github.com/cogeotiff/rio-cogeo/blob/main/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/cogeotiff/rio-cogeo.svg" alt="Downloads">
  </a>
</p>

---

**Documentation**: <a href="https://cogeotiff.github.io/rio-cogeo/" target="_blank">https://cogeotiff.github.io/rio-cogeo/</a>

**Source Code**: <a href="https://github.com/cogeotiff/rio-cogeo" target="_blank">https://github.com/cogeotiff/rio-cogeo</a>

---


## Cloud Optimized GeoTIFF

This plugin aims to facilitate the creation and validation of Cloud Optimized
GeoTIFF (COG or COGEO). While it respects the
[COG specifications](https://github.com/cogeotiff/cog-spec/blob/master/spec.md), this plugin also
enforces several features:

- **Internal overviews** (User can remove overview with option `--overview-level 0`)
- **Internal tiles** (default profiles have 512x512 internal tiles)

**Important**: in GDAL 3.1 a new COG driver has been added ([doc](https://gdal.org/drivers/raster/cog.html), [discussion](https://lists.osgeo.org/pipermail/gdal-dev/2019-May/050169.html)), starting with `rio-cogeo` version 2.2, `--use-cog-driver` option was added to create COG using the `COG` driver.

## Install

```bash
$ pip install -U pip
$ pip install rio-cogeo
```

Or install from source:

```bash
$ pip install -U pip
$ pip install git+https://github.com/cogeotiff/rio-cogeo.git
```

## GDAL Version

It is recommended to use GDAL > 2.3.2. Previous versions might not be able to
create proper COGs (ref: https://github.com/OSGeo/gdal/issues/754).


More info in https://github.com/cogeotiff/rio-cogeo/issues/55

## More

Blog post on good and bad COG formats: https://medium.com/@_VincentS_/do-you-really-want-people-using-your-data-ec94cd94dc3f

Checkout [rio-glui](https://github.com/mapbox/rio-glui/) or [rio-viz](https://github.com/developmentseed/rio-viz) rasterio plugins to explore COG locally in your web browser.

## Contribution & Development

See [CONTRIBUTING.md](https://github.com/cogeotiff/rio-cogeo/blob/main/CONTRIBUTING.md)

## Changes

See [CHANGES.md](https://github.com/cogeotiff/rio-cogeo/blob/main/CHANGES.md).

## License

See [LICENSE](https://github.com/cogeotiff/rio-cogeo/blob/main/LICENSE)

