import tempfile

import numpy as np
import pandas as pd
import rioxarray as rxr
import whitebox

from streamkit._internal.adapters import to_pysheds, from_pysheds


def condition_dem(dem):
    wbt = whitebox.WhiteboxTools()
    working_dir = tempfile.mkdtemp()
    wbt.set_working_dir(working_dir)
    wbt.verbose = False

    dem.rio.to_raster(f"{working_dir}/dem.tif")

    wbt.fill_depressions(
        f"{working_dir}/dem.tif", f"{working_dir}/filled_dem.tif", fix_flats=True
    )
    conditioned_dem = rxr.open_rasterio(
        f"{working_dir}/filled_dem.tif", masked=True
    ).squeeze()
    return conditioned_dem


def flow_accumulation_workflow(dem):
    # wbt condition
    conditioned_dem = condition_dem(dem)
    pysheds_conditioned_dem, grid = to_pysheds(conditioned_dem)
    flow_directions = grid.flowdir(pysheds_conditioned_dem)
    flow_accumulation = grid.accumulation(flow_directions)
    return (
        from_pysheds(pysheds_conditioned_dem),
        from_pysheds(flow_directions),
        from_pysheds(flow_accumulation),
    )


def delineate_subbasins(stream_raster, dem):
    # get pour points from channel network raster
    # these are sorted so that nested basins are handled correctly
    conditioned, flow_directions, flow_accumulation = flow_accumulation_workflow(dem)
    pour_points = identify_pour_points(stream_raster, flow_accumulation)

    subbasins = stream_raster.copy(
        data=np.zeros_like(stream_raster.data, dtype=np.int32)
    )

    pysheds_fdir, grid = to_pysheds(flow_directions)

    for _, row in pour_points.iterrows():
        pour_row = row["row"]
        pour_col = row["col"]

        catchment = grid.catchment(
            x=pour_col,
            y=pour_row,
            fdir=pysheds_fdir,
            xytype="index",
        )

        subbasins.data[catchment] = row["stream_value"]

    return subbasins


def identify_pour_points(stream_raster, flow_accumulation):
    pour_points = []
    for stream_val in np.unique(stream_raster.data):
        if stream_val == 0:
            continue
        rows, cols = np.where(stream_raster.data == stream_val)
        acc_vals = flow_accumulation.data[rows, cols]
        max_idx = np.argmax(acc_vals)
        pour_points.append(
            {
                "row": rows[max_idx],
                "col": cols[max_idx],
                "flow_accumulation": acc_vals[max_idx],
                "stream_value": stream_val,
            }
        )
    pour_points = pd.DataFrame.from_records(pour_points)
    # sort by flow accumulation descending
    pour_points = pour_points.sort_values("flow_accumulation", ascending=False)
    return pour_points
