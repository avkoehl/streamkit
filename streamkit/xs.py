import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import LineString
from shapelysmooth import chaikin_smooth
from shapelysmooth import taubin_smooth


def network_cross_sections(
    linestrings, interval_distance, width, linestring_ids=None, smoothed=False
):
    if linestring_ids is None:
        linestring_ids = linestrings.index
    else:
        if len(linestring_ids) != len(linestrings):
            raise ValueError("provided ids must match the length of linestrings")

    xsections = []
    for cid, linestring in zip(linestring_ids, linestrings):
        channel_xsections = create_cross_sections(
            linestring, interval_distance, width, crs=linestrings.crs, smoothed=smoothed
        )
        # convert to DataFrame and add segment_id
        channel_xsections = gpd.GeoDataFrame(
            geometry=channel_xsections, crs=linestrings.crs
        )
        channel_xsections["linestring_id"] = cid
        xsections.append(channel_xsections)
    xsections = pd.concat(xsections)
    xsections["xs_id"] = np.arange(1, len(xsections) + 1)
    return xsections


def create_cross_sections(
    linestring, interval_distance, width, crs=None, smoothed=False
):
    # returns gpd.GeoSeries[gpd.LineString] for cross sections
    if smoothed:
        angles, points = compute_perpendicular_angles_smoothed(
            linestring, interval_distance
        )
    else:
        angles, points = compute_perpendicular_angles(linestring, interval_distance)

    lines = [
        create_linestring(point, angle, width) for point, angle in zip(points, angles)
    ]
    series = gpd.GeoSeries(lines)
    if crs:
        series.crs = crs
    return series


def _points_on_either_side(linestring, distance, delta=1):
    left_delta = delta
    right_delta = delta

    if distance + delta > linestring.length:
        right_delta = linestring.length
    if distance - delta < 0:
        left_delta = 0

    left_point = linestring.interpolate(distance - left_delta)
    right_point = linestring.interpolate(distance + right_delta)
    return left_point, right_point


def compute_perpendicular_angles(linestring, interval_distance):
    distances = np.arange(0, linestring.length + interval_distance, interval_distance)
    distances = distances[distances <= linestring.length]

    angles = []
    points = []
    for dist in distances:
        point = linestring.interpolate(dist)
        left_point, right_point = _points_on_either_side(linestring, dist)
        angle = np.arctan2(right_point.y - left_point.y, right_point.x - left_point.x)
        angle = angle + np.pi / 2  # rotate 90 degrees
        angles.append(angle)
        points.append(point)

    return angles, points


def compute_perpendicular_angles_smoothed(linestring, interval_distance):
    """
    The smoothed approach calculates perpendicular angles from a smoothed
    version of the linestring (for more consistent, less jagged directions) but
    positions the actual cross-section lines on the original linestring (to
    maintain accurate spatial relationships).
    """
    smoothed_linestring = chaikin_smooth(taubin_smooth(linestring))
    angles, points = compute_perpendicular_angles(
        smoothed_linestring, interval_distance
    )

    # pick a width that is sure to intersect with the original unsmoothed line
    new_points = []
    new_angles = []
    for point, angle in zip(points, angles):
        line = create_linestring(point, angle, width=200)
        # get the closest intersection point on linestring to point
        intersection = linestring.intersection(line)

        # if intersection is a point, use it
        if intersection.geom_type == "Point":
            new_points.append(intersection)
            new_angles.append(angle)
        elif intersection.geom_type == "MultiPoint":
            points = list(intersection.geoms)
            distances = [point.distance(p) for p in points]
            closest_idx = np.argmin(distances)
            new_points.append(points[closest_idx])
            new_angles.append(angle)
        else:
            distance = linestring.project(point)
            new_point = linestring.interpolate(distance)
            new_points.append(new_point)
            new_angles.append(angle)

    return new_angles, new_points


def create_linestring(point, angle, width):
    start_x = point.x - width / 2 * np.cos(angle)
    start_y = point.y - width / 2 * np.sin(angle)
    end_x = point.x + width / 2 * np.cos(angle)
    end_y = point.y + width / 2 * np.sin(angle)

    return LineString([(start_x, start_y), (end_x, end_y)])
