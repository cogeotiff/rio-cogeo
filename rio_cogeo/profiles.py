"""rio_cogeo.profiles: CloudOptimized profiles."""

from rasterio.profiles import Profile
from rasterio.dtypes import uint8


class YCbCrProfile(Profile):
    """Tiled, pixel-interleaved, JPEG-compressed, YCbCr colorspace, 8-bit GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "JPEG",
        "photometric": "YCbCr",
        "dtype": uint8,
    }


class LZWProfile(Profile):
    """Tiled, pixel-interleaved, LZW-compressed GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "LZW",
    }


class DEFLATEProfile(Profile):
    """Tiled, pixel-interleaved, DEFLATE-compressed GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "DEFLATE",
    }


class PACKBITSProfile(Profile):
    """Tiled, pixel-interleaved, PACKBITS-compressed GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "PACKBITS",
    }


class RAWProfile(Profile):
    """Tiled, pixel-interleaved, no-compressed GTiff."""

    defaults = {
        "driver": "GTiff",
        "interleave": "pixel",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
    }


class COGProfiles(dict):
    """CloudOptimized GeoTIFF profiles."""

    def __init__(self):
        """Initialize COGProfiles dict."""
        self.update({"ycbcr": YCbCrProfile()})
        self.update({"lzw": LZWProfile()})
        self.update({"deflate": DEFLATEProfile()})
        self.update({"packbits": PACKBITSProfile()})
        self.update({"raw": RAWProfile()})

    def get(self, key):
        """Like normal item access but error."""
        if key not in (self.keys()):
            raise KeyError("{} is not a valid COG profile name".format(key))

        return self[key].copy()


cog_profiles = COGProfiles()
