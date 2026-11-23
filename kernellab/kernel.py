from __future__ import annotations

from typing import Any

from .deadlock import bankers, wait_for
from .memory import allocate, buddy_allocate, page_replace
from .models import Process, SimulationResult
from .scheduling import SCHEDULERS
from .synchronization import dining_philosophers, producer_consumer


class Kernel:
    class Config:
        default_quantum = 2

    def run(self, module: str, algorithm: str, params: dict[str, Any]) -> SimulationResult:
        if module == "cpu":
            processes = [Process(**p) for p in params["processes"]]
            return SCHEDULERS[algorithm]().run(processes, int(params.get("quantum", self.Config.default_quantum)))
        if module == "memory":
            if algorithm == "buddy":
                return buddy_allocate(int(params.get("memory_size", sum(params.get("blocks", [])))), params["requests"])
            return allocate(params["blocks"], params["requests"], algorithm)
        if module == "vm": return page_replace(params["references"], int(params["frames"]), algorithm)
        if module == "deadlock":
            return bankers(params["available"], params["maximum"], params["allocation"]) if algorithm == "bankers" else wait_for(params["graph"])
        if module == "sync":
            return producer_consumer(int(params["buffer_size"]), params["operations"]) if algorithm == "producer_consumer" else dining_philosophers(int(params.get("rounds", 1)), int(params.get("philosophers", 5)))
        raise ValueError(f"unknown module: {module}")
