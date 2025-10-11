"""
Code for downloading wbd boundaries, flowlines, and dems, for a given HUC ID from usgs using pygeohydro methods.
"""

import rasterio
import py3dep
from pygeohydro import WBD
from pynhd import NHD
import pandas as pd
from rioxarray.merge import merge_arrays


def get_huc_data(
    hucid,
    nhd_layer="flowline_mr",
    crs="EPSG:4326",
    dem_resolution=10,
    wbd=None,
    nhd=None,
):
    """
    Download topography data for a given HUC ID.

    Parameters
    ----------
    hucid : str
        The HUC ID for which to download topography.
    nhd_layer : str, optional
        The NHD layer to use for downloading flowlines. Default is "flowline_mr".
    crs : str, optional
        The coordinate reference system to use for the output data. Default is "EPSG:4326".
    dem_resolution : int, optional
        The resolution of the DEM to download. Default is 10 meters.
    wbd : WBD, optional
        A WBD object to use for downloading HUC boundaries. If None, a new WBD object is created.
    nhd : NHD, optional
        A NHD object to use for downloading flowlines. If None, a new NHD object is created.

    Returns
    -------
    tuple
        A tuple containing the flowlines, and DEM data.
    """
    huc_bounds = download_huc_bounds(hucid, wbd)
    flowlines = download_flowlines(huc_bounds, nhd, nhd_layer, True, crs)
    dem = download_dem(huc_bounds, dem_resolution, crs)

    return flowlines, dem


def download_huc_bounds(huc, wbd=None):
    huc = str(huc)
    level = f"huc{str(len(huc))}"

    if wbd is None:
        wbd = WBD(level)

    huc_wbd = wbd.byids(level, huc)
    return huc_wbd


def download_flowlines(
    gdf, nhd=None, layer="flowline_mr", linestring_only=True, crs="EPSG:4326"
):
    if nhd is None:
        nhd = NHD(layer)

    boundary = gdf.union_all()
    flowlines = nhd.bygeom(boundary)
    flowlines = flowlines.clip(boundary)
    flowlines = flowlines.explode()

    if linestring_only:
        flowlines = flowlines[flowlines.geometry.type == "LineString"]

    flowlines = flowlines.to_crs(crs)
    return flowlines


def download_dem(gdf, resolution, crs="EPSG:4326"):
    boundary = gdf.union_all()
    try:
        dem = py3dep.static_3dep_dem(boundary, resolution=resolution, crs=gdf.crs)
    except:
        dem = retry_on_smaller(boundary)

    if dem.rio.crs != crs:
        dem = dem.rio.reproject(crs, resampling=rasterio.enums.Resampling.bilinear)
    return dem


def retry_on_smaller(boundary):
    bbox = pd.DataFrame(
        {
            "minx": [boundary.bounds[0]],
            "miny": [boundary.bounds[1]],
            "maxx": [boundary.bounds[2]],
            "maxy": [boundary.bounds[3]],
        }
    )
    bbox["mid_x"] = (bbox["minx"] + bbox["maxx"]) / 2
    bbox["mid_y"] = (bbox["miny"] + bbox["maxy"]) / 2

    # Create four smaller bounding boxes
    split_bboxes = pd.DataFrame(
        [
            {
                "minx": bbox.iloc[0]["minx"],
                "miny": bbox.iloc[0]["miny"],
                "maxx": bbox.iloc[0]["mid_x"],
                "maxy": bbox.iloc[0]["mid_y"],
            },  # Bottom-left
            {
                "minx": bbox.iloc[0]["mid_x"],
                "miny": bbox.iloc[0]["miny"],
                "maxx": bbox.iloc[0]["maxx"],
                "maxy": bbox.iloc[0]["mid_y"],
            },  # Bottom-right
            {
                "minx": bbox.iloc[0]["minx"],
                "miny": bbox.iloc[0]["mid_y"],
                "maxx": bbox.iloc[0]["mid_x"],
                "maxy": bbox.iloc[0]["maxy"],
            },  # Top-left
            {
                "minx": bbox.iloc[0]["mid_x"],
                "miny": bbox.iloc[0]["mid_y"],
                "maxx": bbox.iloc[0]["maxx"],
                "maxy": bbox.iloc[0]["maxy"],
            },  # Top-right
        ]
    )

    dems = []
    for _, box in split_bboxes.iterrows():
        dems.append(py3dep.get_dem(tuple(box), crs="EPSG:4326", resolution=10))

    mosaic = merge_arrays(dems)
    clipped = mosaic.rio.clip(boundary)
    return clipped
