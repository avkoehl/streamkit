def strahler_order(G):
    # first, find all root nodes
    # then, for each subgraph, find the strahler order of each edge
    G = G.copy()
    roots = [n for n in G.nodes if G.out_degree(n) == 0]
    for root in roots:
        _calculate_strahler(G, root)
    return G


def _calculate_strahler(G, root_node):
    def _strahler_recursive(node):
        # Get upstream edges
        in_edges = list(G.in_edges(node))

        if not in_edges:  # Leaf node/headwater
            return 1

        # Get Strahler numbers of upstream edges
        upstream_orders = []
        for u, v in in_edges:
            if "strahler" not in G.edges[u, v]:
                upstream_order = _strahler_recursive(u)
                G.edges[u, v]["strahler"] = upstream_order
            upstream_orders.append(G.edges[u, v]["strahler"])

        # Calculate Strahler number for current segment
        max_order = max(upstream_orders)
        if upstream_orders.count(max_order) > 1:
            strahler = max_order + 1
        else:
            strahler = max_order

        # Set order for edge going downstream from current node
        out_edges = list(G.out_edges(node))
        if out_edges:  # if not outlet
            u, v = out_edges[0]  # should only be one downstream edge
            G.edges[u, v]["strahler"] = strahler

        return strahler

    _strahler_recursive(root_node)
