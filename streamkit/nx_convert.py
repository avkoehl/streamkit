# to and from networkx graphs
import geopandas as gpd
import networkx as nx


def vector_streams_to_networkx(lines):
    """lines is goepandas dataframe with linestrings"""
    G = nx.DiGraph()
    for _, line in lines.iterrows():
        start = line.geometry.coords[0]
        end = line.geometry.coords[-1]
        G.add_edge(
            start,
            end,
            crs=lines.crs,
            geometry=line.geometry,
            **line.drop("geometry").to_dict(),
        )
    return G


def networkx_to_gdf(G):
    edges = []
    for u, v, data in G.edges(data=True):
        edges.append(
            {
                "geometry": gpd.points_from_xy([u[0], v[0]], [u[1], v[1]]).unary_union,
                **data,
            }
        )
    gdf = gpd.GeoDataFrame(edges, geometry="geometry")
    gdf = gdf.set_crs(gdf["crs"].iloc[0])
    gdf = gdf.drop(columns=["crs"])
    return gdf
