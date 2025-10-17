import networkx as nx


def label_mainstem(G: nx.DiGraph) -> nx.DiGraph:
    """Label mainstem edges in a stream network graph.

    Identifies and labels the main channel (mainstem) of each drainage network
    by traversing from outlet nodes upstream. Edges are labeled with a 'mainstem'
    attribute set to True for mainstem edges and False for tributaries.

    Args:
        G: A directed graph representing a stream network. Each edge must have
            'strahler' and 'max_upstream_length' attributes. If these are missing,
            run strahler_order() and upstream_length() first.

    Returns:
        A copy of the input graph with edges labeled with a 'mainstem' boolean attribute indicating whether each edge is part of the main channel.

    Raises:
        ValueError: If any edge is missing the required 'strahler' or
            'max_upstream_length' attributes.
    """
    G = G.copy()

    # make sure that edges have a 'strahler' attribute
    if not all("strahler" in G.edges[e] for e in G.edges):
        raise ValueError(
            "All edges must have a 'strahler' attribute. Run strahler_order() first."
        )
    if not all("max_upstream_length" in G.edges[e] for e in G.edges):
        raise ValueError(
            "All edges must have a 'max_upstream_length' attribute. Run upstream_length() first."
        )

    # initialize all edges as not mainstem_edge
    for e in G.edges:
        G.edges[e]["mainstem"] = False

    roots = [n for n in G.nodes if G.out_degree(n) == 0]
    for root in roots:
        _label_mainstem(G, root)
    return G


def _label_mainstem(G, root):
    # starting from the root, work upstream
    # following the highest strahler order at each junction
    # if there is a tie - go to the branch that is longest upstream
    current_node = root
    while True:
        in_edges = list(G.in_edges(current_node))
        if len(in_edges) == 0:
            break

        # get the strahler orders of the incoming edges
        strahler_orders = [G.edges[e]["strahler"] for e in in_edges]
        max_strahler = max(strahler_orders)

        # filter to only the edges with the max strahler order
        candidates = [
            e for e, order in zip(in_edges, strahler_orders) if order == max_strahler
        ]

        if len(candidates) == 1:
            mainstem_edge = candidates[0]
        else:
            # if there is a tie, choose the one with the longest upstream length
            upstream_lengths = [G.edges[e]["max_upstream_length"] for e in candidates]
            max_length = max(upstream_lengths)
            longest_candidates = [
                e
                for e, length in zip(candidates, upstream_lengths)
                if length == max_length
            ]
            if len(longest_candidates) > 1:
                print(
                    f"Warning: Tie in both strahler order and upstream length at node {current_node}. Arbitrarily choosing one."
                )
            mainstem_edge = longest_candidates[0]

        # label the mainstem edge
        G.edges[mainstem_edge]["mainstem"] = True

        # move to the upstream node of the chosen edge
        current_node = mainstem_edge[0]
