# Assignment 3: Graph Algorithms for a Campus Festival — Technical Analysis

## 1. Method Specifications, Invariants, Correctness, Boundaries, and Complexity

### 1.1 Disjoint-Set Union (`dsu`)
* **Steps:**
  1. Initialize `parent[i] = i` and `size[i] = 1` for $i \in [0, n-1]$. Set `components = n` and `largest = 1` if $n > 0$ else `0`.
  2. For each pair `[u, v]` in `operations`, find root representatives `root_u` and `root_v` using two-pass iterative **path compression**.
  3. If `root_u != root_v`, attach the smaller tree to the larger tree's root (**union by size**), add its size, decrement `components`, and update `largest = max(largest, size[root_u])`.
  4. Append `[components, largest]` to `states` after each operation.
* **Invariant:** After processing $k$ operations, `parent` encodes a forest of disjoint trees representing the connected components of the first $k$ edges; for every root $r$, `size[r]` is the exact vertex count of its component, `components` is the number of distinct roots, and `largest` is $\max_r \text{size}[r]$.
* **Correctness:** Union by size bounds tree depth by $O(\log n)$ because a node's depth increases only when its component size at least doubles. Iterative path compression links every traversed vertex directly to the component root without altering partition membership.
* **Boundary Cases:** $n=0, q=0$ (`states = []`), self-unions `[u, u]`, duplicate operations `[u, v]` and `[v, u]`, disconnected components, and scale limits up to $n = 100\,000, q = 250\,000$.
* **Complexity:**
  * **Time:** $O(n + q \alpha(n))$ amortized, where $\alpha(n)$ is the inverse Ackermann function.
  * **Memory:** $O(n + q)$ including `parent`, `size`, and the returned `states` array.

---

### 1.2 Kruskal's Minimum Spanning Forest (`kruskal`)
* **Steps:**
  1. If $n = 0$, return `{"cost": 0, "edge_ids": [], "components": 0}`.
  2. Filter out self-loops (`u == v`) while pairing each edge with its original zero-based index `(w, idx, u, v)` and sort by `(w, idx)`.
  3. Initialize `_DSU(n)`. Scan sorted edges: whenever `uf.union(u, v)` succeeds, add `w` to `cost` and append `idx` to `edge_ids`.
  4. Return `cost`, `edge_ids`, and `components = uf.components`.
* **Invariant:** At any point during the scan, the set of accepted edges $F$ is acyclic and is a subset of some Minimum Spanning Forest of $G$.
* **Correctness:** By the **Cut Property**, when considering the lightest edge $(u, v)$ whose endpoints lie in different connected components of $F$, no lighter edge crosses the cut separating $u$'s component from the rest of the graph. Thus $(u, v)$ is safe to add.
* **Boundary Cases:** Empty graph ($n=0$), isolated vertices ($m=0 \implies \text{components} = n$), self-loops with negative weights (ignored), parallel edges, tied weights, negative weights, and 64-bit sums ($\pm 2.5 \times 10^{14}$).
* **Complexity:**
  * **Time:** $O(n + m \log(m + 1))$ dominated by sorting at most $m$ edges.
  * **Memory:** $O(n + m)$ for indexed edges and DSU arrays.

---

### 1.3 Prim's Minimum Spanning Forest (`prim`)
* **Steps:**
  1. If $n = 0$, return `{"cost": 0, "edge_ids": [], "components": 0}`.
  2. Build undirected adjacency lists `adj[0..n-1]` storing `(w, idx, neighbor)`, skipping self-loops (`u == v`).
  3. Maintain `visited = [False] * n`. Iterate `start` from $0$ to $n-1$:
     * If `not visited[start]`, increment `components`, mark `visited[start] = True`, and push all incident edges of `start` into a min-heap `pq`.
     * While `pq` is non-empty, pop `(w, idx, u)`. If `visited[u]` is True, skip it (lazy deletion). Otherwise mark `visited[u] = True`, add `w` to `cost`, append `idx` to `edge_ids`, and push incident edges `(next_w, next_idx, v)` for unvisited neighbors `v`.
* **Invariant:** During the exploration of component $C$, the vertices marked `visited` in $C$ and the edges selected so far form a Minimum Spanning Tree of the subgraph induced by those visited vertices.
* **Correctness:** Each pop selects the minimum-weight edge crossing the cut between the currently visited vertex set $S \subseteq C$ and $C \setminus S$, which is safe by the Cut Property. Restarting the outer loop for every unvisited vertex guarantees every connected component (including isolated vertices) is spanned.
* **Boundary Cases:** $n=0$, isolates ($m=0$), negative weights, self-loops, parallel edges, and 64-bit total costs.
* **Complexity:**
  * **Time:** $O(n + m \log(m + 1))$ with a binary min-heap (`heapq`).
  * **Memory:** $O(n + m)$ for adjacency lists, `visited`, and heap entries.

---

### 1.4 Strongly Connected Components — Kosaraju's Algorithm (`scc`)
* **Steps:**
  1. If $n = 0$, return `{"component": [], "condensation": []}`.
  2. Build forward adjacency list `adj` and transposed adjacency list `radj`.
  3. **Pass 1 (Iterative DFS):** Traverse all vertices $0 \dots n-1$ using an explicit stack and per-vertex neighbor index `head[u]`. When `head[u] == len(adj[u])`, pop `u` and append `u` to `order`.
  4. **Pass 2 (Iterative Transpose DFS):** Iterate through `reversed(order)`. For each unvisited vertex, assign `comp_id` and run an explicit-stack DFS over `radj` to label all mutually reachable vertices with `comp_id`, then increment `comp_id`.
  5. **Condensation:** Insert `(component[u], component[v])` into a hash set `cond_edges` for every original edge `(u, v)` with `component[u] != component[v]`. Return `component` and sorted `condensation`.
* **Invariant:** If SCC $C_1$ has a directed edge to SCC $C_2$ in the condensation graph, then $\max_{u \in C_1} \text{finish}(u) > \max_{v \in C_2} \text{finish}(v)$ in Pass 1.
* **Correctness:** In the transposed graph $G^T$, edges between SCCs are reversed, so the component with the highest finish time has no outgoing edges to any unvisited SCC in $G^T$. DFS from that root visits exactly one SCC.
* **Boundary Cases:** $n=0$, $m=0$ (each vertex is its own SCC), self-loops, duplicate cross-component edges (deduplicated via `set`), single cycle of $n$ vertices, and deep chains up to $n = 100\,000$.
* **Complexity:**
  * **Time:** $O(n + m)$ expected time for two DFS passes and hash-set deduplication (plus sorting unique condensation edges).
  * **Memory:** $O(n + m)$ for `adj`, `radj`, explicit stacks, `head`, and output structures.

---

### 1.5 DFS Topological Ordering (`topo`)
* **Steps:**
  1. If $n = 0$, return `{"acyclic": True, "order": []}`.
  2. Build directed adjacency list `adj`. Initialize 3-state array `state = [0] * n` (`0` = unvisited, `1` = active, `2` = finished) and neighbor pointers `head = [0] * n`.
  3. For each `start` in $0 \dots n-1$ with `state[start] == 0`, set `state[start] = 1` and push `start` onto `stack`.
  4. At the top vertex `u = stack[-1]`, inspect neighbor `v = adj[u][head[u]]` and increment `head[u]`:
     * If `state[v] == 1`, an edge to an active ancestor exists $\implies$ return `{"acyclic": False, "order": []}`.
     * If `state[v] == 0`, set `state[v] = 1` and push `v`.
     * When `head[u] == len(adj[u])`, set `state[u] = 2`, pop `u`, and append `u` to `order`.
  5. Reverse `order` and return `{"acyclic": True, "order": order}`.
* **Invariant:** At every step, vertices with `state == 1` correspond to the active directed path currently on `stack`, and `head[u]` points to the next uninspected neighbor of `u`.
* **Correctness:** A directed graph contains a cycle if and only if DFS encounters a back-edge to an active vertex (`state == 1`). In a DAG, every edge $(u, v)$ explores $v$ and marks $v$ finished (`state == 2`) before $u$ finishes, so reversing the finish order places $u$ before $v$.
* **Boundary Cases:** $n=0$, self-loops (`u -> u` immediately sees `state[u] == 1`), parallel edges, disconnected cyclic components, and deep chains up to $n = 100\,000$.
* **Complexity:**
  * **Time:** $O(n + m)$ because each vertex is pushed/popped once and `head[u]` advances at most $\text{outdeg}(u)$ times.
  * **Memory:** $O(n + m)$.

---

### 1.6 DAG Shortest Paths (`dag`) and Route Reconstruction Helper (`reconstruct_route`)
* **Steps:**
  1. Run `topo` on the unweighted projection of the entire graph. If `not topo_res["acyclic"]`, return `{"acyclic": False, "distance": [], "parent_edge": []}`.
  2. Initialize `distance = [None] * n`, `parent_edge = [-1] * n`, and set `distance[source] = 0`.
  3. Iterate `u` in `topo_res["order"]`. If `distance[u] is not None`, relax each outgoing edge `(v, w, idx)`: if `distance[v] is None` or `distance[u] + w < distance[v]`, update `distance[v] = distance[u] + w` and `parent_edge[v] = idx`.
  4. **Route Helper (`reconstruct_route`):** Given `(source, target, edges, distance, parent_edge)`, return `None` if `distance[target] is None`. Otherwise, walk backward from `curr = target` to `source` via `edge_id = parent_edge[curr]` (`curr = edges[edge_id][0]`), collect vertices, reverse, and return `[source, ..., target]`.
* **Invariant:** When vertex `u` is processed in topological order, all paths from `source` to `u` have already been relaxed, so `distance[u]` equals the true shortest path distance $\delta(\text{source}, u)$ and `parent_edge[u]` stores the incoming edge ID on a shortest path.
* **Correctness:** In a DAG, every path is a subsequence of the topological order. By induction on the topological index, optimal substructure holds and each edge needs to be relaxed at most once. Whole-graph `topo` detects cycles even in components unreachable from `source`.
* **Boundary Cases:** Singleton graph ($n=1, m=0$), negative edge weights where shortest distance equals `-1` (distinguished from unreachable `null`), cycles unreachable from `source`, parallel edges, and 64-bit path sums.
* **Complexity:**
  * **Time:** $O(n + m)$ for `dag`; $O(L)$ for `reconstruct_route` on a route of $L$ vertices.
  * **Memory:** $O(n + m)$ for `dag`; $O(L)$ for `reconstruct_route`.

---

## 2. State Reset and Deep DFS Architecture

* **State Reset:** All six functions in `src/Python/algorithms.py` are pure functions of `request`. All graph structures (`adj`, `radj`, `_DSU`, `state`, `head`, `visited`, `pq`) are allocated as local variables inside each call. No module-level mutable state is modified, ensuring complete isolation across repeated batches and `ping` requests in a single persistent process.
* **Deep DFS Without Call-Stack Overflow:** Instead of recursive calls (which hit Python's call-stack frame limits and incur high memory overhead on graphs with $n = 100\,000$), both `scc` and `topo` use an explicit heap-allocated Python list `stack` paired with a continuation index array `head = [0] * n`. When DFS suspends vertex `u` to visit neighbor `v = adj[u][head[u]]`, `head[u]` is incremented in place. Upon backtracking to `u`, traversal resumes directly at `head[u]` without rescanning earlier neighbors, guaranteeing strict $O(n + m)$ time and $O(n)$ stack space.

---

## 3. Route Reconstruction Helper Calls and Verification

For unreachable targets, `reconstruct_route` returns `None` (documented in docstring; JSON `dag` output still uses `null` in `distance`).

Tested on the custom DAG with $n = 5$, `source = 0`, and `edges`:
* `edge 0`: `[0, 1, 5]` (parallel edge A)
* `edge 1`: `[0, 1, 5]` (parallel edge B)
* `edge 2`: `[0, 2, 1]`
* `edge 3`: `[1, 3, -3]`
* `edge 4`: `[2, 3, 1]`
* Vertex `4` is isolated.

`dag(request)` returns:
```json
{"acyclic": true, "distance": [0, 5, 1, 2, null], "parent_edge": [-1, 0, 2, 3, -1]}
```

1. **Reachable Target (`target = 3`):**
   * Call: `reconstruct_route(0, 3, edges, distance, parent_edge)`
   * Selected `parent_edge` IDs backward: `parent_edge[3] = 3` (`[1, 3, -3]`), `parent_edge[1] = 0` (`[0, 1, 5]`).
   * Returned route: `[0, 1, 3]`.
   * Direction & Weight Check: $0 \xrightarrow{\text{edge } 0 (w=5)} 1 \xrightarrow{\text{edge } 3 (w=-3)} 3$, total weight $= 5 + (-3) = 2 == \text{distance}[3]$.
2. **Source Vertex (`target = 0`):**
   * Call: `reconstruct_route(0, 0, edges, distance, parent_edge)`
   * Selected `parent_edge` IDs: none (`curr == source` immediately).
   * Returned route: `[0]`, total weight $= 0 == \text{distance}[0]$.
3. **Unreachable Target (`target = 4`):**
   * Call: `reconstruct_route(0, 4, edges, distance, parent_edge)`
   * `distance[4]` is `None` (`parent_edge[4] = -1`).
   * Returned route: `None`.
4. **Tied Shortest Paths & Parallel Edges (`target = 1` and `target = 3`):**
   * Parallel edges `0` and `1` both connect `0 -> 1` with weight `5`. Because relaxation uses strict inequality (`du + w < dv`), `parent_edge[1] = 0` is kept, and `reconstruct_route(0, 1, edges, distance, parent_edge)` returns `[0, 1]`.
   * For `target = 3`, path `0 -> 2 -> 3` via `edge 2` ($w=1$) and `edge 4` ($w=1$) also has weight $1 + 1 = 2$. Passing the alternative valid parent array `alt_pe = [-1, 1, 2, 4, -1]` to `reconstruct_route(0, 3, edges, distance, alt_pe)` returns `[0, 2, 3]` with weight $1 + 1 = 2$.

---

## 4. Kruskal vs. Prim Benchmark

### Experimental Setup
* **Hardware & OS:** AMD Ryzen 7 7735HS, 16 GB RAM, Windows 11 (64-bit).
* **Runtime:** Python 3.13 (CPython, 64-bit).
* **Generator & Seed:** Deterministic `random.Random(42 + n)` generating $m$ undirected edges with endpoints in $[0, n-1]$ and integer weights in $[-10^9, 10^9]$.
* **Timer, Warm-up & Boundary:** `time.perf_counter()` (in milliseconds). A warm-up run on $n = 100, m = 500$ is executed prior to timing. The timing boundary encloses **only** the `algorithms.kruskal(req)` and `algorithms.prim(req)` calls. Correctness of `cost` and `components` is asserted on every run.
* **Command:** `python tests/test_custom.py`

### Benchmark Timings (5 Runs per Method per Size)

| Graph Size ($n, m$) | Method | Run 1 (ms) | Run 2 (ms) | Run 3 (ms) | Run 4 (ms) | Run 5 (ms) | Median (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| $n = 2\,000,\; m = 10\,000$ | **Kruskal** | 9.61 | 8.35 | 8.36 | 8.57 | 11.20 | **8.57 ms** |
| $n = 2\,000,\; m = 10\,000$ | **Prim** | 8.93 | 8.50 | 9.72 | 11.10 | 11.06 | **9.72 ms** |
| $n = 10\,000,\; m = 50\,000$ | **Kruskal** | 60.38 | 64.18 | 65.73 | 81.48 | 84.91 | **65.73 ms** |
| $n = 10\,000,\; m = 50\,000$ | **Prim** | 91.31 | 87.31 | 106.47 | 111.67 | 164.99 | **106.47 ms** |
| $n = 50\,000,\; m = 250\,000$ | **Kruskal** | 529.02 | 462.51 | 496.91 | 499.76 | 518.98 | **499.76 ms** |
| $n = 50\,000,\; m = 250\,000$ | **Prim** | 738.01 | 737.90 | 766.48 | 771.36 | 771.82 | **766.48 ms** |

### Analysis: Observations, Limitations, and Asymptotic Comparison
* **Asymptotic Argument:** Both Kruskal and lazy-heap Prim run in $O(n + m \log(m + 1))$ time and $O(n + m)$ space.
* **Empirical Observations:** Across all three sizes, Kruskal is consistently $\approx 1.5\times - 1.6\times$ faster than Prim in Python. Kruskal performs one bulk `list.sort()` call (executed in optimized C via Timsort) followed by flat integer list lookups in `_DSU`. Prim must allocate $n$ adjacency lists of $2m$ tuples and perform up to $2m$ `heapq.heappush` and `heapq.heappop` calls in an interpreted Python loop.
* **Experimental Limitations:** Measurements reflect CPython interpreter overhead (tuple allocations and dynamic type comparisons in `heapq`) and uniform random graph topology. On dense graphs ($m \approx n^2$), indexed heaps or dense matrix approaches can change relative performance.

---

## 5. Build, Run, and Test Commands

Run from the repository root:

```sh
# 1. Verify environment setup and ping response
python tools/run.py --setup

# 2. Run all 36 public checks and state-reset batch verification
python tools/run.py --check

# 3. Run custom unit tests, witness validations, route helper checks, and benchmarks
python tests/test_custom.py

# 4. Run the JSON-Lines adapter directly on custom test inputs
python tools/run.py --input tests/my_cases.jsonl
```

---

## 6. Sources and AI Assistance Acknowledgment

* **Sources:** Course lecture slides (Lecture 7, Astana IT University), the official DAA Assignment 3 interactive specification and visualizer (https://rzhaniya.github.io/daa-assignment-3-festival/), and standard graph theory materials (CLRS).
* **AI Assistance:** AI was used for minor syntax debugging, formatting the Markdown tables, and checking English grammar.
