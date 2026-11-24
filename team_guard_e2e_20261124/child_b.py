"""
Team Guard implementation for e2e testing.

This module provides a TeamGuard class that manages concurrent access control
and rate limiting for team-based operations. It ensures that team operations
are properly coordinated and don't exceed configured limits.

Example:
    >>> guard = TeamGuard(team_id="team-alpha", max_concurrent=3, rate_limit=10)
    >>> with guard.acquire("deploy") as allowed:
    ...     if allowed:
    ...         print("Operation permitted")
    ...     else:
    ...         print("Rate limit exceeded")
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional, Generator, Any
from contextlib import contextmanager


@dataclass
class TeamOperation:
    """
    Represents a team operation being tracked by the guard.

    Attributes:
        operation_id: Unique identifier for this operation.
        team_id: Identifier of the team performing the operation.
        operation_type: Type of operation (e.g., "deploy", "test", "build").
        started_at: Unix timestamp when the operation started.
        metadata: Additional operation-specific data.
    """
    operation_id: str
    team_id: str
    operation_type: str
    started_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def duration(self) -> float:
        """Return the elapsed time in seconds since the operation started."""
        return time.time() - self.started_at

    def is_expired(self, timeout: float) -> bool:
        """Check if the operation has exceeded the given timeout in seconds."""
        return self.duration() > timeout


@dataclass
class TeamLimits:
    """
    Configuration limits for a team.

    Attributes:
        max_concurrent: Maximum number of concurrent operations allowed.
        rate_limit: Maximum number of operations per time window.
        rate_window: Time window in seconds for rate limiting.
        operation_timeout: Maximum allowed duration for an operation in seconds.
    """
    max_concurrent: int = 5
    rate_limit: int = 20
    rate_window: float = 60.0
    operation_timeout: float = 300.0

    def __post_init__(self) -> None:
        """Validate limit values after initialization."""
        if self.max_concurrent <= 0:
            raise ValueError("max_concurrent must be positive")
        if self.rate_limit <= 0:
            raise ValueError("rate_limit must be positive")
        if self.rate_window <= 0:
            raise ValueError("rate_window must be positive")
        if self.operation_timeout <= 0:
            raise ValueError("operation_timeout must be positive")


class TeamGuard:
    """
    Manages concurrent access and rate limiting for team operations.

    This class provides thread-safe coordination for team-based operations,
    enforcing both concurrency limits and rate limits. It tracks active
    operations and ensures teams don't exceed their configured quotas.

    Attributes:
        team_id: Identifier of the team this guard manages.
        limits: TeamLimits configuration for this team.

    Example:
        >>> guard = TeamGuard("team-alpha", TeamLimits(max_concurrent=2, rate_limit=5))
        >>> with guard.acquire("deploy") as allowed:
        ...     if allowed:
        ...         # Perform deploy operation
        ...         pass

    Thread Safety:
        All public methods are thread-safe and can be called concurrently
        from multiple threads.
    """

    def __init__(self, team_id: str, limits: Optional[TeamLimits] = None) -> None:
        """
        Initialize a TeamGuard for the given team.

        Args:
            team_id: Unique identifier for the team.
            limits: Optional TeamLimits configuration. Uses defaults if not provided.

        Raises:
            ValueError: If team_id is empty or limits are invalid.
        """
        if not team_id or not team_id.strip():
            raise ValueError("team_id must be a non-empty string")

        self._team_id = team_id.strip()
        self._limits = limits or TeamLimits()
        self._lock = threading.RLock()

        # Active operations tracked by operation_id
        self._active_operations: Dict[str, TeamOperation] = {}

        # Completed operation timestamps for rate limiting
        self._completed_timestamps: list[float] = []

        # Operation counter for generating unique IDs
        self._operation_counter = 0

    @property
    def team_id(self) -> str:
        """Return the team identifier."""
        return self._team_id

    @property
    def limits(self) -> TeamLimits:
        """Return the current limits configuration."""
        return self._limits

    def _generate_operation_id(self, operation_type: str) -> str:
        """Generate a unique operation ID."""
        with self._lock:
            self._operation_counter += 1
            return f"{self._team_id}-{operation_type}-{self._operation_counter}"

    def _cleanup_expired_operations(self, current_time: float) -> None:
        """Remove expired operations and old rate limit timestamps."""
        # Remove expired active operations
        expired_ops = [
            op_id for op_id, op in self._active_operations.items()
            if op.is_expired(self._limits.operation_timeout)
        ]
        for op_id in expired_ops:
            del self._active_operations[op_id]

        # Remove timestamps outside the rate window
        cutoff = current_time - self._limits.rate_window
        self._completed_timestamps = [
            ts for ts in self._completed_timestamps if ts > cutoff
        ]

    def _check_rate_limit(self, current_time: float) -> bool:
        """Check if the rate limit allows a new operation."""
        self._cleanup_expired_operations(current_time)
        return len(self._completed_timestamps) < self._limits.rate_limit

    def _check_concurrency_limit(self) -> bool:
        """Check if the concurrency limit allows a new operation."""
        return len(self._active_operations) < self._limits.max_concurrent

    def can_acquire(self, operation_type: str) -> bool:
        """
        Check if a new operation of the given type can be acquired.

        This checks both concurrency and rate limits without actually
        acquiring the operation.

        Args:
            operation_type: Type of operation to check.

        Returns:
            True if the operation would be allowed, False otherwise.
        """
        current_time = time.time()
        with self._lock:
            self._cleanup_expired_operations(current_time)
            return (self._check_concurrency_limit() and
                    self._check_rate_limit(current_time))

    @contextmanager
    def acquire(
        self,
        operation_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        blocking: bool = False,
        timeout: Optional[float] = None,
    ) -> Generator[tuple[bool, Optional[TeamOperation]], None, None]:
        """
        Acquire permission to perform an operation.

        This context manager handles the full lifecycle of an operation:
        checking limits, registering the operation, and cleaning up on exit.

        Args:
            operation_type: Type of operation (e.g., "deploy", "test", "build").
            metadata: Optional metadata to attach to the operation.
            blocking: If True, wait until the operation can be acquired.
            timeout: Maximum time to wait when blocking (seconds). None = wait forever.

        Yields:
            A tuple of (allowed: bool, operation: TeamOperation | None).
            If allowed is True, operation contains the active operation.
            If allowed is False, operation is None.

        Example:
            >>> guard = TeamGuard("team-alpha")
            >>> with guard.acquire("deploy") as (allowed, op):
            ...     if allowed:
            ...         print(f"Starting {op.operation_id}")
            ...         # Do work
            ...     else:
            ...         print("Operation rejected: limits exceeded")

        Thread Safety:
            This method is thread-safe.
        """
        if not operation_type or not operation_type.strip():
            raise ValueError("operation_type must be a non-empty string")

        op_type = operation_type.strip()
        meta = metadata or {}
        operation: Optional[TeamOperation] = None
        allowed = False

        start_wait = time.time()

        while True:
            current_time = time.time()

            with self._lock:
                self._cleanup_expired_operations(current_time)

                can_proceed = (self._check_concurrency_limit() and
                               self._check_rate_limit(current_time))

                if can_proceed:
                    # Acquire the operation
                    op_id = self._generate_operation_id(op_type)
                    operation = TeamOperation(
                        operation_id=op_id,
                        team_id=self._team_id,
                        operation_type=op_type,
                        started_at=current_time,
                        metadata=meta,
                    )
                    self._active_operations[op_id] = operation
                    allowed = True
                    break

            # Can't proceed right now
            if not blocking:
                break

            # Check timeout
            if timeout is not None and (current_time - start_wait) >= timeout:
                break

            # Wait a bit before retrying
            time.sleep(0.01)

        try:
            yield (allowed, operation)
        finally:
            # Clean up on exit
            if allowed and operation is not None:
                with self._lock:
                    # Record completion timestamp for rate limiting
                    self._completed_timestamps.append(time.time())
                    # Remove from active operations
                    self._active_operations.pop(operation.operation_id, None)

    def get_active_operations(self) -> list[TeamOperation]:
        """
        Get a list of currently active operations.

        Returns:
            List of active TeamOperation objects (copies, safe to modify).
        """
        current_time = time.time()
        with self._lock:
            self._cleanup_expired_operations(current_time)
            return list(self._active_operations.values())

    def get_active_count(self) -> int:
        """
        Get the number of currently active operations.

        Returns:
            Count of active operations.
        """
        current_time = time.time()
        with self._lock:
            self._cleanup_expired_operations(current_time)
            return len(self._active_operations)

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get the current rate limit status.

        Returns:
            Dictionary with 'used', 'limit', 'remaining', and 'window_seconds'.
        """
        current_time = time.time()
        with self._lock:
            self._cleanup_expired_operations(current_time)
            used = len(self._completed_timestamps)
            return {
                "used": used,
                "limit": self._limits.rate_limit,
                "remaining": max(0, self._limits.rate_limit - used),
                "window_seconds": self._limits.rate_window,
            }

    def force_release(self, operation_id: str) -> bool:
        """
        Forcefully release an operation by its ID.

        This should only be used for cleanup in exceptional circumstances
        (e.g., when an operation crashes without proper cleanup).

        Args:
            operation_id: The ID of the operation to release.

        Returns:
            True if the operation was found and released, False otherwise.
        """
        with self._lock:
            if operation_id in self._active_operations:
                self._active_operations.pop(operation_id, None)
                self._completed_timestamps.append(time.time())
                return True
            return False

    def reset(self) -> None:
        """
        Reset the guard state, clearing all operations and rate limit history.

        Warning: This should only be used in testing scenarios.
        """
        with self._lock:
            self._active_operations.clear()
            self._completed_timestamps.clear()
            self._operation_counter = 0


def create_team_guard(team_id: str, **limits_kwargs: Any) -> TeamGuard:
    """
    Factory function to create a TeamGuard with custom limits.

    Args:
        team_id: Unique identifier for the team.
        **limits_kwargs: Keyword arguments passed to TeamLimits constructor.

    Returns:
        A new TeamGuard instance.

    Example:
        >>> guard = create_team_guard("team-alpha", max_concurrent=3, rate_limit=10)
    """
    limits = TeamLimits(**limits_kwargs) if limits_kwargs else TeamLimits()
    return TeamGuard(team_id, limits)