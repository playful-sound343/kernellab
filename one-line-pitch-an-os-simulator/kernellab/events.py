from __future__ import annotations

from collections.abc import Callable
from .models import Event


class EventBus:
    """Small Observer-pattern event bus shared by simulations."""

    def __init__(self) -> None:
        self.events: list[Event] = []
        self._observers: list[Callable[[Event], None]] = []

    def subscribe(self, observer: Callable[[Event], None]) -> None:
        self._observers.append(observer)

    def emit(self, tick: int, event_type: str, **payload: object) -> None:
        event = Event(tick, event_type, dict(payload))
        self.events.append(event)
        for observer in self._observers:
            observer(event)
