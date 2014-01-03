import utils
import config
import struct

@utils.profile
def parse_RLE(w, h, pallette_colors, rle):
    # Parse a little endian unsigned short
    result = bytearray(struct.pack('BBB', *config.colorKey) * (w * h))
    # Start run length decoding
    n = len(rle)
    p = 0
    for y in range(h):
        if p >= n:
            break
        p0 = p
        # Read how many RLE items in this row
        nRLEDataInRow = rle[p]
        p += 1
        x = 0
        while p - p0 < nRLEDataInRow:
            nEmptyPixels = rle[p]
            p += 1
            x += nEmptyPixels
            # x exceeded line width, break and read next row
            if x >= w: 
                break
            nSolidPixels = rle[p]
            p += 1
            for j in range(nSolidPixels):
                assert x < w
                # surface.set_at((x, y), pallette.get(rle[p]))
                color = pallette_colors[rle[p]]
                i = (y * w + x) * 3
                result[i:i + 3] = color
                p += 1
                x += 1
            # x exceeded line width, break and read next row
            if x >= w: 
                break
    return bytes(result)
