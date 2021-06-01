"""rio-cogeo models."""

from typing import Any, Dict, Optional, Sequence, Tuple

from pydantic import BaseModel

BBox = Tuple[float, float, float, float]


class DictLike:
    """Provides dictionary access for pydantic models, for backwards compatability with rio-cogeo<2.2.0."""

    def __getitem__(self, item):
        """Dictionary access."""
        return self.__dict__[item]


class IFD(DictLike, BaseModel):
    """ImageFileDirectory info."""

    Level: int
    Width: int
    Height: int
    Blocksize: Tuple[int, int]
    Decimation: int


class Geo(DictLike, BaseModel):
    """rio-cogeo validation GEO information."""

    CRS: Optional[str]
    BoundingBox: BBox
    Origin: Tuple[float, float]
    Resolution: Tuple[float, float]
    MinZoom: Optional[int]
    MaxZoom: Optional[int]


class Profile(DictLike, BaseModel):
    """rio-cogeo validation Profile information."""

    Bands: int
    Width: int
    Height: int
    Tiled: bool
    Dtype: str
    Interleave: str
    AlphaBand: bool
    InternalMask: bool
    Nodata: Any
    ColorInterp: Sequence[str]
    ColorMap: bool
    Scales: Sequence[float]
    Offsets: Sequence[float]

    class Config:
        """Config for model."""

        extra = "ignore"


class Info(DictLike, BaseModel):
    """rio-cogeo Info."""

    Path: str
    Driver: str
    COG: bool
    Compression: Optional[str]
    ColorSpace: Optional[str]
    COG_errors: Optional[Sequence[str]]
    COG_warnings: Optional[Sequence[str]]
    Profile: Profile
    GEO: Geo
    Tags: Dict[str, Dict]
    IFD: Sequence[IFD]
