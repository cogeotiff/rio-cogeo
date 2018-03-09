
from rasterio.profiles import Profile


class CogeoProfiles(object):
    """Rasterio profiles
    """

    def get(self, name):
        if name == 'ycbcr':
            return self.cog_ycbcr
        elif name == 'lzw':
            return self.cog_lzw
        elif name == 'deflate':
            return self.cog_deflate
        else:
            raise Exception('Invalid Profile name')

    class COG_YCbCr(Profile):
        """Tiled, pixel-interleaved, JPEG-compressed, 8-bit GTiff."""

        defaults = {
            'driver': 'GTiff',
            'interleave': 'pixel',
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'compress': 'JPEG',
            'photometric': 'YCbCr'}

    cog_ycbcr = COG_YCbCr()

    class COG_LZW(Profile):
        """Tiled, pixel-interleaved, LZW-compressed, 8-bit GTiff."""

        defaults = {
            'driver': 'GTiff',
            'interleave': 'pixel',
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'compress': 'LZW',
            'photometric': 'RGB'}

    cog_lzw = COG_LZW()

    class COG_DEFLATE(Profile):
        """Tiled, pixel-interleaved, DEFLATE-compressed, 8-bit GTiff."""

        defaults = {
            'driver': 'GTiff',
            'interleave': 'pixel',
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'compress': 'LZW',
            'photometric': 'DEFLATE'}

    cog_deflate = COG_DEFLATE()


CogeoProfiles = CogeoProfiles()
