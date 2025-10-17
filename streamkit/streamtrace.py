import numba
import numpy as np
import xarray as xr

from streamkit._internal.dirmap import _make_numba_esri_dirmap


def trace_streams(
    points: list[tuple[int, int]], flow_directions: xr.DataArray
) -> xr.DataArray:
    """
    Trace streams from a list of starting points based on flow directions.
    Args:
        points: List of (row, col) tuples representing starting points (i.e. channel head locations).
        flow_directions: xarray DataArray of flow directions (ESRI style).
    Returns:
        Binary stream raster where 1 indicates stream cells and 0 indicates non-stream cells. Can be used as input to `streamroute.streamlink` to label individual stream segments.
    """
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
