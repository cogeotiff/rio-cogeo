"""rio_cogeo.profiles: CloudOptimized profiles."""


class COG(dict):
    """CloudOptimized GeoTIFF profiles."""

    def __init__(self):
        """Tiled, pixel-interleaved, JPEG-compressed GTiff."""
        self.update({'ycbcr': {
            'driver': 'GTiff',
            'interleave': 'pixel',
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'compress': 'JPEG',
            'photometric': 'YCbCr'}})

        """Tiled, pixel-interleaved, LZW-compressed GTiff."""
        self.update({'lzw': {
            'driver': 'GTiff',
            'interleave': 'pixel',
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'compress': 'LZW',
            'photometric': 'RGB'}})

        """Tiled, pixel-interleaved, DEFLATE-compressed GTiff."""
        self.update({'deflate': {
            'driver': 'GTiff',
            'interleave': 'pixel',
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'compress': 'DEFLATE',
            'photometric': 'RGB'}})

        """Tiled, pixel-interleaved, PACKBITS-compressed GTiff."""
        self.update({'packbits': {
            'driver': 'GTiff',
            'interleave': 'pixel',
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'compress': 'PACKBITS',
            'photometric': 'RGB'}})

        """Tiled, pixel-interleaved, no-compression GTiff."""
        self.update({'raw': {
            'driver': 'GTiff',
            'interleave': 'pixel',
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'photometric': 'RGB'}})

    def get(self, key):
        """Like normal item access but error."""
        if key not in (self.keys()):
            raise KeyError('{} is not a valid COG profile name'.format(key))
        return self[key].copy()


cog_profiles = COG()
