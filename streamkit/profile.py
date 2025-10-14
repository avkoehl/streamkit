"""
profilesProcess Cross Section Linestrings into profiles.

The linestrings are converted into a profile by sampling points along the linestring at user specified intervals.
"""

import numpy as np
import geopandas as gpd
import pandas as pd


def make_profiles(xs_linestrings, point_interval):
    """
    Generates points along cross section linestrings at specified intervals.
    Returns a GeoDataFrame with points and their corresponding sides (center, positive, negative).

    xs_id (int id), side (negative, positive, center), geometry (Point), distance (from center) + any other columns in xs_linestrings.
    """
    if "xs_id" not in xs_linestrings.columns:
        xs_linestrings["xs_id"] = np.arange(1, len(xs_linestrings) + 1)

    xs_points = []
    for xs_id, xs_linestring in xs_linestrings.groupby("xs_id"):
        for _, linestring in xs_linestring.iterrows():
            points = points_along_linestring(
                linestring.geometry, point_interval, crs=xs_linestrings.crs
            )
            points["xs_id"] = xs_id
            # add other columns from xs_linestrings
            for col in xs_linestring.columns:
                if col != "geometry":
                    points[col] = linestring[col]
            xs_points.append(points)

    return gpd.GeoDataFrame(
        pd.concat(xs_points), crs=xs_linestrings.crs, geometry="geometry"
    ).reset_index(drop=True)


def points_along_linestring(linestring, interval, crs=None):
    center = linestring.length / 2

    # Generate distances for all three directions
    pos_dists = np.arange(center + interval, linestring.length + interval, interval)
    neg_dists = np.arange(center - interval, -interval, -interval)

    distances = np.concatenate([[center], pos_dists, neg_dists])
    sides = ["center"] + ["positive"] * len(pos_dists) + ["negative"] * len(neg_dists)

    # Filter valid distances and create points
    valid_mask = (distances >= 0) & (distances <= linestring.length)
    points = [linestring.interpolate(d) for d in distances[valid_mask]]

    # relabel distances to be relative to the center
    distances = distances[valid_mask] - center

    return gpd.GeoDataFrame(
        {
            "side": [s for s, v in zip(sides, valid_mask) if v],
            "geometry": points,
            "distance": distances,
        },
        crs=crs,
    )
