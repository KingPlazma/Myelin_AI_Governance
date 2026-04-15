from dataclasses import dataclass, field
from threading import Lock


@dataclass
class MetricsSnapshot:
    total_requests: int = 0
    blocked_requests: int = 0
    remediated_responses: int = 0
    downstream_errors: int = 0


@dataclass
class MetricsCollector:
    _snapshot: MetricsSnapshot = field(default_factory=MetricsSnapshot)
    _lock: Lock = field(default_factory=Lock)

    def record_request(self) -> None:
        with self._lock:
            self._snapshot.total_requests += 1

    def record_block(self) -> None:
        with self._lock:
            self._snapshot.blocked_requests += 1

    def record_remediation(self) -> None:
        with self._lock:
            self._snapshot.remediated_responses += 1

    def record_downstream_error(self) -> None:
        with self._lock:
            self._snapshot.downstream_errors += 1

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "total_requests": self._snapshot.total_requests,
                "blocked_requests": self._snapshot.blocked_requests,
                "remediated_responses": self._snapshot.remediated_responses,
                "downstream_errors": self._snapshot.downstream_errors
            }
