import numpy as np
from scipy.ndimage import gaussian_filter
import xarray as xr


def gaussian_smooth_raster(
    raster: xr.DataArray, spatial_radius: float, sigma: float
) -> xr.DataArray:
    """Apply Gaussian smoothing to a raster while preserving NaN values.

    Performs NaN-aware Gaussian filtering that conserves intensity by only
    redistributing values between non-NaN pixels. NaN pixels remain NaN in
    the output.

    Args:
        raster: Input raster to smooth.
        spatial_radius: Radius of the Gaussian kernel in map units (e.g., meters).
            Converted internally to pixels based on raster resolution.
        sigma: Standard deviation of the Gaussian kernel in pixels. Controls
            the strength of smoothing.

    Returns:
        Smoothed raster with the same dimensions, coordinates, and NaN pattern as the input.
    """
    resolution = raster.rio.resolution()[0]
    radius_pixels = int(round(spatial_radius / resolution))

    raster_copy = raster.copy(deep=True)
    raster_copy.data = _filter_nan_gaussian_conserving(
        raster_copy.data, radius_pixels, sigma
    )
    return raster_copy


def _filter_nan_gaussian_conserving(arr, radius_pixels, sigma):
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
