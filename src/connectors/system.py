"""
NovaIR System Connector - Reads real system metrics (CPU, memory, etc.).

This connector interfaces with the operating system to read real metrics.
Works on Windows, Linux, and macOS.
"""

import os
import platform
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .base import SensorConnector, ConnectorInfo

# Try to import psutil for cross-platform metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class SystemConnector(SensorConnector):
    """Connector for reading system metrics (CPU, memory, disk, etc.)."""

    def __init__(self):
        self._connected = False
        self._cache: Dict[str, float] = {}

    def connect(self) -> bool:
        """Check if system metrics are available."""
        self._connected = PSUTIL_AVAILABLE
        return self._connected

    def disconnect(self) -> None:
        """Nothing to disconnect."""
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected and PSUTIL_AVAILABLE

    def get_info(self) -> ConnectorInfo:
        return ConnectorInfo(
            name="SystemConnector",
            type="sensor",
            description="Reads system metrics (CPU, memory, disk)",
            metrics=self.get_available_metrics(),
            metadata={
                "platform": platform.system(),
                "psutil_available": PSUTIL_AVAILABLE,
            }
        )

    def get_available_metrics(self) -> List[str]:
        """List available system metrics."""
        metrics = [
            "cpu.percent",
            "cpu.count",
            "cpu.freq",
            "memory.percent",
            "memory.used_gb",
            "memory.available_gb",
            "disk.percent",
            "disk.used_gb",
            "disk.free_gb",
        ]

        # Add per-CPU metrics
        if PSUTIL_AVAILABLE:
            cpu_count = psutil.cpu_count()
            for i in range(cpu_count):
                metrics.append(f"cpu.{i}.percent")

        return metrics

    def read(self, metric: str) -> float:
        """Read a single metric."""
        if not self.is_connected():
            return 0.0

        parts = metric.split(".")

        try:
            if parts[0] == "cpu":
                return self._read_cpu(parts[1:])
            elif parts[0] == "memory":
                return self._read_memory(parts[1:])
            elif parts[0] == "disk":
                return self._read_disk(parts[1:])
        except Exception as e:
            print(f"Error reading {metric}: {e}")

        return 0.0

    def read_all(self) -> Dict[str, float]:
        """Read all metrics."""
        result = {}
        for metric in self.get_available_metrics():
            result[metric] = self.read(metric)
        return result

    def _read_cpu(self, parts: List[str]) -> float:
        """Read CPU metrics."""
        if not parts:
            return 0.0

        if parts[0] == "percent":
            return psutil.cpu_percent(interval=0.1)
        elif parts[0] == "count":
            return float(psutil.cpu_count())
        elif parts[0] == "freq":
            freq = psutil.cpu_freq()
            return freq.current if freq else 0.0
        elif parts[0].isdigit():
            # Per-CPU percentage
            cpu_idx = int(parts[0])
            percents = psutil.cpu_percent(interval=0.1, percpu=True)
            if cpu_idx < len(percents):
                return percents[cpu_idx]

        return 0.0

    def _read_memory(self, parts: List[str]) -> float:
        """Read memory metrics."""
        if not parts:
            return 0.0

        mem = psutil.virtual_memory()

        if parts[0] == "percent":
            return mem.percent
        elif parts[0] == "used_gb":
            return mem.used / (1024 ** 3)
        elif parts[0] == "available_gb":
            return mem.available / (1024 ** 3)
        elif parts[0] == "total_gb":
            return mem.total / (1024 ** 3)

        return 0.0

    def _read_disk(self, parts: List[str]) -> float:
        """Read disk metrics."""
        if not parts:
            return 0.0

        # Use root partition by default
        path = "/" if platform.system() != "Windows" else "C:\\"
        disk = psutil.disk_usage(path)

        if parts[0] == "percent":
            return disk.percent
        elif parts[0] == "used_gb":
            return disk.used / (1024 ** 3)
        elif parts[0] == "free_gb":
            return disk.free / (1024 ** 3)
        elif parts[0] == "total_gb":
            return disk.total / (1024 ** 3)

        return 0.0


# Optional GPU connector (requires pynvml for NVIDIA)
class GPUConnector(SensorConnector):
    """Connector for reading NVIDIA GPU metrics."""

    def __init__(self):
        self._connected = False
        self._nvml_available = False

        try:
            import pynvml
            self._nvml = pynvml
            self._nvml_available = True
        except ImportError:
            self._nvml = None

    def connect(self) -> bool:
        if not self._nvml_available:
            return False

        try:
            self._nvml.nvmlInit()
            self._connected = True
            return True
        except Exception:
            return False

    def disconnect(self) -> None:
        if self._connected and self._nvml:
            try:
                self._nvml.nvmlShutdown()
            except Exception:
                pass
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_info(self) -> ConnectorInfo:
        return ConnectorInfo(
            name="GPUConnector",
            type="sensor",
            description="Reads NVIDIA GPU metrics",
            metrics=self.get_available_metrics(),
            metadata={"nvml_available": self._nvml_available}
        )

    def get_available_metrics(self) -> List[str]:
        if not self._connected:
            return []

        return [
            "gpu.0.temperature",
            "gpu.0.utilization",
            "gpu.0.memory_used_mb",
            "gpu.0.memory_total_mb",
            "gpu.0.power_draw_w",
        ]

    def read(self, metric: str) -> float:
        if not self._connected:
            return 0.0

        parts = metric.split(".")
        if len(parts) < 3 or parts[0] != "gpu":
            return 0.0

        try:
            gpu_idx = int(parts[1])
            handle = self._nvml.nvmlDeviceGetHandleByIndex(gpu_idx)

            if parts[2] == "temperature":
                return float(self._nvml.nvmlDeviceGetTemperature(
                    handle, self._nvml.NVML_TEMPERATURE_GPU))
            elif parts[2] == "utilization":
                util = self._nvml.nvmlDeviceGetUtilizationRates(handle)
                return float(util.gpu)
            elif parts[2] == "memory_used_mb":
                mem = self._nvml.nvmlDeviceGetMemoryInfo(handle)
                return mem.used / (1024 ** 2)
            elif parts[2] == "memory_total_mb":
                mem = self._nvml.nvmlDeviceGetMemoryInfo(handle)
                return mem.total / (1024 ** 2)
            elif parts[2] == "power_draw_w":
                return self._nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0

        except Exception as e:
            print(f"Error reading GPU metric {metric}: {e}")

        return 0.0

    def read_all(self) -> Dict[str, float]:
        result = {}
        for metric in self.get_available_metrics():
            result[metric] = self.read(metric)
        return result
