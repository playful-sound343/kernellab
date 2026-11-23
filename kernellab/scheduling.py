from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Iterable

from .events import EventBus
from .models import Process, SimulationResult


@dataclass
class _State:
    process: Process
    remaining: int
    first_start: int | None = None
    finish: int | None = None


class Scheduler(ABC):
    name: str

    @abstractmethod
    def run(self, processes: Iterable[Process], quantum: int = 2) -> SimulationResult: ...

    @staticmethod
    def _finish(name: str, states: list[_State], bus: EventBus) -> SimulationResult:
        metrics: dict[str, float] = {}
        waiting, turnaround, response = [], [], []
        rows = []
        for state in states:
            assert state.finish is not None and state.first_start is not None
            p = state.process
            tat = state.finish - p.arrival
            wait = tat - p.burst
            resp = state.first_start - p.arrival
            waiting.append(wait); turnaround.append(tat); response.append(resp)
            rows.append({"pid": p.pid, "arrival": p.arrival, "finish": state.finish,
                         "waiting": wait, "turnaround": tat, "response": resp})
        metrics.update(avg_waiting_time=sum(waiting) / len(states),
                       avg_turnaround_time=sum(turnaround) / len(states),
                       avg_response_time=sum(response) / len(states),
                       makespan=max(s.finish or 0 for s in states),
                       throughput=len(states) / max(1, max(s.finish or 0 for s in states)))
        return SimulationResult("cpu", name, metrics, bus.events, {"processes": rows})


class FCFSScheduler(Scheduler):
    name = "fcfs"
    def run(self, processes: Iterable[Process], quantum: int = 2) -> SimulationResult:
        states = [_State(p, p.burst) for p in sorted(processes, key=lambda p: (p.arrival, p.pid))]
        if not states: raise ValueError("at least one process is required")
        bus, now = EventBus(), 0
        for s in states:
            now = max(now, s.process.arrival); s.first_start = now
            bus.emit(now, "dispatch", pid=s.process.pid)
            now += s.remaining; s.remaining = 0; s.finish = now
            bus.emit(now, "complete", pid=s.process.pid)
        return self._finish(self.name, states, bus)


class SJFNonPreemptiveScheduler(FCFSScheduler):
    name = "sjf"
    def run(self, processes: Iterable[Process], quantum: int = 2) -> SimulationResult:
        incoming = sorted(processes, key=lambda p: (p.arrival, p.pid))
        if not incoming: raise ValueError("at least one process is required")
        states = [_State(p, p.burst) for p in incoming]; ready: list[tuple[int, str, _State]] = []
        bus, now, i = EventBus(), 0, 0
        while i < len(states) or ready:
            if not ready: now = max(now, states[i].process.arrival)
            while i < len(states) and states[i].process.arrival <= now:
                s = states[i]; heappush(ready, (s.remaining, s.process.pid, s)); i += 1
            _, _, s = heappop(ready); s.first_start = now; bus.emit(now, "dispatch", pid=s.process.pid)
            now += s.remaining; s.remaining = 0; s.finish = now; bus.emit(now, "complete", pid=s.process.pid)
        return self._finish(self.name, states, bus)


class SRTFScheduler(Scheduler):
    name = "srtf"
    def run(self, processes: Iterable[Process], quantum: int = 2) -> SimulationResult:
        incoming = sorted(processes, key=lambda p: (p.arrival, p.pid))
        if not incoming: raise ValueError("at least one process is required")
        states = [_State(p, p.burst) for p in incoming]; ready: list[tuple[int, str, _State]] = []
        bus, now, i = EventBus(), 0, 0
        while i < len(states) or ready:
            if not ready: now = max(now, states[i].process.arrival)
            while i < len(states) and states[i].process.arrival <= now:
                s = states[i]; heappush(ready, (s.remaining, s.process.pid, s)); i += 1
            _, _, s = heappop(ready)
            if s.first_start is None: s.first_start = now
            bus.emit(now, "dispatch", pid=s.process.pid)
            next_arrival = states[i].process.arrival if i < len(states) else float("inf")
            duration = min(s.remaining, next_arrival - now); now += int(duration); s.remaining -= int(duration)
            while i < len(states) and states[i].process.arrival <= now:
                x = states[i]; heappush(ready, (x.remaining, x.process.pid, x)); i += 1
            if s.remaining: heappush(ready, (s.remaining, s.process.pid, s))
            else: s.finish = now; bus.emit(now, "complete", pid=s.process.pid)
        return self._finish(self.name, states, bus)


class RoundRobinScheduler(Scheduler):
    name = "round_robin"
    def run(self, processes: Iterable[Process], quantum: int = 2) -> SimulationResult:
        if quantum <= 0: raise ValueError("quantum must be positive")
        incoming = sorted(processes, key=lambda p: (p.arrival, p.pid))
        if not incoming: raise ValueError("at least one process is required")
        states = [_State(p, p.burst) for p in incoming]; ready: deque[_State] = deque(); bus = EventBus(); now = i = 0
        while i < len(states) or ready:
            if not ready: now = max(now, states[i].process.arrival)
            while i < len(states) and states[i].process.arrival <= now: ready.append(states[i]); i += 1
            s = ready.popleft(); s.first_start = s.first_start if s.first_start is not None else now
            run_for = min(quantum, s.remaining); bus.emit(now, "dispatch", pid=s.process.pid, slice=run_for)
            now += run_for; s.remaining -= run_for
            while i < len(states) and states[i].process.arrival <= now: ready.append(states[i]); i += 1
            if s.remaining: ready.append(s)
            else: s.finish = now; bus.emit(now, "complete", pid=s.process.pid)
        return self._finish(self.name, states, bus)


class PriorityScheduler(SJFNonPreemptiveScheduler):
    name = "priority"
    def run(self, processes: Iterable[Process], quantum: int = 2) -> SimulationResult:
        incoming = sorted(processes, key=lambda p: (p.arrival, p.pid))
        if not incoming: raise ValueError("at least one process is required")
        states = [_State(p, p.burst) for p in incoming]; ready: list[tuple[int, int, str, _State]] = []
        bus, now, i = EventBus(), 0, 0
        while i < len(states) or ready:
            if not ready: now = max(now, states[i].process.arrival)
            while i < len(states) and states[i].process.arrival <= now:
                s = states[i]; heappush(ready, (s.process.priority, s.process.arrival, s.process.pid, s)); i += 1
            _, _, _, s = heappop(ready); s.first_start = now; bus.emit(now, "dispatch", pid=s.process.pid)
            now += s.remaining; s.remaining = 0; s.finish = now; bus.emit(now, "complete", pid=s.process.pid)
        return self._finish(self.name, states, bus)


SCHEDULERS = {x.name: x for x in (FCFSScheduler, SJFNonPreemptiveScheduler, SRTFScheduler, RoundRobinScheduler, PriorityScheduler)}
