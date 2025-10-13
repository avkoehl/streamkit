# streamkit

A python toolkit for terrain-based stream network processing at the catchment scale.

### Watershed Analysis
- `flow_accumulation_workflow(dem)`: hydrologically condition, compute flow direction and accumulation from DEM.
- `trace_path(flow_direction, point(s))`: Trace flow path(s) from given point(s) to the outlet.
- `delineate_subbasins(flow_direction, pour_point(s))`: Delineate watershed(s) from given pour point(s).

### Stream Network Analysis
- `identify_source_points(streams)`: Identify source points in the stream network.
- `to_networkx(streams)`: Convert stream network to a NetworkX graph(s) for advanced analysis.
- `from_networkx(graph)`: Convert a NetworkX graph back to a GeoDataFrame.
- `compute_stream_order(graph)`: Compute stream order using Strahler method.
- `compute_mainstem(graph)`: Identify the mainstem of a stream network.
- `rasterize_streams(streams, dem)`: Rasterize stream network to match DEM resolution.
- `xsections_along_streams(streams, spacing, width)`: Generate cross-sections along streams at specified spacing and width.
- `profiles(xsections, dem)`: Extract elevation profiles along cross-sections from DEM.

### Reach Segmentation
- `segment_reaches(streams, elevation_raster, penalty, min_length, sample_distance)`: Segment streams into reaches based on change points detected in stream gradient.

### Terrain Methods
- `compute_slope(dem)`: Compute slope from DEM.
- `smooth_raster(raster, spatial_radius, sigma)`: Smooth a raster using Gaussian filter preserving NaN.

### NHD
- `get_huc_data(hucid, nhd_layer, dem_resolution)`: Download dem and nhd data for a huc watershed using HyRiver.
- `identify_inlets(nhd_flowlines)`: Identify inlet points in NHD flowlines.
