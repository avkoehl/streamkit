"""Adapter functions to convert between rioxarray DataArray and pysheds Grid."""

from pysheds.grid import Grid


def to_pysheds(raster_xr, data_name="data"):
    """Convert rioxarray DataArray to pysheds Grid."""
    grid = Grid()
    grid.add_gridded_data(
        data=raster_xr.values,
        data_name=data_name,
        affine=raster_xr.rio.transform(),
        crs=raster_xr.rio.crs,
        nodata=raster_xr.rio.nodata,
    )
    return grid, data_name


def from_pysheds(grid, data_name, template):
    """Convert pysheds Grid result back to rioxarray DataArray."""
    data = grid.view(data_name)
    result = template.copy(data=data)
    result.rio.write_nodata(grid.nodata, inplace=True)
    return result
