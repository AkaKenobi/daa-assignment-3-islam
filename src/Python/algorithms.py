"""Implement the six graph methods and your route helper. See the README at the repository root."""

import heapq


class _DSU:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n
        self.largest = 1 if n > 0 else 0

    def find(self, i: int) -> int:
        root = i
        while self.parent[root] != root:
            root = self.parent[root]
        curr = i
        while curr != root:
            nxt = self.parent[curr]
            self.parent[curr] = root
            curr = nxt
        return root

    def union(self, u: int, v: int) -> bool:
        root_u = self.find(u)
        root_v = self.find(v)
        if root_u == root_v:
            return False
        if self.size[root_u] < self.size[root_v]:
            root_u, root_v = root_v, root_u
        self.parent[root_v] = root_u
        self.size[root_u] += self.size[root_v]
        self.components -= 1
        if self.size[root_u] > self.largest:
            self.largest = self.size[root_u]
        return True


def dsu(request):
    """DSU with path compression and union by size/rank; return states."""
    n = request["n"]
    operations = request["operations"]

    uf = _DSU(n)
    states = []
    for u, v in operations:
        uf.union(u, v)
        states.append([uf.components, uf.largest])

    return {"states": states}


def kruskal(request):
    """Separate Kruskal implementation; return cost, edge_ids, components."""
    n = request["n"]
    edges = request["edges"]

    if n == 0:
        return {"cost": 0, "edge_ids": [], "components": 0}

    indexed_edges = [(w, idx, u, v) for idx, (u, v, w) in enumerate(edges) if u != v]
    indexed_edges.sort(key=lambda item: (item[0], item[1]))

    uf = _DSU(n)
    cost = 0
    edge_ids = []

    for w, idx, u, v in indexed_edges:
        if uf.union(u, v):
            cost += w
            edge_ids.append(idx)

    return {
        "cost": cost,
        "edge_ids": edge_ids,
        "components": uf.components,
    }


def prim(request):
    """Separate Prim implementation; restart for every unvisited component."""
    n = request["n"]
    edges = request["edges"]

    if n == 0:
        return {"cost": 0, "edge_ids": [], "components": 0}

    adj = [[] for _ in range(n)]
    for idx, (u, v, w) in enumerate(edges):
        if u == v:
            continue
        adj[u].append((w, idx, v))
        adj[v].append((w, idx, u))

    visited = [False] * n
    cost = 0
    edge_ids = []
    components = 0

    for start in range(n):
        if not visited[start]:
            components += 1
            visited[start] = True
            pq = []
            for edge_tuple in adj[start]:
                heapq.heappush(pq, edge_tuple)

            while pq:
                w, idx, u = heapq.heappop(pq)
                if visited[u]:
                    continue
                visited[u] = True
                cost += w
                edge_ids.append(idx)
                for next_edge in adj[u]:
                    if not visited[next_edge[2]]:
                        heapq.heappush(pq, next_edge)

    return {
        "cost": cost,
        "edge_ids": edge_ids,
        "components": components,
    }


def scc(request):
    """Kosaraju with two DFS passes; return component and condensation."""
    n = request["n"]
    edges = request["edges"]

    if n == 0:
        return {"component": [], "condensation": []}

    adj = [[] for _ in range(n)]
    radj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        radj[v].append(u)

    visited = [False] * n
    head = [0] * n
    order = []

    for start in range(n):
        if not visited[start]:
            visited[start] = True
            stack = [start]
            while stack:
                u = stack[-1]
                neighbors = adj[u]
                idx = head[u]
                if idx < len(neighbors):
                    head[u] = idx + 1
                    v = neighbors[idx]
                    if not visited[v]:
                        visited[v] = True
                        stack.append(v)
                else:
                    stack.pop()
                    order.append(u)

    component = [-1] * n
    comp_id = 0

    for start in reversed(order):
        if component[start] == -1:
            component[start] = comp_id
            stack = [start]
            while stack:
                u = stack.pop()
                for v in radj[u]:
                    if component[v] == -1:
                        component[v] = comp_id
                        stack.append(v)
            comp_id += 1

    cond_edges = set()
    for u, v in edges:
        cu = component[u]
        cv = component[v]
        if cu != cv:
            cond_edges.add((cu, cv))

    condensation = [[cu, cv] for cu, cv in sorted(cond_edges)]
    return {
        "component": component,
        "condensation": condensation,
    }


def topo(request):
    """Three-state DFS and reverse finish order; return acyclic and order."""
    n = request["n"]
    edges = request["edges"]

    if n == 0:
        return {"acyclic": True, "order": []}

    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)

    state = [0] * n
    head = [0] * n
    order = []

    for start in range(n):
        if state[start] == 0:
            state[start] = 1
            stack = [start]
            while stack:
                u = stack[-1]
                neighbors = adj[u]
                idx = head[u]
                if idx < len(neighbors):
                    head[u] = idx + 1
                    v = neighbors[idx]
                    if state[v] == 1:
                        return {"acyclic": False, "order": []}
                    if state[v] == 0:
                        state[v] = 1
                        stack.append(v)
                else:
                    state[u] = 2
                    stack.pop()
                    order.append(u)

    order.reverse()
    return {"acyclic": True, "order": order}


def dag(request):
    """Whole-graph cycle check and DAG relaxation; add your own route helper."""
    n = request["n"]
    source = request["source"]
    edges = request["edges"]

    unweighted_edges = [[u, v] for u, v, _ in edges]
    topo_res = topo({"n": n, "edges": unweighted_edges})

    if not topo_res["acyclic"]:
        return {
            "acyclic": False,
            "distance": [],
            "parent_edge": [],
        }

    order = topo_res["order"]
    adj = [[] for _ in range(n)]
    for idx, (u, v, w) in enumerate(edges):
        adj[u].append((v, w, idx))

    distance = [None] * n
    parent_edge = [-1] * n
    distance[source] = 0

    for u in order:
        du = distance[u]
        if du is not None:
            for v, w, idx in adj[u]:
                dv = distance[v]
                if dv is None or du + w < dv:
                    distance[v] = du + w
                    parent_edge[v] = idx

    return {
        "acyclic": True,
        "distance": distance,
        "parent_edge": parent_edge,
    }


def reconstruct_route(source, target, edges, distance, parent_edge):
    if not distance or target < 0 or target >= len(distance) or distance[target] is None:
        return None

    vertices = [target]
    curr = target
    steps = 0
    max_steps = len(distance)

    while curr != source:
        edge_id = parent_edge[curr]
        if edge_id < 0 or edge_id >= len(edges):
            return None
        u, v, _ = edges[edge_id]
        if v != curr:
            return None
        vertices.append(u)
        curr = u
        steps += 1
        if steps > max_steps:
            return None

    vertices.reverse()
    return vertices