from __future__ import annotations

from .models import SimulationResult


def find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    active, done, stack = set(), set(), []
    def visit(node: str) -> list[str] | None:
        if node in active: return stack[stack.index(node):] + [node]
        if node in done: return None
        active.add(node); stack.append(node)
        for next_node in graph.get(node, []):
            found = visit(next_node)
            if found: return found
        stack.pop(); active.remove(node); done.add(node); return None
    for node in graph:
        found = visit(node)
        if found: return found
    return None


def bankers(available: list[int], maximum: list[list[int]], allocation: list[list[int]]) -> SimulationResult:
    if len(maximum) != len(allocation) or any(len(a) != len(available) for a in maximum + allocation): raise ValueError("matrix dimensions differ")
    need = [[maximum[i][j] - allocation[i][j] for j in range(len(available))] for i in range(len(maximum))]
    work, finish, sequence = available[:], [False] * len(maximum), []
    changed = True
    while changed:
        changed = False
        for i in range(len(maximum)):
            if not finish[i] and all(need[i][j] <= work[j] for j in range(len(work))):
                work = [work[j] + allocation[i][j] for j in range(len(work))]; finish[i] = True; sequence.append(i); changed = True
    safe = all(finish)
    return SimulationResult("deadlock", "bankers", {"safe": float(safe), "safe_processes": float(len(sequence))}, [], {"safe_sequence": sequence, "need": need})


def wait_for(graph: dict[str, list[str]]) -> SimulationResult:
    cycle = find_cycle(graph)
    return SimulationResult("deadlock", "wait_for_dfs", {"deadlocked": float(cycle is not None)}, [], {"cycle": cycle or []})
