"""Rio-Cogeo Errors and Warnings."""


class LossyCompression(UserWarning):
    """Rio-cogeo module Lossy compression warning."""


class IncompatibleBlockRasterSize(UserWarning):
    """Rio-cogeo module incompatible raster block/size warning."""


class NodataAlphaMaskWarning(UserWarning):
    """Dataset with nodata and alpha/mask warning."""


class RioCogeoError(Exception):
    """Base exception class."""


class IncompatibleOptions(RioCogeoError):
    """Rio-cogeo module incompatible options."""
