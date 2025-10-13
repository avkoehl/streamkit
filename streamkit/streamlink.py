import numba
import numpy as np

from streamkit._internal.dirmap import _make_numba_esri_dirmap


def link_streams(stream_raster, flow_directions):
    """Create stream links (unique IDs for segments between junctions)

    Automatically finds source points and confluence points from the stream network.
    """
    dirmap = _make_numba_esri_dirmap()
    link_arr = _link_streams_numba(stream_raster.data, flow_directions.data, dirmap)
    link_raster = flow_directions.copy(data=link_arr)
    return link_raster


@numba.njit
def _link_streams_numba(stream_arr, flow_directions_arr, dirmap):
    """Assign unique IDs to stream links (segments between junctions)"""
    nrows, ncols = flow_directions_arr.shape

    # Find junctions
    sources, confluences = _find_stream_junctions_numba(
        stream_arr, flow_directions_arr, dirmap
    )

    # Create confluence lookup for faster checking
    confluence_arr = np.zeros((nrows, ncols), dtype=np.uint8)
    for row, col in confluences:
        confluence_arr[row, col] = 1

    # Assign link IDs starting from each source
    link_id = 1
    link_arr = np.zeros((nrows, ncols), dtype=np.uint16)

    for source_row, source_col in sources:
        row, col = source_row, source_col

        while True:
            if link_arr[row, col] != 0 or stream_arr[row, col] == 0:
                break

            link_arr[row, col] = link_id

            current_direction = flow_directions_arr[row, col]
            if current_direction in (-1, -2, 0):
                link_id += 1
                break

            drow, dcol = dirmap[current_direction]
            next_row = row + drow
            next_col = col + dcol

            if not (0 <= next_row < nrows and 0 <= next_col < ncols):
                link_id += 1
                break

            # If next cell is a confluence, end current link
            if confluence_arr[next_row, next_col] == 1:
                link_id += 1
                row, col = next_row, next_col
                continue

            # If next cell already has an ID, we've merged
            if link_arr[next_row, next_col] != 0:
                link_id += 1
                break

            row, col = next_row, next_col

    return link_arr


@numba.njit
def _find_stream_junctions_numba(stream_arr, flow_directions_arr, dirmap):
    """Find source points (headwaters) and confluence points in stream network"""
    nrows, ncols = flow_directions_arr.shape
    inflow_count = np.zeros((nrows, ncols), dtype=np.uint8)

    # Count how many stream cells flow into each cell
    for row in range(nrows):
        for col in range(ncols):
            if stream_arr[row, col] == 0:
                continue

            current_direction = flow_directions_arr[row, col]
            if current_direction in (-1, -2, 0):
                continue

            drow, dcol = dirmap[current_direction]
            next_row = row + drow
            next_col = col + dcol

            if 0 <= next_row < nrows and 0 <= next_col < ncols:
                if stream_arr[next_row, next_col] != 0:
                    inflow_count[next_row, next_col] += 1

    # Find source points (no inflow) and confluence points (multiple inflows)
    sources = []
    confluences = []

    for row in range(nrows):
        for col in range(ncols):
            if stream_arr[row, col] == 0:
                continue

            if inflow_count[row, col] == 0:
                sources.append((row, col))
            elif inflow_count[row, col] > 1:
                confluences.append((row, col))

    return sources, confluences
