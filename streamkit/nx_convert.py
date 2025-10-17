# to and from networkx graphs
import geopandas as gpd
import networkx as nx


def vector_streams_to_networkx(lines: gpd.GeoDataFrame) -> nx.DiGraph:
    """Convert a GeoDataFrame of LineString geometries to a NetworkX directed graph.

    Creates a directed graph where nodes represent stream endpoints (start and end
    coordinates) and edges represent stream segments. All attributes from the input
    GeoDataFrame are preserved as edge attributes in the graph.

    Args:
        lines: GeoDataFrame containing LineString geometries representing stream
            segments, along with any associated attributes.

    Returns:
        A directed graph where edges contain the original geometry, CRS, and all other attributes from the input GeoDataFrame.
    """
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


def networkx_to_gdf(G: nx.DiGraph) -> gpd.GeoDataFrame:
    """Convert a NetworkX directed graph back to a GeoDataFrame.

    Reconstructs vector stream data from a graph representation by converting
    each edge into a LineString geometry connecting its start and end nodes.
    All edge attributes are preserved in the output GeoDataFrame.

    Args:
        G: A directed graph representing stream networks. Edges must contain
            'crs' and 'geometry' attributes, typically created by
            vector_streams_to_networkx().

    Returns:
        A GeoDataFrame with LineString geometries representing stream segments and all edge attributes from the graph (excluding the 'crs' attribute which is set as the GeoDataFrame's CRS).
    """
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
