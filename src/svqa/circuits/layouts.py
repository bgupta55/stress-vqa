"""
src/svqa/circuits/layouts.py
Graph layouts and edge colourings for device subgraphs.
"""
import networkx as nx


def line_graph_edges(n: int) -> list:
    """Simple 1D line connectivity: qubit i — qubit i+1."""
    return [(i, i + 1) for i in range(n - 1)]


def square_lattice_edges(rows: int, cols: int) -> list:
    """Square lattice connectivity."""
    edges = []
    for r in range(rows):
        for c in range(cols):
            q = r * cols + c
            if c + 1 < cols:
                edges.append((q, q + 1))
            if r + 1 < rows:
                edges.append((q, q + cols))
    return edges


def heavy_hex_edges(n: int) -> list:
    """
    Approximate heavy-hex connectivity for n qubits.
    Returns edges for a heavy-hex-like graph (chain with periodic skip connections).
    For real device use backend.coupling_map directly.
    """
    edges = [(i, i + 1) for i in range(n - 1)]
    # Add heavy-hex flag connections every 4 qubits
    for i in range(0, n - 2, 4):
        if i + 2 < n:
            edges.append((i, i + 2))
    return list(set(edges))


def edge_color_matchings(edges: list) -> list:
    """
    Decompose edges into matchings using line-graph greedy colouring.
    Heavy-hex has max degree 3 so ≤ 4 colours suffice.
    [UNTESTED on real device graph; logic standard]
    """
    G = nx.Graph(edges)
    L = nx.line_graph(G)
    col = nx.coloring.greedy_color(L, strategy="largest_first")
    if not col:
        return [[]]
    k = max(col.values()) + 1
    out = [[] for _ in range(k)]
    for e, c in col.items():
        out[c].append(e)
    return out
