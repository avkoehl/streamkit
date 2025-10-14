from xrspatial import slope


# wrapper of xrspatial.slope
def compute_slope(dem):
    slope_raster = slope(dem)
    return slope_raster
