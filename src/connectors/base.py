"""
NovaIR Connector Base Classes - Abstract interfaces for sensors and actuators.

These classes define the contract that concrete connectors must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ConnectorInfo:
    """Information about a connector."""
    name: str
    type: str  # "sensor" or "actuator"
    description: str
    metrics: List[str]
    metadata: Dict[str, Any]


class Connector(ABC):
    """Base class for all connectors."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection. Returns True if successful."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected."""
        pass

    @abstractmethod
    def get_info(self) -> ConnectorInfo:
        """Get connector information."""
        pass


class SensorConnector(Connector):
    """Base class for sensor connectors (read-only)."""

    @abstractmethod
    def read(self, metric: str) -> float:
        """Read a single metric value."""
        pass

    @abstractmethod
    def read_all(self) -> Dict[str, float]:
        """Read all available metrics."""
        pass

    @abstractmethod
    def get_available_metrics(self) -> List[str]:
        """List available metric names."""
        pass


class ActuatorConnector(Connector):
    """Base class for actuator connectors (write)."""

    @abstractmethod
    def execute(self, action: str, parameters: Dict[str, Any]) -> bool:
        """Execute an action with parameters. Returns True if successful."""
        pass

    @abstractmethod
    def get_available_actions(self) -> List[str]:
        """List available action names."""
        pass

    @abstractmethod
    def get_action_parameters(self, action: str) -> Dict[str, Any]:
        """Get parameter schema for an action."""
        pass
