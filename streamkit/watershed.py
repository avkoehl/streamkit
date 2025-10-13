# condition dem, flow directions, and flow accumulation
# trace flow path
# delineat watershed from pour points
from streamkit._internal.adapters import to_pysheds, from_pysheds


def condition_dem(dem):
    pysheds_dem, grid = to_pysheds(dem)
    pit_filled_dem = grid.fill_pits(pysheds_dem)
    flooded_dem = grid.fill_depressions(pit_filled_dem)
    inflated_dem = grid.resolve_flats(flooded_dem)
    conditioned = from_pysheds(inflated_dem)
    return conditioned


def compute_flow_directions(dem):
    pysheds_dem, grid = to_pysheds(dem)
    flow_directions = grid.flowdir(pysheds_dem)
    flow_directions_xr = from_pysheds(flow_directions)
    return flow_directions_xr


def compute_flow_accumulation(flow_directions):
    pysheds_flow_direction, grid = to_pysheds(flow_directions)
    flow_accumulation = grid.accumulation(pysheds_flow_direction)
    flow_accumulation_xr = from_pysheds(flow_accumulation)
    return flow_accumulation_xr


def delineate_subbasins(channel_network_raster, flow_directions):
    # get pour points from channel network raster
    # these are sorted so that nested basins are handled correctly
    pass
