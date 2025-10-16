import numpy as np
import networkx as nx
import xarray as xr

from streamkit._internal.dirmap import _make_numba_esri_dirmap
from streamkit.streamnodes import find_stream_nodes


def upstream_length_raster(
    streams: xr.DataArray, flow_direction: xr.DataArray
) -> xr.DataArray:
    """
    For each cell in the stream raster, compute the maximum upstream length

    Args:
        streams: A binary raster where stream cells are 1 and non-stream cells are 0.
        flow_direction: A raster representing flow direction using ESRI convention.
    Returns:
        A raster where each stream cell contains the maximum upstream length in map units.
    """
    dirmap = _make_numba_esri_dirmap()
    sources, _, _ = find_stream_nodes(streams, flow_direction)
    distance_arr = _distance_from_head(
        streams.data, sources, flow_direction.data, dirmap
    )
    distance_raster = flow_direction.copy(data=distance_arr)
    distance_raster *= np.abs(flow_direction.rio.resolution()[0])
    return distance_raster


def _distance_from_head(stream_arr, headwater_points, flow_dir_arr, dirmap):
    nrows, ncols = flow_dir_arr.shape
    distance_arr = np.zeros((nrows, ncols), dtype=np.float32)

    for point in headwater_points:
        row, col = point
        distance = 0.0

        while True:
            if distance >= distance_arr[row, col]:
                distance_arr[row, col] = distance
            else:
                break

            current_direction = flow_dir_arr[row, col]
            if current_direction in (-1, -2, 0):
                break

            drow, dcol = dirmap[current_direction]
            next_row = row + drow
            next_col = col + dcol

            if not (0 <= next_row < nrows and 0 <= next_col < ncols):
                break

            if stream_arr[next_row, next_col] == 0:
                break

            # Assuming each cell is 1 unit length; modify if cell size is different
            dist_increment = np.sqrt(drow**2 + dcol**2)
            distance += dist_increment
            row, col = next_row, next_col
    return distance_arr


def upstream_length(G: nx.DiGraph) -> nx.DiGraph:
    """
    Compute the maximum upstream length for each edge in a directed graph G. Uses the length attribute of the edge geometry.

    Args:
        G: A directed graph where edges have a 'geometry' attribute (shapely LineString).
    Returns:
        A copy of the graph with an additional attribute 'max_upstream_length' for each edge.
    """
    # Compute the maximum upstream length for each edge in a directed graph G.
    # confirm that all edges have a 'geometry' attribute
    G = G.copy()
    if not all("geometry" in G.edges[e] for e in G.edges):
        raise ValueError(
            "All edges must have a 'geometry' attribute. Cannot compute upstream length."
        )

    for u, v, d in G.edges(data=True):
        d["max_upstream_length"] = 0.0

    for node in nx.topological_sort(G):
        upstream = list(G.in_edges(node, data=True))

        if len(upstream) == 0:
            # this is headwater, set length to the length of the edge.geometry
            out_edges = list(G.out_edges(node, data=True))
            if len(out_edges) == 1:
                _, _, out_data = out_edges[0]
                length = out_data.get("geometry").length
        elif len(upstream) == 1:
            u, v, data = upstream[0]
            length = data.get("max_upstream_length") + data.get("geometry").length
        else:
            max_upstream_length = 0.0
            for u, v, data in upstream:
                upstream_length = (
                    data.get("max_upstream_length") + data.get("geometry").length
                )
                if upstream_length > max_upstream_length:
                    max_upstream_length = upstream_length
            length = max_upstream_length

        for _, v, out_data in G.out_edges(node, data=True):
            out_data["max_upstream_length"] = length
    return G
