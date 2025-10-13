import numpy as np
from scipy.ndimage import gaussian_filter


def gaussian_smooth_raster(raster, spatial_radius, sigma):
    resolution = raster.rio.resolution()[0]
    radius_pixels = int(round(spatial_radius / resolution))

    raster_copy = raster.copy(deep=True)
    raster_copy.data = filter_nan_gaussian_conserving(
        raster_copy.data, radius_pixels, sigma
    )
    return raster_copy


def filter_nan_gaussian_conserving(arr, radius_pixels, sigma):
    """Apply a gaussian filter to an array with nans.
    modified from:
    https://stackoverflow.com/a/61481246

    Intensity is only shifted between not-nan pixels and is hence conserved.
    The intensity redistribution with respect to each single point
    is done by the weights of available pixels according
    to a gaussian distribution.
    All nans in arr, stay nans in gauss.
    """
    nan_msk = np.isnan(arr)

    loss = np.zeros(arr.shape)
    loss[nan_msk] = 1
    loss = gaussian_filter(
        loss, sigma=sigma, mode="constant", cval=1, radius=radius_pixels
    )

    gauss = arr.copy()
    gauss[nan_msk] = 0
    gauss = gaussian_filter(
        gauss, sigma=sigma, mode="constant", cval=0, radius=radius_pixels
    )
    gauss[nan_msk] = np.nan

    gauss += loss * arr

    return gauss
