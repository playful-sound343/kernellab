from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int = 0

    def __post_init__(self) -> None:
        if self.arrival < 0 or self.burst <= 0:
            raise ValueError("arrival must be non-negative and burst must be positive")


@dataclass
class Event:
    tick: int
    event_type: str
    payload: dict[str, Any]


@dataclass
class SimulationResult:
    module: str
    algorithm: str
    metrics: dict[str, float]
    events: list[Event] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def serializable(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "algorithm": self.algorithm,
            "metrics": self.metrics,
            "events": [asdict(event) for event in self.events],
            "details": self.details,
        }
