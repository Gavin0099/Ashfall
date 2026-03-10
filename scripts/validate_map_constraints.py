#!/usr/bin/env python3
"""validate_map_constraints.py — P1-2: map generation constraint checker.

Validates that a node map satisfies the Ashfall v0.1 map generation invariants:

  INV-1  Single start node (exactly one node with is_start=True).
  INV-2  Single final node (exactly one node with is_final=True).
  INV-3  Final node is reachable from start via BFS.
  INV-4  Every non-final node has at least 1 outgoing connection (no dead ends).
  INV-5  All connection targets reference existing node IDs.
  INV-6  No node lists itself as a connection (no self-loops).
  INV-7  Every non-start node is reachable from start (no unreachable islands).
  INV-8  Every node has a non-empty event_pool.

These invariants are partially enforced at runtime by validate_map_connectivity()
in run_engine.py.  This script makes them explicitly testable and reports
violations with node-level detail.
"""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_playability_check import build_node_payloads


def bfs_reachable(nodes: dict[str, dict], start_id: str) -> set[str]:
    visited: set[str] = set()
    queue: deque[str] = deque([start_id])
    while queue:
        node_id = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)
        for conn in nodes[node_id].get("connections", []):
            if conn in nodes:
                queue.append(conn)
    return visited


def validate_map(nodes: dict[str, dict]) -> list[str]:
    """Return a list of violation strings. Empty list = all invariants pass."""
    violations: list[str] = []

    # INV-1: exactly one start node
    starts = [nid for nid, n in nodes.items() if n.get("is_start")]
    if len(starts) != 1:
        violations.append(f"INV-1 FAIL: expected 1 start node, found {len(starts)}: {starts}")

    # INV-2: exactly one final node
    finals = [nid for nid, n in nodes.items() if n.get("is_final")]
    if len(finals) != 1:
        violations.append(f"INV-2 FAIL: expected 1 final node, found {len(finals)}: {finals}")

    if not starts or not finals:
        violations.append("Cannot continue map validation without exactly 1 start and 1 final node.")
        return violations

    start_id = starts[0]
    final_id = finals[0]

    # INV-3: final node reachable from start
    reachable = bfs_reachable(nodes, start_id)
    if final_id not in reachable:
        violations.append(f"INV-3 FAIL: final node '{final_id}' is not reachable from start '{start_id}'")

    # INV-4: every non-final node has >= 1 connection
    for nid, node in nodes.items():
        if not node.get("is_final"):
            conns = node.get("connections", [])
            if len(conns) < 1:
                violations.append(f"INV-4 FAIL: non-final node '{nid}' has 0 connections (dead end)")

    # INV-5: all connection targets exist
    for nid, node in nodes.items():
        for conn in node.get("connections", []):
            if conn not in nodes:
                violations.append(f"INV-5 FAIL: node '{nid}' references unknown connection '{conn}'")

    # INV-6: no self-loops
    for nid, node in nodes.items():
        if nid in node.get("connections", []):
            violations.append(f"INV-6 FAIL: node '{nid}' has a self-loop connection")

    # INV-7: every non-start node is reachable from start
    for nid in nodes:
        if nid != start_id and nid not in reachable:
            violations.append(f"INV-7 FAIL: node '{nid}' is unreachable from start '{start_id}'")

    # INV-8: every node has a non-empty event_pool
    for nid, node in nodes.items():
        pool = node.get("event_pool", [])
        if not pool:
            violations.append(f"INV-8 FAIL: node '{nid}' has an empty event_pool")

    return violations


def main() -> int:
    nodes = build_node_payloads()
    violations = validate_map(nodes)

    if violations:
        print("Map constraint validation FAILED:")
        for v in violations:
            print(f"  {v}")
        return 1

    print(f"Map constraint validation passed ({len(nodes)} nodes)")
    print("  Invariants checked: INV-1 through INV-8")

    # Summary report
    starts = [nid for nid, n in nodes.items() if n.get("is_start")]
    finals = [nid for nid, n in nodes.items() if n.get("is_final")]
    reachable = bfs_reachable(nodes, starts[0])

    print(f"  Start node:    {starts[0]}")
    print(f"  Final node:    {finals[0]}")
    print(f"  Total nodes:   {len(nodes)}")
    print(f"  Reachable:     {len(reachable)} / {len(nodes)}")
    max_conns = max(len(n.get("connections", [])) for n in nodes.values())
    print(f"  Max out-degree:{max_conns}")
    pool_sizes = {nid: len(n.get("event_pool", [])) for nid, n in nodes.items()}
    print(f"  Event pool sizes: {pool_sizes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
