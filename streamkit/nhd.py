# methods for handling NHD flowlines data
# rasterize_nhd
#
from shapely.geometry import Point
import geopandas as gpd
import networkx as nx

from streamkit.watershed import flow_accumulation_workflow
from streamkit.streamtrace import trace_streams
from streamkit.streamlink import link_streams


def rasterize_nhd(nhd_flowlines, dem):
    channel_heads = nhd_channel_heads(nhd_flowlines)

    xs, ys = zip(*[(pt.x, pt.y) for pt in channel_heads])
    inverse = ~dem.rio.transform()
    indices = [inverse * (x, y) for x, y in zip(xs, ys)]
    points = [
        (int(row), int(col)) for col, row in indices
    ]  # note the order of col, row...

    _, flow_directions, _ = flow_accumulation_workflow(dem)

    stream_raster = trace_streams(points, flow_directions)
    stream_raster = link_streams(stream_raster, flow_directions)
    return stream_raster


def nhd_channel_heads(nhd_flowlines):
    G = nx.DiGraph()
    for flowline in nhd_flowlines.geometry:
        start = flowline.coords[0]
        end = flowline.coords[-1]
        G.add_edge(start, end)

    channel_heads = [Point(node) for node, deg in G.in_degree() if deg == 0]
    return gpd.GeoSeries(channel_heads, crs=nhd_flowlines.crs)
