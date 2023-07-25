"""rio-cogeo models."""

from typing import Any, Dict, Optional, Sequence, Tuple

from pydantic import BaseModel, Field

BBox = Tuple[float, float, float, float]


class DictLike:
    """Provides dictionary access for pydantic models, for backwards compatability with rio-cogeo<2.2.0."""

    def __getitem__(self, item):
        """Access item like in Dict."""
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

    CRS: Optional[str] = None
    BoundingBox: BBox
    Origin: Tuple[float, float]
    Resolution: Tuple[float, float]
    MinZoom: Optional[int] = None
    MaxZoom: Optional[int] = None


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
    Nodata: Any = None
    ColorInterp: Sequence[str]
    ColorMap: bool
    Scales: Sequence[float]
    Offsets: Sequence[float]

    model_config = {"extra": "ignore"}


class BandMetadata(DictLike, BaseModel):
    """Band metadata."""

    Description: Optional[str] = None
    ColorInterp: str
    Offset: float
    Scale: float
    Metadata: Optional[Dict[str, Any]] = None


class Info(DictLike, BaseModel):
    """rio-cogeo Info."""

    Path: str
    Driver: str
    COG: bool
    Compression: Optional[str] = None
    ColorSpace: Optional[str] = None
    COG_errors: Optional[Sequence[str]] = None
    COG_warnings: Optional[Sequence[str]] = None
    Profile: Profile
    GEO: Geo
    Tags: Dict[str, Dict]
    Band_Metadata: Dict[str, BandMetadata] = Field(None, alias="Band Metadata")
    IFD: Sequence[IFD]

    model_config = {"populate_by_name": True}
