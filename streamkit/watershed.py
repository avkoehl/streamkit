import numpy as np
import pandas as pd

from streamkit._internal.adapters import to_pysheds, from_pysheds


def flow_accumulation_workflow(dem):
    pysheds_dem, grid = to_pysheds(dem)

    pit_filled_dem = grid.fill_pits(pysheds_dem)
    pits = grid.detect_pits(pit_filled_dem)
    assert not pits.any()

    flooded_dem = grid.fill_depressions(pit_filled_dem)
    depressions = grid.detect_depressions(flooded_dem)
    assert not depressions.any()

    # inflated_dem = grid.resolve_flats(flooded_dem, eps=1e-11, max_iter=5000)
    inflated_dem = grid.resolve_flats(flooded_dem)
    flats = grid.detect_flats(inflated_dem)
    # assert not flats.any()
    if flats.any():
        num_flats = np.sum(flats)
        print(f"Warning: {num_flats} flat cells remain in DEM after inflation")

    flow_directions = grid.flowdir(inflated_dem)
    flow_accumulation = grid.accumulation(flow_directions)

    return (
        from_pysheds(inflated_dem),
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
