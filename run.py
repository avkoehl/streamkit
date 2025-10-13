import matplotlib.pyplot as plt
import geopandas as gpd

from streamkit.data import get_huc_data
from streamkit.watershed import flow_accumulation_workflow, delineate_subbasins
from streamkit.nhd import rasterize_nhd
from streamkit.vectorize_streams import vectorize_streams

flowlines, dem = get_huc_data("1805000205", crs="EPSG:3310")

# watershed stuff
conditioned, flow_directions, flow_accumulation = flow_accumulation_workflow(dem)

stream_raster = rasterize_nhd(flowlines, dem)
stream_vec = vectorize_streams(stream_raster, flow_directions, flow_accumulation)
