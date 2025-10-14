import matplotlib.pyplot as plt
import geopandas as gpd

from streamkit.data import get_huc_data
from streamkit.watershed import flow_accumulation_workflow, delineate_subbasins
from streamkit.nhd import rasterize_nhd
from streamkit.vectorize_streams import vectorize_streams
from streamkit.nx_convert import vector_streams_to_networkx
from streamkit.nx_convert import networkx_to_gdf
from streamkit.strahler import strahler_order
from streamkit.upstream_length import upstream_length
from streamkit.mainstem import label_mainstem
from streamkit.upstream_length import upstream_length_raster

flowlines, dem = get_huc_data("1805000205", crs="EPSG:3310")

conditioned, flow_directions, flow_accumulation = flow_accumulation_workflow(dem)

stream_raster = rasterize_nhd(flowlines, dem)
stream_vec = vectorize_streams(stream_raster, flow_directions, flow_accumulation)

basins = delineate_subbasins(stream_raster, flow_directions, flow_accumulation)

graph = vector_streams_to_networkx(stream_vec)

graph = strahler_order(graph)
graph = upstream_length(graph)
graph = label_mainstem(graph)
gdf = networkx_to_gdf(graph)


ul = upstream_length_raster(stream_raster, flow_directions)
