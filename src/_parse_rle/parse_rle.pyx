import utils
import config
from struct import pack
from cython.view cimport array as cvarray
import cython

#@utils.profile
def parse_RLE(int w, int h, pallette_colors, rle):
    result = cvarray(shape=(w * h * 3,), itemsize=1, format='B')
    cdef unsigned char [:] resultV = result
    cdef unsigned char [:] rleV = rle
    cdef int i, j

    for i in range(0, w * h * 3, 3):
        for j in range(3):
            resultV[i + j] = config.colorKey[j]

    # Start run length decoding
    cdef int n = len(rleV)
    cdef int p = 0
    cdef int x, y

    for y in range(h):
        if p >= n:
            break
        p0 = p
        # Read how many RLE items in this row
        nRLEDataInRow = rleV[p]
        p += 1
        x = 0
        while p - p0 < nRLEDataInRow:
            nEmptyPixels = rleV[p]
            p += 1
            x += nEmptyPixels
            # x exceeded line width, break and read next row
            if x >= w: 
                break
            nSolidPixels = rleV[p]
            p += 1
            for j in range(nSolidPixels):
                assert x < w
                i = (y * w + x) * 3
                resultV[i], resultV[i + 1], resultV[i + 2] = pallette_colors[rleV[p]]
                p += 1
                x += 1
            # x exceeded line width, break and read next row
            if x >= w: 
                break
    return bytes(resultV)
