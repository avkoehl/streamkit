import geopandas as gpd
import numpy as np
import numba
from rasterio.transform import xy
from shapely.geometry import LineString

from streamkit._internal.dirmap import _make_numba_esri_dirmap


def vectorize_streams(stream_raster, flow_directions, flow_accumulation):
    dirmap = _make_numba_esri_dirmap()

    flowlines = []
    for stream_id in np.unique(stream_raster.values):
        if stream_id == 0 or np.isnan(stream_id):
            continue

        stream = stream_raster.where(stream_raster == stream_id, other=0)
        flow_acc = flow_accumulation.where(stream_raster == stream_id, other=0)

        # skip any empty streams or those with one cell
        if np.sum(stream.data > 0) < 2:
            continue

        line = vectorize_single_stream(stream, flow_directions, flow_acc, dirmap)
        flowlines.append({"geometry": line, "stream_id": int(stream_id)})

    gdf = gpd.GeoDataFrame(flowlines, crs=stream_raster.rio.crs)
    return gdf


def vectorize_single_stream(stream, flow_dir, flow_acc, dirmap):
    start, end = _determine_start_and_end(stream, flow_acc)
    break_conditions_arr = stream <= 0
    path = _trace_path_numba(
        start[0], start[1], flow_dir.data, dirmap, break_conditions_arr.data
    )

    # confirm start and end
    if path[0] != start or path[-1] != end:
        raise ValueError("Traced path does not match start and end points")

    # confirm all cells in stream are in path (list of tuples)
    stream_cells = np.argwhere(stream.data > 0)
    stream_cells_set = set((row, col) for row, col in stream_cells)
    path_set = set(path)
    if stream_cells_set != path_set:
        raise ValueError("Traced path does not cover all stream cells")

    # if the final cell points somewhere else, add that cell to the path
    final_direction = flow_dir.data[path[-1][0], path[-1][1]]
    if final_direction not in (-1, -2, 0):
        drow, dcol = dirmap[final_direction]
        next_row = path[-1][0] + drow
        next_col = path[-1][1] + dcol
        if 0 <= next_row < flow_dir.shape[0] and 0 <= next_col < flow_dir.shape[1]:
            path.append((next_row, next_col))

    # convert path to LineString
    rows, cols = zip(*path)
    xs, ys = xy(stream.rio.transform(), rows, cols, offset="center")
    line = LineString(zip(xs, ys))
    return line


@numba.njit
def _trace_path_numba(row, col, flow_directions_arr, dirmap, break_conditions_arr):
    """Trace the path of a stream segment from start to end using flow directions"""
    nrows, ncols = flow_directions_arr.shape
    path = [(row, col)]

    while True:
        current_direction = flow_directions_arr[row, col]
        if current_direction in (-1, -2, 0):
            break

        drow, dcol = dirmap[current_direction]
        next_row = row + drow
        next_col = col + dcol

        if not (0 <= next_row < nrows and 0 <= next_col < ncols):
            break

        if break_conditions_arr[next_row, next_col] == 1:
            break

        path.append((next_row, next_col))
        row, col = next_row, next_col

    return path


def _determine_start_and_end(stream, flow_acc):
    """Given a mask of a single stream segment, determine the start and end points"""
    # find the stream cells with the lowest and highest flow accumulation
    stream_cells = np.argwhere(stream.data > 0)
    flow_acc_values = flow_acc.data[stream.data > 0]
    min_idx = np.argmin(flow_acc_values)
    max_idx = np.argmax(flow_acc_values)
    start = tuple(stream_cells[min_idx])
    end = tuple(stream_cells[max_idx])
    return start, end
