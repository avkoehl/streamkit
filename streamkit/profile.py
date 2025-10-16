import numpy as np
import geopandas as gpd
import pandas as pd


def sample_cross_sections(
    xs_linestrings: gpd.GeoDataFrame, point_interval: float
) -> gpd.GeoDataFrame:
    """Generate profile points along cross-section linestrings at regular intervals.

    Creates evenly-spaced points along each cross-section line, measuring distances
    from the center point. Points are labeled as 'center', 'positive' (downstream
    of center), or 'negative' (upstream of center).

    Args:
        xs_linestrings: GeoDataFrame containing LineString geometries representing
            cross-sections. If 'xs_id' column is not present, sequential IDs will
            be automatically assigned.
        point_interval: Spacing between points along each cross-section, in the
            units of the GeoDataFrame's CRS.

    Returns:
        A GeoDataFrame with Point geometries containing columns:
            - xs_id: Cross-section identifier
            - side: Position relative to center ('center', 'positive', 'negative')
            - distance: Distance from center point (negative for upstream, positive
              for downstream)
            - geometry: Point geometry
            - Additional columns from input xs_linestrings are preserved
    """

    if "xs_id" not in xs_linestrings.columns:
        xs_linestrings["xs_id"] = np.arange(1, len(xs_linestrings) + 1)

    xs_points = []
    for xs_id, xs_linestring in xs_linestrings.groupby("xs_id"):
        for _, linestring in xs_linestring.iterrows():
            points = _points_along_linestring(
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


def _points_along_linestring(linestring, interval, crs=None):
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
