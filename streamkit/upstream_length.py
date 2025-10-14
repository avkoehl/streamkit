import networkx as nx


def upstream_length(G):
    # confirm that all edges have a 'geometry' attribute
    G = G.copy()
    if not all("geometry" in G.edges[e] for e in G.edges):
        raise ValueError(
            "All edges must have a 'geometry' attribute. Cannot compute upstream length."
        )

    for u, v, d in G.edges(data=True):
        d["max_upstream_length"] = 0.0

    for node in nx.topological_sort(G):
        upstream = list(G.in_edges(node, data=True))

        if len(upstream) == 0:
            # this is headwater, set length to the length of the edge.geometry
            out_edges = list(G.out_edges(node, data=True))
            if len(out_edges) == 1:
                _, _, out_data = out_edges[0]
                length = out_data.get("geometry").length
        elif len(upstream) == 1:
            u, v, data = upstream[0]
            length = data.get("max_upstream_length") + data.get("geometry").length
        else:
            max_upstream_length = 0.0
            for u, v, data in upstream:
                upstream_length = (
                    data.get("max_upstream_length") + data.get("geometry").length
                )
                if upstream_length > max_upstream_length:
                    max_upstream_length = upstream_length
            length = max_upstream_length

        for _, v, out_data in G.out_edges(node, data=True):
            out_data["max_upstream_length"] = length
    return G
