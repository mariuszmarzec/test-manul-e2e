"""
Tests for team_guard_e2e_20261124.child_b module.

Covers normal operation flow, concurrency limits, rate limiting,
and edge cases including invalid inputs and timeout behavior.
"""

import pytest
import time
import threading

from team_guard_e2e_20261124.child_b import (
    TeamGuard,
    TeamLimits,
    TeamOperation,
    create_team_guard,
)


class TestTeamLimits:
    """Tests for the TeamLimits dataclass."""

    def test_valid_limits(self):
        """Test that valid limit values are accepted."""
        limits = TeamLimits(max_concurrent=5, rate_limit=20, rate_window=60.0)
        assert limits.max_concurrent == 5
        assert limits.rate_limit == 20
        assert limits.rate_window == 60.0
        assert limits.operation_timeout == 300.0

    def test_default_limits(self):
        """Test default limit values."""
        limits = TeamLimits()
        assert limits.max_concurrent == 5
        assert limits.rate_limit == 20
        assert limits.rate_window == 60.0
        assert limits.operation_timeout == 300.0

    def test_invalid_max_concurrent_zero(self):
        """Test that zero max_concurrent raises ValueError."""
        with pytest.raises(ValueError, match="max_concurrent must be positive"):
            TeamLimits(max_concurrent=0)

    def test_invalid_max_concurrent_negative(self):
        """Test that negative max_concurrent raises ValueError."""
        with pytest.raises(ValueError, match="max_concurrent must be positive"):
            TeamLimits(max_concurrent=-1)

    def test_invalid_rate_limit_zero(self):
        """Test that zero rate_limit raises ValueError."""
        with pytest.raises(ValueError, match="rate_limit must be positive"):
            TeamLimits(rate_limit=0)

    def test_invalid_rate_window_zero(self):
        """Test that zero rate_window raises ValueError."""
        with pytest.raises(ValueError, match="rate_window must be positive"):
            TeamLimits(rate_window=0.0)

    def test_invalid_operation_timeout_zero(self):
        """Test that zero operation_timeout raises ValueError."""
        with pytest.raises(ValueError, match="operation_timeout must be positive"):
            TeamLimits(operation_timeout=0.0)


class TestTeamOperation:
    """Tests for the TeamOperation dataclass."""

    def test_creation_and_duration(self):
        """Test basic operation creation and duration tracking."""
        op = TeamOperation(
            operation_id="op-1",
            team_id="team-alpha",
            operation_type="deploy",
        )
        assert op.operation_id == "op-1"
        assert op.team_id == "team-alpha"
        assert op.operation_type == "deploy"
        assert op.duration() >= 0

    def test_is_expired_within_timeout(self):
        """Test that operation is not expired within timeout."""
        op = TeamOperation(
            operation_id="op-1",
            team_id="team-alpha",
            operation_type="deploy",
        )
        # Fresh operation should not be expired with any reasonable timeout
        assert op.is_expired(300.0) is False

    def test_is_expired_long_timeout(self):
        """Test that operation eventually expires."""
        op = TeamOperation(
            operation_id="op-1",
            team_id="team-alpha",
            operation_type="deploy",
        )
        time.sleep(0.1)
        assert op.is_expired(0.01) is True


class TestTeamGuardInit:
    """Tests for TeamGuard initialization."""

    def test_basic_init(self):
        """Test basic guard creation."""
        guard = TeamGuard("team-alpha")
        assert guard.team_id == "team-alpha"
        assert isinstance(guard.limits, TeamLimits)

    def test_init_with_custom_limits(self):
        """Test guard creation with custom limits."""
        limits = TeamLimits(max_concurrent=3, rate_limit=10)
        guard = TeamGuard("team-beta", limits)
        assert guard.team_id == "team-beta"
        assert guard.limits.max_concurrent == 3
        assert guard.limits.rate_limit == 10

    def test_empty_team_id_raises(self):
        """Test that empty team_id raises ValueError."""
        with pytest.raises(ValueError, match="team_id must be a non-empty string"):
            TeamGuard("")

    def test_whitespace_team_id_stripped(self):
        """Test that whitespace in team_id is stripped."""
        guard = TeamGuard("  team-gamma  ")
        assert guard.team_id == "team-gamma"


class TestAcquireNormal:
    """Tests for normal acquire operations."""

    def test_acquire_single_operation(self):
        """Test acquiring a single operation succeeds."""
        guard = TeamGuard("team-alpha", TeamLimits(max_concurrent=1, rate_limit=1))
        with guard.acquire("deploy") as (allowed, op):
            assert allowed is True
            assert op is not None
            assert op.team_id == "team-alpha"
            assert op.operation_type == "deploy"

    def test_active_count_after_acquire(self):
        """Test active count increases after acquire."""
        guard = TeamGuard("team-alpha", TeamLimits(max_concurrent=5, rate_limit=10))
        with guard.acquire("build") as (allowed, _):
            assert allowed is True
            assert guard.get_active_count() == 1

    def test_operation_released_on_exit(self):
        """Test that operation is cleaned up after context exit."""
        guard = TeamGuard("team-alpha", TeamLimits(max_concurrent=1, rate_limit=1))
        with guard.acquire("deploy") as (allowed, _):
            pass
        assert guard.get_active_count() == 0

    def test_metadata_preserved(self):
        """Test that metadata is passed through correctly."""
        meta = {"key": "value", "count": 42}
        with create_team_guard("team-x").acquire("test", metadata=meta) as (allowed, op):
            assert allowed is True
            assert op.metadata["key"] == "value"
            assert op.metadata["count"] == 42


class TestConcurrencyLimit:
    """Tests for concurrency limit enforcement."""

    def test_respects_concurrency_limit(self):
        """Test that concurrency limit is enforced."""
        limits = TeamLimits(max_concurrent=2, rate_limit=10)
        guard = TeamGuard("team-alpha", limits)

        # Should allow exactly 2 concurrent operations
        acquisitions = []
        for i in range(3):
            ctx = guard.acquire(f"op-{i}")
            acquisitions.append(ctx)
            _, op = ctx.__enter__()
            if i < 2:
                assert op is not None
            else:
                assert op is None

        for ctx in acquisitions:
            ctx.__exit__(None, None, None)

        assert guard.get_active_count() == 0

    def test_can_acquire_after_release(self):
        """Test that new operations can be acquired after old ones complete."""
        limits = TeamLimits(max_concurrent=1, rate_limit=10)
        guard = TeamGuard("team-alpha", limits)

        with guard.acquire("deploy") as (first_allowed, first_op):
            assert first_allowed is True

        # Now acquire again
        with guard.acquire("build") as (second_allowed, second_op):
            assert second_allowed is True
            assert second_op.operation_id != first_op.operation_id

    def test_get_active_operations_returns_correct_list(self):
        """Test getting list of active operations."""
        limits = TeamLimits(max_concurrent=5, rate_limit=20)
        guard = TeamGuard("team-alpha", limits)

        with guard.acquire("deploy") as (_, op1), guard.acquire("test") as (_, op2):
            active = guard.get_active_operations()
            assert len(active) == 2
            active_ids = {op.operation_id for op in active}
            assert op1.operation_id in active_ids
            assert op2.operation_id in active_ids


class TestRateLimit:
    """Tests for rate limit enforcement."""

    def test_respects_rate_limit(self):
        """Test that rate limit is enforced."""
        limits = TeamLimits(max_concurrent=10, rate_limit=2, rate_window=60.0)
        guard = TeamGuard("team-alpha", limits)

        # First two should succeed
        with guard.acquire("deploy") as (first_allowed, _):
            assert first_allowed is True

        with guard.acquire("build") as (second_allowed, _):
            assert second_allowed is True

        # Third should fail due to rate limit
        with guard.acquire("test") as (third_allowed, third_op):
            assert third_allowed is False
            assert third_op is None

    def test_rate_limit_resets_after_window(self):
        """Test that rate limit resets after window expires."""
        limits = TeamLimits(max_concurrent=10, rate_limit=2, rate_window=0.2)
        guard = TeamGuard("team-alpha", limits)

        # Use up rate limit
        with guard.acquire("deploy") as (first, _):
            assert first is True
        with guard.acquire("build") as (second, _):
            assert second is True

        # Should be blocked
        with guard.acquire("test") as (blocked, _):
            assert blocked is False

        # Wait for window to expire
        time.sleep(0.25)

        # Should be allowed again
        with guard.acquire("test") as (allowed, op):
            assert allowed is True
            assert op is not None

    def test_rate_limit_status(self):
        """Test rate limit status reporting."""
        limits = TeamLimits(max_concurrent=10, rate_limit=5, rate_window=60.0)
        guard = TeamGuard("team-alpha", limits)

        # Initially should show full capacity
        status = guard.get_rate_limit_status()
        assert status["used"] == 0
        assert status["remaining"] == 5
        assert status["limit"] == 5

        # After one acquisition and exit, rate limit should be updated
        with guard.acquire("deploy"):
            pass
        status = guard.get_rate_limit_status()
        assert status["used"] == 1
        assert status["remaining"] == 4


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_acquire_empty_operation_type_raises(self):
        """Test that empty operation_type raises ValueError."""
        guard = TeamGuard("team-alpha")
        with pytest.raises(ValueError, match="operation_type must be a non-empty string"):
            with guard.acquire("") as result:
                pass

    def test_force_release_existing_operation(self):
        """Test force_release successfully releases an existing operation."""
        limits = TeamLimits(max_concurrent=1, rate_limit=1)
        guard = TeamGuard("team-alpha", limits)

        with guard.acquire("deploy") as (_, op):
            op_id = op.operation_id
            released = guard.force_release(op_id)
            assert released is True
            assert guard.get_active_count() == 0

    def test_force_release_nonexistent_operation(self):
        """Test force_release returns False for nonexistent operation."""
        guard = TeamGuard("team-alpha")
        released = guard.force_release("nonexistent-op-id")
        assert released is False

    def test_reset_clears_all_state(self):
        """Test that reset clears all operations and counters."""
        limits = TeamLimits(max_concurrent=5, rate_limit=10)
        guard = TeamGuard("team-alpha", limits)

        with guard.acquire("deploy"), guard.acquire("build"):
            assert guard.get_active_count() == 2
            guard.reset()
            # Note: operations may still be active inside the context managers,
            # but counter is reset
        assert guard._operation_counter == 0

    def test_blocking_acquire_times_out(self):
        """Test that blocking acquire times out when limits exceeded."""
        limits = TeamLimits(max_concurrent=1, rate_limit=10)
        guard = TeamGuard("team-alpha", limits)

        # Hold one operation
        ctx = guard.acquire("deploy")
        allowed, op = ctx.__enter__()
        assert allowed is True

        # Try to block-acquire another with short timeout
        with guard.acquire("build", blocking=True, timeout=0.1) as (blocked_allowed, blocked_op):
            assert blocked_allowed is False
            assert blocked_op is None

        ctx.__exit__(None, None, None)
        assert guard.get_active_count() == 0

    def test_non_blocking_return_false_immediately(self):
        """Test that non-blocking acquire returns False immediately when limited."""
        limits = TeamLimits(max_concurrent=1, rate_limit=10)
        guard = TeamGuard("team-alpha", limits)

        # Hold one operation, filling the concurrency limit
        with guard.acquire("deploy") as (first_allowed, _):
            assert first_allowed is True

            # Now try to acquire another non-blocking - should fail
            with guard.acquire("build", blocking=False) as (second_allowed, second_op):
                assert second_allowed is False
                assert second_op is None


class TestFactoryFunction:
    """Tests for the create_team_guard factory function."""

    def test_create_without_args(self):
        """Test factory with defaults."""
        guard = create_team_guard("team-alpha")
        assert guard.team_id == "team-alpha"
        assert isinstance(guard.limits, TeamLimits)

    def test_create_with_kwargs(self):
        """Test factory with custom limits."""
        guard = create_team_guard("team-beta", max_concurrent=3, rate_limit=8)
        assert guard.team_id == "team-beta"
        assert guard.limits.max_concurrent == 3
        assert guard.limits.rate_limit == 8


class TestThreadSafety:
    """Tests for thread safety of TeamGuard."""

    def test_concurrent_acquisitions(self):
        """Test that concurrent acquisitions are handled safely."""
        limits = TeamLimits(max_concurrent=5, rate_limit=20)
        guard = TeamGuard("team-thread-safe", limits)

        results = []
        start_event = threading.Event()

        def worker(worker_id: int) -> None:
            # Wait for all threads to be ready
            start_event.wait()
            # Use non-blocking to test the limit without waiting
            with guard.acquire("task", blocking=False) as (allowed, op):
                results.append({
                    "id": worker_id,
                    "allowed": allowed,
                    "has_op": op is not None,
                    "active_count": guard.get_active_count(),
                })
                # Small delay to ensure concurrent execution
                time.sleep(0.01)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()

        # Start all threads simultaneously
        start_event.set()

        for t in threads:
            t.join()

        # Should have exactly 5 successful acquisitions (matching max_concurrent)
        successful = [r for r in results if r["allowed"]]
        rejected = [r for r in results if not r["allowed"]]
        assert len(successful) == 5
        assert len(rejected) == 5

    def test_blocking_acquire_respects_concurrency(self):
        """Test that blocking acquire properly queues and respects limits."""
        limits = TeamLimits(max_concurrent=2, rate_limit=10)
        guard = TeamGuard("team-blocking", limits)

        completion_order = []
        holders_started = threading.Event()
        release_event = threading.Event()
        holders_done = threading.Event()

        def holder(holder_id: int):
            with guard.acquire("hold") as (allowed, op):
                assert allowed is True
                holders_started.set()  # Signal that holder is active
                release_event.wait()   # Wait for release signal
            holders_done.set()
            completion_order.append(f"holder-{holder_id}")

        def waiter(waiter_id: int):
            holders_started.wait()  # Wait for holders to be active
            with guard.acquire("wait", blocking=True, timeout=2.0) as (allowed, op):
                if allowed:
                    completion_order.append(f"waiter-{waiter_id}")
                else:
                    completion_order.append(f"waiter-{waiter_id}-timeout")

        threads = [
            threading.Thread(target=holder, args=(0,)),
            threading.Thread(target=holder, args=(1,)),
            threading.Thread(target=waiter, args=(0,)),
            threading.Thread(target=waiter, args=(1,)),
        ]
        for t in threads:
            t.start()

        # Wait for holders to start
        holders_started.wait(timeout=2.0)
        # Verify holders are active
        assert guard.get_active_count() == 2
        # Release holders
        release_event.set()

        for t in threads:
            t.join(timeout=3.0)

        # Both waiters should have succeeded after holders released
        assert len([c for c in completion_order if c.startswith("waiter") and not c.endswith("timeout")]) == 2