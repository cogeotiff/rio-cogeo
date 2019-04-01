"""tests rio_cogeo.profiles."""

import pytest
from rio_cogeo.profiles import cog_profiles


def test_profiles_jpeg():
    """Should work as expected (return jpeg profile)."""
    profile = cog_profiles.get("jpeg")
    assert profile["tiled"]
    assert profile["compress"] == "JPEG"
    assert profile["blockxsize"] == 512
    assert profile["blockysize"] == 512
    assert profile["photometric"] == "YCbCr"
    assert profile["interleave"] == "pixel"


def test_profiles_webp():
    """Should work as expected (return webp profile)."""
    profile = cog_profiles.get("webp")
    assert profile["tiled"]
    assert profile["compress"] == "WEBP"
    assert profile["blockxsize"] == 512
    assert profile["blockysize"] == 512
    assert profile["interleave"] == "pixel"


def test_profiles_lzw():
    """Should work as expected (return lzw profile)."""
    profile = cog_profiles.get("lzw")
    assert profile["tiled"]
    assert profile["compress"] == "LZW"
    assert profile["blockxsize"] == 512
    assert profile["blockysize"] == 512
    assert profile["interleave"] == "pixel"


def test_profiles_deflate():
    """Should work as expected (return deflate profile)."""
    profile = cog_profiles.get("deflate")
    assert profile["tiled"]
    assert profile["compress"] == "DEFLATE"
    assert profile["blockxsize"] == 512
    assert profile["blockysize"] == 512
    assert profile["interleave"] == "pixel"


def test_profiles_packbits():
    """Should work as expected (return packbits profile)."""
    profile = cog_profiles.get("packbits")
    assert profile["tiled"]
    assert profile["compress"] == "PACKBITS"
    assert profile["blockxsize"] == 512
    assert profile["blockysize"] == 512
    assert profile["interleave"] == "pixel"


def test_profiles_raw():
    """Should work as expected (return packbits profile)."""
    profile = cog_profiles.get("raw")
    assert profile["tiled"]
    assert not profile.get("compress")
    assert profile["blockxsize"] == 512
    assert profile["blockysize"] == 512
    assert profile["interleave"] == "pixel"


def test_profiles_copy():
    """'get' should perform a dict copy."""
    profile = cog_profiles.get("raw")
    profile.update({"interleave": "bands"})
    profile2 = cog_profiles.get("raw")
    assert not profile == profile2


def test_profiles_error():
    """Should raise an error on key not found."""
    with pytest.raises(KeyError):
        cog_profiles.get("something")
