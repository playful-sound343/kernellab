from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

from .events import EventBus
from .models import SimulationResult


@dataclass
class Block:
    start: int
    size: int


def allocate(blocks: Iterable[int], requests: Iterable[int], algorithm: str) -> SimulationResult:
    # Materialize inputs once so generator workloads behave exactly like lists.
    sizes = list(blocks)
    request_list = list(requests)
    free = [Block(sum(sizes[:i]), size) for i, size in enumerate(sizes)]
    if algorithm not in {"first_fit", "best_fit", "worst_fit"}: raise ValueError("unknown allocation algorithm")
    events, placements, failed, internal = EventBus(), [], 0, 0
    for i, request in enumerate(request_list):
        candidates = [b for b in free if b.size >= request]
        if not candidates:
            failed += 1; events.emit(i, "allocation_failed", request=request); continue
        if algorithm == "first_fit": chosen = candidates[0]
        elif algorithm == "best_fit": chosen = min(candidates, key=lambda b: b.size)
        else: chosen = max(candidates, key=lambda b: b.size)
        placements.append({"request": request, "start": chosen.start, "block_size": chosen.size})
        chosen.start += request; chosen.size -= request
        events.emit(i, "allocated", request=request, start=placements[-1]["start"])
        if chosen.size == 0: free.remove(chosen)
    total = sum(sizes); remaining = sum(b.size for b in free); largest = max((b.size for b in free), default=0)
    return SimulationResult("memory", algorithm, {"utilization": (total - remaining) / max(1, total),
        "failure_rate": failed / max(1, len(request_list)),
        "external_fragmentation": 0 if remaining == 0 else 1 - largest / remaining, "internal_fragmentation": internal}, events.events,
        {"placements": placements, "free_blocks": [b.__dict__ for b in free]})


def buddy_allocate(memory_size: int, requests: Iterable[int]) -> SimulationResult:
    """Split power-of-two blocks on demand; released blocks are intentionally out of scope."""
    if memory_size < 1 or memory_size & (memory_size - 1):
        raise ValueError("memory_size must be a positive power of two")
    request_list = list(requests)
    free: dict[int, list[int]] = {memory_size: [0]}
    placements, bus, failed, internal = [], EventBus(), 0, 0
    for tick, request in enumerate(request_list):
        if request <= 0: raise ValueError("requests must be positive")
        required = 1 << (request - 1).bit_length()
        size = required
        while size <= memory_size and not free.get(size): size *= 2
        if size > memory_size:
            failed += 1; bus.emit(tick, "allocation_failed", request=request); continue
        start = free[size].pop()
        while size > required:
            size //= 2
            free.setdefault(size, []).append(start + size)
        placements.append({"request": request, "start": start, "block_size": required})
        internal += required - request
        bus.emit(tick, "allocated", request=request, start=start, block_size=required)
    remaining = sum(size * len(starts) for size, starts in free.items())
    largest = max((size for size, starts in free.items() if starts), default=0)
    return SimulationResult("memory", "buddy", {"utilization": (memory_size - remaining) / memory_size,
        "failure_rate": failed / max(1, len(request_list)), "internal_fragmentation": float(internal),
        "external_fragmentation": 0.0 if remaining == 0 else 1 - largest / remaining}, bus.events,
        {"placements": placements, "free_lists": free})


def page_replace(references: list[int], frames: int, algorithm: str) -> SimulationResult:
    if frames < 1: raise ValueError("frames must be positive")
    if algorithm not in {"fifo", "lru", "clock", "optimal"}: raise ValueError("unknown page algorithm")
    resident: list[int] = []; order: deque[int] = deque(); last: dict[int, int] = {}; hand = 0; bits: dict[int, int] = {}; bus = EventBus(); faults = 0
    for tick, page in enumerate(references):
        hit = page in resident
        if not hit:
            faults += 1
            if len(resident) < frames: resident.append(page); order.append(page)
            else:
                if algorithm == "fifo": victim = order.popleft()
                elif algorithm == "lru": victim = min(resident, key=lambda x: last[x])
                elif algorithm == "optimal": victim = max(resident, key=lambda x: next((j for j in range(tick + 1, len(references)) if references[j] == x), float("inf")))
                else:
                    while bits.get(resident[hand], 0): bits[resident[hand]] = 0; hand = (hand + 1) % frames
                    victim = resident[hand]; hand = (hand + 1) % frames
                resident[resident.index(victim)] = page
                if victim in order: order.remove(victim)
                order.append(page)
            bus.emit(tick, "page_fault", page=page, frames=list(resident))
        else: bus.emit(tick, "page_hit", page=page, frames=list(resident))
        last[page] = tick; bits[page] = 1
    return SimulationResult("vm", algorithm, {"page_faults": float(faults), "hit_ratio": (len(references) - faults) / max(1, len(references))}, bus.events, {"final_frames": resident})
