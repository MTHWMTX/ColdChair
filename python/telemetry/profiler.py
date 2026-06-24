from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, TypeVar, Generic

T = TypeVar("T")


@dataclass
class TimingMetric:
    name: str
    elapsed_ms: float
    count: int = 1
    min_ms: float = 0.0
    max_ms: float = 0.0

    def update(self, elapsed_ms: float) -> None:
        self.count += 1
        self.elapsed_ms += elapsed_ms
        if self.min_ms == 0 or elapsed_ms < self.min_ms:
            self.min_ms = elapsed_ms
        if elapsed_ms > self.max_ms:
            self.max_ms = elapsed_ms

    def mean_ms(self) -> float:
        return self.elapsed_ms / max(self.count, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "count": self.count,
            "total_ms": self.elapsed_ms,
            "mean_ms": self.mean_ms(),
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
        }


@dataclass
class PipelineProfile:
    """Comprehensive performance profile of a pipeline execution."""

    total_elapsed_ms: float = 0.0
    metrics: dict[str, TimingMetric] = field(default_factory=dict)
    phase_timings: dict[str, float] = field(default_factory=dict)
    errors_encountered: int = 0

    def record_metric(self, name: str, elapsed_ms: float) -> None:
        if name not in self.metrics:
            self.metrics[name] = TimingMetric(name=name, elapsed_ms=elapsed_ms)
        else:
            self.metrics[name].update(elapsed_ms)

    def record_phase(self, phase: str, elapsed_ms: float) -> None:
        self.phase_timings[phase] = self.phase_timings.get(phase, 0.0) + elapsed_ms

    def add_error(self) -> None:
        self.errors_encountered += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_elapsed_ms": self.total_elapsed_ms,
            "phase_timings": self.phase_timings,
            "metrics": {name: metric.to_dict() for name, metric in self.metrics.items()},
            "errors_encountered": self.errors_encountered,
        }


class Profiler(Generic[T]):
    """Context manager for profiling code blocks."""

    def __init__(self, profile: PipelineProfile, name: str):
        self.profile = profile
        self.name = name
        self.start_time = 0.0

    def __enter__(self) -> Profiler[T]:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        self.profile.record_metric(self.name, elapsed_ms)
        if exc_type is not None:
            self.profile.add_error()


def profile_function(profile: PipelineProfile, name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for profiling function execution."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with Profiler(profile, name):
                return func(*args, **kwargs)

        return wrapper

    return decorator
