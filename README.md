# streamkit

A python toolkit for terrain-based stream network processing.

## Overview

streamkit provides tools for analyzing and manipulating stream networks derived
from DEMs. It repackages and extends functionality from several great libraries
(pysheds, hyriver, whitebox, etc.) to be more convenient to use in my workflows
that use rioxarray to represent raster data.


- **Watershed delineation** - DEM conditioning, flow direction, flow accumulation, and basin delineation
- **Stream network extraction** - Create a stream raster from NHD flowlines
- **Network analysis** - Strahler ordering and mainstem identification
- **Terrain analysis** - Smoothing, slope, HAND, upstream distance to furthest channel head
- **Reach delineation** - Segmentation of streams by changepoints in stream gradient
- **Cross-section generation** - Create transects and elevation profiles along stream networks
- **Vectorization** - Convert raster stream networks to vector formats and NetworkX graphs
- **Data utilities** - Download HUC boundaries, NHD flowlines, and USGS DEMs

## Installation

### From github to use as a dependency in your project

e.g. for poetry:
```toml
[tool.poetry.dependencies]
streamkit = { git = "ssh://git@github.com/avkoehl/streamkit.git", branch = "main" }
```

### build and install locally

```bash
git clone git@github.com:avkoehl/streamkit.git
cd streamkit
poetry install
```
