

class COG(dict):
    """CloudOptimized GeoTiff profiles
    """

    def __init__(self):
        """Tiled, pixel-interleaved, JPEG-compressed, 8-bit GTiff."""
        self.update({'ycbcr': {
            'driver': 'GTiff',
            'interleave': 'pixel',
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'compress': 'JPEG',
            'photometric': 'YCbCr'}})

        """Tiled, pixel-interleaved, LZW-compressed, 8-bit GTiff."""
        self.update({'lzw': {
            'driver': 'GTiff',
            'interleave': 'pixel',
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'compress': 'LZW',
            'photometric': 'RGB'}})

        """Tiled, pixel-interleaved, DEFLATE-compressed, 8-bit GTiff."""
        self.update({'deflate': {
            'driver': 'GTiff',
            'interleave': 'pixel',
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'compress': 'DEFLATE',
            'photometric': 'RGB'}})

    def get(self, key):
        """Like normal item access but error."""
        if key not in (self.keys()):
            raise KeyError('{} is not a valid COG profile name'.format(key))
        return self[key]


cog_profiles = COG()
