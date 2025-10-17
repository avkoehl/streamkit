import numpy as np
from shapely.geometry import Point
import geopandas as gpd
import networkx as nx
import xarray as xr

from streamkit.watershed import flow_accumulation_workflow
from streamkit.streamtrace import trace_streams
from streamkit.streamlink import link_streams


def rasterize_nhd(nhd_flowlines: gpd.GeoDataFrame, dem: xr.DataArray) -> xr.DataArray:
    """Create a raster representation of NHD flowlines traced on a DEM.

    Converts vector NHD flowlines to a raster stream network by identifying
    channel heads, tracing streams downslope along the DEM's flow directions,
    and linking stream segments. Small streams (< 2 pixels) are removed and
    the remaining streams are relabeled with consecutive integers.

    Args:
        nhd_flowlines: Vector flowline data from the National Hydrography Dataset
            containing stream geometries.
        dem: Digital elevation model raster with spatial reference information.
            Used to determine flow directions for stream tracing.

    Returns:
        A raster DataArray where each pixel value represents a unique stream ID (0 for non-stream pixels, consecutive positive integers for stream segments).
    """
    channel_heads = _nhd_channel_heads(nhd_flowlines)

    xs, ys = zip(*[(pt.x, pt.y) for pt in channel_heads])
    inverse = ~dem.rio.transform()
    indices = [inverse * (x, y) for x, y in zip(xs, ys)]
    points = [
        (int(row), int(col)) for col, row in indices
    ]  # note the order of col, row...

    _, flow_directions, _ = flow_accumulation_workflow(dem)

    stream_raster = trace_streams(points, flow_directions)
    stream_raster = link_streams(stream_raster, flow_directions)

    # drop any small streams (< 2 pixels)
    # find all unique stream IDs where the count is < 2
    unique, counts = np.unique(stream_raster.data, return_counts=True)
    small_streams = unique[counts < 2]
    for stream_id in small_streams:
        stream_raster.data[stream_raster.data == stream_id] = 0

    # re-label streams to be consecutive integers
    unique, counts = np.unique(stream_raster.data, return_counts=True)
    new_id = 1
    for stream_id in unique:
        if stream_id == 0:
            continue
        stream_raster.data[stream_raster.data == stream_id] = new_id
        new_id += 1
    return stream_raster


def _nhd_channel_heads(nhd_flowlines):
    G = nx.DiGraph()
    for flowline in nhd_flowlines.geometry:
        start = flowline.coords[0]
        end = flowline.coords[-1]
        G.add_edge(start, end)

    channel_heads = [Point(node) for node, deg in G.in_degree() if deg == 0]
    return gpd.GeoSeries(channel_heads, crs=nhd_flowlines.crs)
