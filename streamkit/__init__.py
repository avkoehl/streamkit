"""
streamkit
"""

__version__ = "0.1.0"

# Core watershed functions
from streamkit.watershed import (
    compute_hand,
    flow_accumulation_workflow,
    delineate_subbasins,
)

# Stream vectorization and network conversion
from streamkit.vectorize_streams import vectorize_streams, vectorize_single_stream
from streamkit.nx_convert import vector_streams_to_networkx, networkx_to_gdf

# Network analysis
from streamkit.strahler import strahler_order
from streamkit.upstream_length import upstream_length
from streamkit.mainstem import label_mainstem
from streamkit.xs import network_cross_sections
from streamkit.profile import make_profiles

# Terrain analysis
from streamkit.slope import compute_slope
from streamkit.smooth import gaussian_smooth_raster
from streamkit.upstream_length import upstream_length_raster

# Reach delineation
from streamkit.reach import delineate_reaches

# Data download utilities
from streamkit.data import (
    get_huc_data,
    download_huc_bounds,
    download_flowlines,
    download_dem,
)

# NHD-specific utilities
from streamkit.nhd import rasterize_nhd

__all__ = [
    # Watershed
    "compute_hand",
    "flow_accumulation_workflow",
    "delineate_subbasins",
    # Conversion Utilities
    "vectorize_streams",
    "vectorize_single_stream",
    "vector_streams_to_networkx",
    "networkx_to_gdf",
    # Network analysis
    "strahler_order",
    "upstream_length",
    "label_mainstem",
    "network_cross_sections",
    "make_profiles",
    # Terrain
    "upstream_length_raster",
    "compute_slope",
    "gaussian_smooth_raster",
    # Reaches
    "delineate_reaches",
    # Data
    "get_huc_data",
    "download_huc_bounds",
    "download_flowlines",
    "download_dem",
    # NHD
    "rasterize_nhd",
]
