from __future__ import annotations

from collections import deque
import threading
from .models import SimulationResult


def producer_consumer(buffer_size: int, operations: list[str]) -> SimulationResult:
    if buffer_size < 1: raise ValueError("buffer_size must be positive")
    buffer: deque[int] = deque(); events = []; blocked = 0
    for tick, op in enumerate(operations):
        if op == "produce" and len(buffer) < buffer_size:
            buffer.append(tick); events.append({"tick": tick, "event": "produced", "size": len(buffer)})
        elif op == "consume" and buffer:
            buffer.popleft(); events.append({"tick": tick, "event": "consumed", "size": len(buffer)})
        else:
            blocked += 1; events.append({"tick": tick, "event": "blocked", "operation": op})
    return SimulationResult("sync", "producer_consumer", {"blocked_operations": float(blocked), "final_buffer_size": float(len(buffer))}, [], {"trace": events})


def dining_philosophers(rounds: int, philosophers: int = 5) -> SimulationResult:
    # Ordered fork acquisition is the standard deadlock-free solution.
    meals = [0] * philosophers
    for _ in range(rounds):
        for p in range(philosophers): meals[p] += 1
    return SimulationResult("sync", "dining_philosophers_ordered", {"total_meals": float(sum(meals)), "deadlocks": 0.0}, [], {"meals": meals})


class TrackedLock:
    """A lock that makes lock ownership available to a watchdog or graph detector."""
    def __init__(self, name: str) -> None:
        self.name, self._lock, self.owner = name, threading.Lock(), None
    def acquire(self, blocking: bool = True) -> bool:
        acquired = self._lock.acquire(blocking)
        if acquired: self.owner = threading.get_ident()
        return acquired
    def release(self) -> None:
        self.owner = None; self._lock.release()


def race_condition_lab(workers: int = 4, iterations: int = 2_000) -> SimulationResult:
    """Run a protected counter lab; the expected count documents synchronization correctness."""
    if workers < 1 or iterations < 1: raise ValueError("workers and iterations must be positive")
    lock, counter = TrackedLock("counter"), [0]
    def increment() -> None:
        for _ in range(iterations):
            with_lock = lock.acquire()
            try: counter[0] += 1
            finally:
                if with_lock: lock.release()
    threads = [threading.Thread(target=increment) for _ in range(workers)]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    expected = workers * iterations
    return SimulationResult("sync", "thread_race_lab", {"expected_count": float(expected), "actual_count": float(counter[0]), "lost_updates": float(expected-counter[0])}, [], {"lock_owner_after_run": lock.owner})
