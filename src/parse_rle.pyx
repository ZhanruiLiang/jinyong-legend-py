import utils
import config
from struct import pack
from cython.view cimport array as cvarray
import cython

MAX_W, MAX_H = 256, 256
result = cvarray(shape=(MAX_W * MAX_H * 3,), itemsize=1, format='B')
cdef unsigned char pallette[256][3]

def load_pallette(colors):
    for i, color in enumerate(colors):
        for j in range(3):
            pallette[i][j] = color[j]

#@utils.profile
def parse_RLE(int w, int h, rle):
    cdef unsigned char [:] resultV = result
    cdef unsigned char [:] rleV = rle
    cdef int i, j

    cdef unsigned char ck0, ck1, ck2
    ck0, ck1, ck2 = config.colorKey
    for i in range(0, w * h * 3, 3):
        resultV[i], resultV[i + 1], resultV[i + 2] = ck0, ck1, ck2

    # Start run length decoding
    cdef int n = len(rleV)
    cdef int p = 0
    cdef int x, y, p0
    cdef int nRLEDataInRow, nEmptyPixels, nSolidPixels

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
                # assert x < w
                i = (y * w + x) * 3
                for j in range(3):
                    resultV[i + j] = pallette[rleV[p]][j]
                p += 1
                x += 1
            # x exceeded line width, break and read next row
            if x >= w: 
                break
    return bytes(resultV[:w * h * 3])
