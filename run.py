import matplotlib.pyplot as plt
import geopandas as gpd

from streamkit.data import get_huc_data
from streamkit.watershed import (
    condition_dem,
    compute_flow_directions,
    compute_flow_accumulation,
)

flowlines, dem = get_huc_data("1805000205")

# watershed stuff
conditioned = condition_dem(dem)
flow_directions = compute_flow_directions(conditioned)
flow_accumulation = compute_flow_accumulation(flow_directions)
