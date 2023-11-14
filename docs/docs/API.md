

**rio-cogeo** can also be integrated directly in your custom script. See [rio_cogeo.cogeo.cog_translate](https://github.com/cogeotiff/rio-cogeo/blob/master/rio_cogeo/cogeo.py#L53-L108) function.

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


## Using the API with in MemoryFile

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

# Rasterio uses numpy array of shape of `(bands, height, width)`
width = 1024
height = 1024
nbands = 3

img_array = tile = numpy.random.rand(nbands, height, width).astype(numpy.float32)

src_transform = from_bounds(*bounds, width=width, height=height)

src_profile = dict(
    driver="GTiff",
    dtype="float32",
    count=nbands,
    height=height,
    width=width,
    crs="epsg:4326",
    transform=src_transform,
)


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
    cog_translate("my-input-file.tif", mem_dst.name, dst_profile, in_memory=True)

    # You can then use the memoryfile to do something else like
    # upload to AWS S3
    client = boto3_session.client("s3")
    client.upload_fileobj(mem_dst, "my-bucket", "my-key")
```

3. Progress to TextIO

```python
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

config = dict(
    GDAL_NUM_THREADS="ALL_CPUS",
    GDAL_TIFF_INTERNAL_MASK=True,
    GDAL_TIFF_OVR_BLOCKSIZE="128",
)

with open("logfile.txt", "w+") as example:
    cog_translate(
        "example-input.tif",
        "example-output.tif",
        cog_profiles.get("deflate"),
        config=config,
        in_memory=False,
        nodata=0,
        quiet=False,
        progress=example
    )
```
