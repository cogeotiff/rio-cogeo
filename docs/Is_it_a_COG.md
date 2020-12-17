
# How to recognize a COG and how to create a proper one!

**Requirements**

- python 3.7
- rio-cogeo

`$ pip install rio-cogeo`

The COG Specification is pretty basic

> A cloud optimized GeoTIFF is a regular GeoTIFF file, aimed at being hosted on a HTTP file server, whose internal organization is friendly for consumption by clients issuing HTTP GET range request ("bytes: start_offset-end_offset" HTTP header).
> It contains at its beginning the metadata of the full resolution imagery, followed by the optional presence of overview metadata, and finally the imagery itself. To make it friendly with streaming and progressive rendering, we recommand starting with the imagery of the smallest overview and finishing with the imagery of the full resolution level.

Ref: https://github.com/cogeotiff/cog-spec/blob/master/spec.md

In Short, the specification just means you MUST create a GeoTIFF with internal block (tile) and the header must be ordered.

*From a command line point of view, it just means you need to add `--co TILED=TRUE` in a gdal_translate command.*

## 1. Get some data

Natural Earth web site host really neat raster and vector datasets. Let's download a large scale raster image: https://www.naturalearthdata.com/downloads/50m-raster-data/50m-cross-blend-hypso/


    $ wget https://naciscdn.org/naturalearth/50m/raster/HYP_50M_SR.zip
## 2. Inspect the data

Here is what we want to look at:

- the size in row x lines
- the data type (byte, float, complex …)
- the internal block size
- the presence of overview or not

```
$ rio cogeo info HYP_50M_SR.tif
Driver: GTiff
File: /Users/vincentsarago/Downloads/HYP_50M_SR/HYP_50M_SR.tif
Compression: None
ColorSpace: None

Profile
    Width:            10800
    Height:           5400
    Bands:            3
    Tiled:            False
    Dtype:            uint8
    NoData:           None
    Alpha Band:       False
    Internal Mask:    False
    Interleave:       PIXEL
    ColorMap:         False

Geo
    Crs:              EPSG:4326
    Origin:           (-179.99999999999997, 90.0)
    Resolution:       (0.03333333333333, -0.03333333333333)
    BoundingBox:      (-179.99999999999997, -89.99999999998201, 179.99999999996405, 90.0)

IFD
    Id      Size           BlockSize     Decimation
    0       10800x5400     10800x1       0
```

What we can see from the rio cogeo info output:

- The raster has 3 bands
- The data type is Byte (0 → 255)
- It's not internally tiled (`Tiled: false` and `BlockSize=10800x1`)
- There is no overview (Only one IFD)

With those informations we already know the GeoTIFF is not a COG (no internal blocks), but let's confirm with the validation script.

## 3. COG validation

```
$ rio cogeo validate HYP_50M_SR.tif
The following warnings were found:
- The file is greater than 512xH or 512xW, it is recommended to include internal overviews

The following errors were found:
- The file is greater than 512xH or 512xW, but is not tiled
- The offset of the main IFD should be 8 for ClassicTIFF or 16 for BigTIFF. It is 174982088 instead
- The offset of the first block of the image should be after its IFD
/Users/vincentsarago/Downloads/HYP_50M_SR/HYP_50M_SR.tif is NOT a valid cloud optimized GeoTIFF
```

As mentioned earlier, the validation script confirms the GeoTIFF is not internally tiled and doesn't have overviews.

## 4. COG creation

Creating a valid Cloud Optimized GeoTIFF, is not just about creating internal tiles and/or internal overviews. The file internal structure has to be specific and require a **complete** copy of a file, which is what rio-cogeo does internally.

```
$ rio cogeo create HYP_50M_SR.tif HYP_50M_SR_COG.tif
Reading input: /Users/vincentsarago/Downloads/HYP_50M_SR/HYP_50M_SR.tif
    [####################################]  100%
Adding overviews...
Updating dataset tags...
Writing output to: /Users/vincentsarago/Downloads/HYP_50M_SR/HYP_50M_SR_COG.tif
```

You could get the same COG with GDAL commands

```
$ gdal_translate HYP_50M_SR.tif tmp.tif -co TILED=YES -co COMPRESS=DEFLATE
$ gdaladdo -r nearest tmp.tif 2 4 8 16 32
$ gdal_translate tmp.tif HYP_50M_SR_COG.tif -co TILED=YES -co COMPRESS=DEFLATE -co COPY_SRC_OVERVIEWS=YES
```

By default `rio-cogeo` will create a COG with 512x512 blocksize (for the raw resolution) and use DEFLATE compression to reduce file size.

```
$ rio cogeo info HYP_50M_SR_COG.tif
Driver: GTiff
File: /Users/vincentsarago/Downloads/HYP_50M_SR/HYP_50M_SR_COG.tif
Compression: DEFLATE
ColorSpace: None

Profile
    Width:            10800
    Height:           5400
    Bands:            3
    Tiled:            True
    Dtype:            uint8
    NoData:           None
    Alpha Band:       False
    Internal Mask:    False
    Interleave:       PIXEL
    ColorMap:         False

Geo
    Crs:              EPSG:4326
    Origin:           (-179.99999999999997, 90.0)
    Resolution:       (0.03333333333333001, -0.03333333333333001)
    BoundingBox:      (-179.99999999999997, -89.99999999998204, 179.9999999999641, 90.0)

IFD
    Id      Size           BlockSize     Decimation
    0       10800x5400     512x512       0
    1       5400x2700      128x128       2
    2       2700x1350      128x128       4
    3       1350x675       128x128       8
    4       675x338        128x128       16
```

**The importance of the compression**

```
$ ls -lah
-rw-r--r--@  1 youpi  staff   167M Oct 18  2014 HYP_50M_SR.tif
-rw-r--r--   1 youpi  staff    58M Jun 12 14:56 HYP_50M_SR_COG.tif
```


By using `rio-cogeo`, we are not only creating a valid COG with internal tiling but we are also adding internal overviews (which let us get previews of the raw resolution with few GET requests).

Even with the addition of 4 levels of overviews (see **IFD** section in previous  `rio cogeo info` output), we managed to reduce the file size by 3 (167Mb → 58Mb), and this is because rio cogeo applies **Deflate** compression by default to the COG.

**More Magic ?**

As seen in the first `rio cogeo info` output, the data has 3 bands (RGB) and is of Uint8 data type. Because of this configuration, we can use even more efficient compression like JPEG or WEBP.

```
$ rio cogeo create HYP_50M_SR.tif HYP_50M_SR_COG_jpeg.tif -p jpeg
Reading input: /Users/vincentsarago/Downloads/HYP_50M_SR/HYP_50M_SR.tif
    [####################################]  100%
Adding overviews...
Updating dataset tags...
Writing output to: /Users/vincentsarago/Downloads/HYP_50M_SR/HYP_50M_SR_COG_jpeg.tif

$ ls -lah
-rw-r--r--@  1 vincentsarago  staff   167M Oct 18  2014 HYP_50M_SR.tif
-rw-r--r--   1 vincentsarago  staff    58M Jun 12 14:56 HYP_50M_SR_COG.tif
-rw-r--r--   1 vincentsarago  staff   4.8M Jun 15 11:08 HYP_50M_SR_COG_jpeg.tif
```

Now, our output file is only **4.8Mb,** which is only ~3% of the original size 😱.

Note:

- JPEG compression is not lossless but **lossy**, meaning we will loose some information (change in pixel values) but if you need a COG for visual purposes the gain in size might be worth it.
- WEBP compression has a configuration option to be lossless and will result is a file which will be ~50% smaller than the deflate version. Sadly WEBP is not provided by default in geospatial software.

## 5. Visualize

You can either load the COG in QGIS or use our plugin (rio-viz) to load it in a web browser.

```
$ pip install rio-viz
$ rio viz HYP_50M_SR_COG.tif
```

![](https://user-images.githubusercontent.com/10407788/84684622-ea130100-af06-11ea-8e13-e9d27fc43afc.png)
