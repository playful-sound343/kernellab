from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any


class SystemProbe(ABC):
    @abstractmethod
    def snapshot(self) -> list[dict[str, Any]]: ...


class PsutilProbe(SystemProbe):
    def snapshot(self) -> list[dict[str, Any]]:
        import psutil
        return [{"pid": p.info["pid"], "name": p.info["name"], "memory": p.info["memory_info"].rss if p.info["memory_info"] else 0}
                for p in psutil.process_iter(["pid", "name", "memory_info"])]


class WindowsProbe(PsutilProbe):
    """Host-only extension point. Containers retain the portable psutil behavior."""
    def snapshot(self) -> list[dict[str, Any]]:
        processes = super().snapshot()
        try:
            import win32api  # type: ignore[import-not-found]
            for process in processes: process["windows"] = True
            _ = win32api.GetVersionEx()
        except ImportError:
            for process in processes: process["windows"] = False
        return processes


class FakeProbe(SystemProbe):
    def __init__(self, processes: list[dict[str, Any]] | None = None): self.processes = processes or [{"pid": 1, "name": "init", "memory": 1024}]
    def snapshot(self) -> list[dict[str, Any]]: return self.processes


def stamped_snapshot(probe: SystemProbe) -> dict[str, Any]:
    return {"taken_at": datetime.now(timezone.utc).isoformat(), "source": probe.__class__.__name__, "processes": probe.snapshot()}
