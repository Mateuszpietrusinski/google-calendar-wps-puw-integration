"""Abstract base class for platform connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import CalendarEvent


class ConnectorBase(ABC):
    @abstractmethod
    def fetch(self) -> list[CalendarEvent]:
        """Fetch events from the platform and return as CalendarEvents."""
        ...
