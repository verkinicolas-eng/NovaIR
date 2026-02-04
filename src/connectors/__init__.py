# NovaIR Connectors
# Interfaces for reading sensors and controlling actuators

from .base import Connector, SensorConnector, ActuatorConnector
from .system import SystemConnector
from .simulation import SimulatedSystem

__version__ = "0.1.0"
__all__ = [
    "Connector", "SensorConnector", "ActuatorConnector",
    "SystemConnector",
    "SimulatedSystem",
]
