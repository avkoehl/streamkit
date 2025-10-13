import numba
import numpy as np

from streamkit._internal.dirmap import _make_numba_esri_dirmap


def trace_streams(points, flow_directions):
    dirmap = _make_numba_esri_dirmap()
    stream_arr = _trace_streams_numba(points, flow_directions.data, dirmap)
    stream_raster = flow_directions.copy(data=stream_arr)
    return stream_raster


@numba.njit
def _trace_streams_numba(points, flow_directions_arr, dirmap):
    """Mark all stream cells (binary stream network)"""
    nrows, ncols = flow_directions_arr.shape
    stream_arr = np.zeros((nrows, ncols), dtype=np.uint8)

    for point in points:
        row, col = point
        if stream_arr[row, col] != 0:
            continue

        while True:
            stream_arr[row, col] = 1

            current_direction = flow_directions_arr[row, col]
            if current_direction in (-1, -2, 0):
                break

            drow, dcol = dirmap[current_direction]
            next_row = row + drow
            next_col = col + dcol

            if not (0 <= next_row < nrows and 0 <= next_col < ncols):
                break

            if stream_arr[next_row, next_col] != 0:
                break

            row, col = next_row, next_col

    return stream_arr


@numba.njit
def _trace_flowpath_numba(start_row, start_col, flow_directions_arr, dirmap):
    nrows, ncols = flow_directions_arr.shape
    path = [(start_row, start_col)]

    current_row, current_col = start_row, start_col

    while True:  # loop until we hit a boundary condition (no flow, edge of raster, etc)
        current_direction = flow_directions_arr[current_row, current_col]
        if current_direction in (-1, -2, 0):
            break

        drow, dcol = dirmap[current_direction]
        next_row = current_row + drow
        next_col = current_col + dcol

        if not (0 <= next_row < nrows and 0 <= next_col < ncols):
            break

        path.append((next_row, next_col))
        current_row, current_col = next_row, next_col

    return path
