import geopandas as gpd
import numpy as np
from rasterio.transform import xy
from shapely.geometry import LineString
import xarray as xr

from streamkit.streamroute import route_stream


def vectorize_streams(
    stream_raster: xr.DataArray,
    flow_directions: xr.DataArray,
    flow_accumulation: xr.DataArray,
) -> gpd.GeoDataFrame:
    """
    Vectorize streams from a raster to a GeoDataFrame of LineStrings.
    Args:
        stream_raster: A raster of stream segments with unique IDs.
        flow_directions: A raster of flow directions (ESRI D8 encoding).
        flow_accumulation: A raster of flow accumulation values.
    Returns:
        A GeoDataFrame with LineString geometries representing the streams with
        stream_id column (from the raster values).
    """
    flowlines = []
    for stream_id in np.unique(stream_raster.values):
        if stream_id == 0 or np.isnan(stream_id):
            continue

        stream = stream_raster.where(stream_raster == stream_id, other=0)
        flow_acc = flow_accumulation.where(stream_raster == stream_id, other=0)

        # skip any empty streams or those with one cell
        if np.sum(stream.data > 0) < 2:
            continue

        line = _vectorize_single_stream(stream > 0, flow_directions, flow_acc)
        flowlines.append({"geometry": line, "stream_id": int(stream_id)})

    gdf = gpd.GeoDataFrame(flowlines, crs=stream_raster.rio.crs)
    return gdf


def _vectorize_single_stream(stream_mask, flow_dir, flow_acc):
    path = route_stream(stream_mask, flow_dir, flow_acc)
    rows, cols = zip(*path)
    xs, ys = xy(stream_mask.rio.transform(), rows, cols, offset="center")
    line = LineString(zip(xs, ys))
    return line
