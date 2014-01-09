import config
from collections import deque

def search_path(grid_table, int level, start, end, int max_search):
    if start == end:
        return []
    cdef:
        int x, y, xmax, ymax, dmin, d
        short[:, :, :] gt = grid_table
        dict prev
        bint found
        list path

    xmax, ymax = grid_table.shape[1:]
    que = deque([start])
    prev = {start: None}
    directions = config.Directions.all
    dmin = 100000000
    dminPos = None
    found = False
    while que and len(que) <= max_search and not found:
        head = que.popleft()
        for direction in directions:
            x, y = pos = add(head, direction)
            d = dist(pos, end)
            if d == 0:
                prev[pos] = head
                found = True
                break
            if not (0 <= x < xmax and 0 <= y < ymax)\
                    or gt[level, y, x] > 0 or pos in prev:
                continue
            if d < dmin:
                dmin = d
                dminPos = pos
            prev[pos] = head
            que.append(pos)
    if not found:
        pos = dminPos
    else:
        pos = end
    # Construct the path
    path = []
    while pos and pos != start:
        path.append(pos)
        pos = prev[pos]
    return path

def add(a, b):
    cdef int x1, y1, x2, y2
    x1, y1 = a
    x2, y2 = b
    return (x1 + x2, y1 + y2)

def minus(a, b):
    cdef int x1, y1, x2, y2
    x1, y1 = a
    x2, y2 = b
    return (x1 - x2, y1 - y2)

def dist(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

