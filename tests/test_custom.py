"""Custom test suite, semantic witness checks, route reconstruction checks, and MSF benchmark."""

import json
import pathlib
import random
import statistics
import subprocess
import sys
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "Python"))
sys.path.insert(0, str(ROOT / "tools"))

import algorithms
import public_validate
import run


CUSTOM_CASES = [
    {
        "name": "dsu boundary: empty, self-union, duplicate unions",
        "justification": "Self-union [0,0] keeps 3 components; [0,1] merges into 2 components (max 2); duplicate [1,0] does not alter state.",
        "input": {"task": "dsu", "n": 3, "operations": [[0, 0], [0, 1], [1, 0], [2, 2]]},
        "output": {"states": [[3, 1], [2, 2], [2, 2], [2, 2]]},
    },
    {
        "name": "kruskal 64-bit negative and positive weights with loops and isolates",
        "justification": "Self-loop [0,0,-500000000] is ignored; parallel edge [0,1,-1000000000] is chosen over [0,1,10]; vertex 3 is isolated (2 components).",
        "input": {
            "task": "kruskal",
            "n": 4,
            "edges": [[0, 0, -500000000], [0, 1, 10], [0, 1, -1000000000], [1, 2, -1000000000]],
        },
        "output": {"cost": -2000000000, "edge_ids": [2, 3], "components": 2},
    },
    {
        "name": "prim 64-bit negative and positive weights with loops and isolates",
        "justification": "Same graph solved by Prim restarting across components; total cost is -2000000000 with 2 components.",
        "input": {
            "task": "prim",
            "n": 4,
            "edges": [[0, 0, -500000000], [0, 1, 10], [0, 1, -1000000000], [1, 2, -1000000000]],
        },
        "output": {"cost": -2000000000, "edge_ids": [2, 3], "components": 2},
    },
    {
        "name": "scc multiple cycles, parallel cross-edges, and isolated vertex",
        "justification": "{0,1} and {2,3} form two SCCs with parallel cross-edges (0->2, 1->3) deduplicated into one condensation edge; vertex 4 is isolated.",
        "input": {
            "task": "scc",
            "n": 5,
            "edges": [[0, 1], [1, 0], [0, 2], [1, 3], [2, 3], [3, 2]],
        },
        "output": {"component": [0, 0, 1, 1, 2], "condensation": [[0, 1]]},
    },
    {
        "name": "topo diamond DAG with isolated vertex",
        "justification": "0 precedes 1 and 2, which both precede 3; vertex 4 is independent. Graph is acyclic.",
        "input": {"task": "topo", "n": 5, "edges": [[0, 1], [0, 2], [1, 3], [2, 3]]},
        "output": {"acyclic": True, "order": [4, 0, 2, 1, 3]},
    },
    {
        "name": "dag cycle unreachable from source",
        "justification": "Source 0 only reaches 1, while 2<->3 forms a disconnected directed cycle. Whole-graph check must return acyclic=False.",
        "input": {
            "task": "dag",
            "n": 4,
            "source": 0,
            "edges": [[0, 1, 5], [2, 3, 1], [3, 2, 1]],
        },
        "output": {"acyclic": False, "distance": [], "parent_edge": []},
    },
    {
        "name": "dag tied shortest paths, parallel edges, and unreachable vertex",
        "justification": "Edges 0 and 1 are parallel [0,1,5]; path 0->1->3 has weight 5+(-3)=2, tying 0->2->3 (1+1=2). Vertex 4 is unreachable (null).",
        "input": {
            "task": "dag",
            "n": 5,
            "source": 0,
            "edges": [[0, 1, 5], [0, 1, 5], [0, 2, 1], [1, 3, -3], [2, 3, 1]],
        },
        "output": {
            "acyclic": True,
            "distance": [0, 5, 1, 2, None],
            "parent_edge": [-1, 0, 2, 3, -1],
        },
    },
]


class CustomAlgorithmTests(unittest.TestCase):
    def test_custom_cases_and_export_files(self):
        tests_dir = ROOT / "tests"
        tests_dir.mkdir(exist_ok=True)

        jsonl_path = tests_dir / "my_cases.jsonl"
        expected_path = tests_dir / "expected_cases.json"
        actual_path = tests_dir / "actual_outputs.jsonl"

        jsonl_path.write_text(
            "".join(json.dumps(c["input"], separators=(",", ":")) + "\n" for c in CUSTOM_CASES),
            encoding="utf-8",
        )
        expected_path.write_text(json.dumps(CUSTOM_CASES, indent=2), encoding="utf-8")

        command = run.build("Python")
        # Run twice in one process to verify state reset on custom mixed requests
        answers = run.execute(command, [c["input"] for c in CUSTOM_CASES] * 2)
        actual_path.write_text(
            "".join(json.dumps(ans, separators=(",", ":")) + "\n" for ans in answers[: len(CUSTOM_CASES)]),
            encoding="utf-8",
        )

        for case, answer in zip(CUSTOM_CASES * 2, answers):
            with self.subTest(name=case["name"]):
                self.assertTrue(public_validate.check(case["input"], answer, case["output"]))

    def test_route_reconstruction_helper(self):
        req = {
            "task": "dag",
            "n": 5,
            "source": 0,
            "edges": [[0, 1, 5], [0, 1, 5], [0, 2, 1], [1, 3, -3], [2, 3, 1]],
        }
        res = algorithms.dag(req)
        dist = res["distance"]
        pe = res["parent_edge"]
        edges = req["edges"]

        # 1. Reachable target 
        route_reachable = algorithms.reconstruct_route(0, 3, edges, dist, pe)
        self.assertIn(route_reachable, [[0, 1, 3], [0, 2, 3]])
        total_w = sum(edges[pe[v]][2] for v in route_reachable[1:])
        self.assertEqual(total_w, dist[3])

        # 2. Source vertex 
        route_source = algorithms.reconstruct_route(0, 0, edges, dist, pe)
        self.assertEqual(route_source, [0])

        # 3. Unreachable target 
        route_unreachable = algorithms.reconstruct_route(0, 4, edges, dist, pe)
        self.assertIsNone(route_unreachable)

        route_parallel = algorithms.reconstruct_route(0, 1, edges, dist, pe)
        self.assertEqual(route_parallel, [0, 1])
        alt_pe = [-1, 1, 2, 3, -1]
        self.assertEqual(algorithms.reconstruct_route(0, 3, edges, dist, alt_pe), [0, 1, 3])
    def test_alternative_valid_and_invalid_witnesses(self):
        msf_req = {"task": "kruskal", "n": 3, "edges": [[0, 1, 2], [0, 1, 2], [1, 2, 3], [0, 2, 3]]}
        msf_exp = {"cost": 5, "components": 1, "edge_ids": [0, 2]}
        self.assertTrue(public_validate.check(msf_req, {"cost": 5, "components": 1, "edge_ids": [1, 3]}, msf_exp))
        self.assertFalse(public_validate.check(msf_req, {"cost": 5, "components": 1, "edge_ids": [0, 1]}, msf_exp))

        topo_req = {"task": "topo", "n": 4, "edges": [[0, 1], [0, 2], [1, 3], [2, 3]]}
        topo_exp = {"acyclic": True, "order": [0, 1, 2, 3]}
        self.assertTrue(public_validate.check(topo_req, {"acyclic": True, "order": [0, 2, 1, 3]}, topo_exp))
        self.assertFalse(public_validate.check(topo_req, {"acyclic": True, "order": [0, 3, 1, 2]}, topo_exp))

    def test_full_scale_deep_chain_limits(self):
        n = 20000
        edges_unweighted = [[i, i + 1] for i in range(n - 1)]
        topo_res = algorithms.topo({"n": n, "edges": edges_unweighted})
        self.assertTrue(topo_res["acyclic"])
        self.assertEqual(len(topo_res["order"]), n)

        scc_res = algorithms.scc({"n": n, "edges": edges_unweighted})
        self.assertEqual(len(set(scc_res["component"])), n)
        self.assertEqual(len(scc_res["condensation"]), n - 1)


def run_benchmark():
    print("\n=== Kruskal vs Prim Benchmark (Seed = 42) ===")
    sizes = [
        (2000, 10000),
        (10000, 50000),
        (50000, 250000),
    ]
    runs = 5

    rng_warm = random.Random(0)
    warm_edges = [[rng_warm.randint(0, 99), rng_warm.randint(0, 99), rng_warm.randint(-100, 100)] for _ in range(500)]
    algorithms.kruskal({"n": 100, "edges": warm_edges})
    algorithms.prim({"n": 100, "edges": warm_edges})

    print(f"{'Size (n, m)':<20} | {'Method':<8} | {'5 Timings (ms)':<42} | {'Median (ms)':<12}")
    print("-" * 90)

    for n, m in sizes:
        rng = random.Random(42 + n)
        edges = [[rng.randint(0, n - 1), rng.randint(0, n - 1), rng.randint(-10**9, 10**9)] for _ in range(m)]
        req = {"n": n, "edges": edges}

        k_times, p_times = [], []
        for _ in range(runs):
            t0 = time.perf_counter()
            res_k = algorithms.kruskal(req)
            t1 = time.perf_counter()
            k_times.append((t1 - t0) * 1000.0)

            t2 = time.perf_counter()
            res_p = algorithms.prim(req)
            t3 = time.perf_counter()
            p_times.append((t3 - t2) * 1000.0)

            assert res_k["cost"] == res_p["cost"]
            assert res_k["components"] == res_p["components"]

        k_med = statistics.median(k_times)
        p_med = statistics.median(p_times)
        print(f"n={n:<6}, m={m:<7} | Kruskal  | {', '.join(f'{t:6.2f}' for t in k_times)} | {k_med:8.2f} ms")
        print(f"n={n:<6}, m={m:<7} | Prim     | {', '.join(f'{t:6.2f}' for t in p_times)} | {p_med:8.2f} ms")
        print("-" * 90)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CustomAlgorithmTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    run_benchmark()