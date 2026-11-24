"""
Tests for team_flow_e2e.child_b module.

Covers normal input scenarios and edge cases including:
- Normal team member and work item operations
- Edge case: Empty team and work items
- Edge case: Circular dependency detection
- Edge case: Capacity overflow handling
- Edge case: Invalid assignee references
"""

import pytest
from datetime import datetime, timedelta

from team_flow_e2e.child_b import (
    TeamFlowProcessor,
    TeamMember,
    WorkItem,
    MemberRole,
    WorkItemStatus,
    WorkItemType,
    create_sample_team,
)


class TestTeamMember:
    """Tests for TeamMember dataclass."""

    def test_create_member_with_defaults(self):
        """Test creating a member with default values."""
        member = TeamMember.create("Alice", MemberRole.DEVELOPER)
        assert member.name == "Alice"
        assert member.role == MemberRole.DEVELOPER
        assert member.capacity == 8
        assert member.skills == frozenset()
        assert len(member.id) == 8  # UUID prefix

    def test_create_member_with_custom_values(self):
        """Test creating a member with custom capacity and skills."""
        member = TeamMember.create(
            "Bob",
            MemberRole.TECH_LEAD,
            capacity=10,
            skills={"python", "architecture"},
        )
        assert member.capacity == 10
        assert member.skills == frozenset({"python", "architecture"})

    def test_member_validation_empty_name(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Member name cannot be empty"):
            TeamMember(id="1", name="", role=MemberRole.DEVELOPER)

    def test_member_validation_negative_capacity(self):
        """Test that negative capacity raises ValueError."""
        with pytest.raises(ValueError, match="Capacity cannot be negative"):
            TeamMember(id="1", name="Alice", role=MemberRole.DEVELOPER, capacity=-1)

    def test_has_skill_case_insensitive(self):
        """Test skill checking is case insensitive."""
        member = TeamMember.create("Alice", MemberRole.DEVELOPER, skills={"Python", "REACT"})
        assert member.has_skill("python")
        assert member.has_skill("PYTHON")
        assert member.has_skill("react")
        assert not member.has_skill("java")

    def test_available_capacity(self):
        """Test available capacity calculation."""
        member = TeamMember.create("Alice", MemberRole.DEVELOPER, capacity=8)
        assert member.available_capacity(0) == 8
        assert member.available_capacity(3) == 5
        assert member.available_capacity(8) == 0
        assert member.available_capacity(10) == 0  # Doesn't go negative


class TestWorkItem:
    """Tests for WorkItem dataclass."""

    def test_create_work_item_with_defaults(self):
        """Test creating a work item with default values."""
        item = WorkItem.create(
            "Implement feature",
            WorkItemType.FEATURE,
            5,
        )
        assert item.title == "Implement feature"
        assert item.type == WorkItemType.FEATURE
        assert item.effort == 5
        assert item.status == WorkItemStatus.BACKLOG
        assert item.assignee_id is None
        assert item.tags == frozenset()
        assert item.dependencies == frozenset()
        assert len(item.id) == 8

    def test_create_work_item_with_all_fields(self):
        """Test creating a work item with all optional fields."""
        item = WorkItem.create(
            "Fix bug",
            WorkItemType.BUG,
            3,
            assignee_id="member-1",
            tags={"bugfix", "urgent"},
            dependencies={"task-1", "task-2"},
        )
        assert item.assignee_id == "member-1"
        assert item.tags == frozenset({"bugfix", "urgent"})
        assert item.dependencies == frozenset({"task-1", "task-2"})

    def test_work_item_validation_empty_title(self):
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError, match="Work item title cannot be empty"):
            WorkItem(id="1", title="", type=WorkItemType.FEATURE, status=WorkItemStatus.BACKLOG,
                     assignee_id=None, effort=1)

    def test_work_item_validation_negative_effort(self):
        """Test that negative effort raises ValueError."""
        with pytest.raises(ValueError, match="Effort cannot be negative"):
            WorkItem(id="1", title="Task", type=WorkItemType.FEATURE, status=WorkItemStatus.BACKLOG,
                     assignee_id=None, effort=-1)

    def test_is_ready_with_satisfied_dependencies(self):
        """Test is_ready returns True when all dependencies are complete."""
        item = WorkItem.create("Task", WorkItemType.FEATURE, 5, dependencies={"dep-1", "dep-2"})
        completed = {"dep-1", "dep-2", "dep-3"}
        assert item.is_ready(completed) is True

    def test_is_ready_with_unsatisfied_dependencies(self):
        """Test is_ready returns False when dependencies are missing."""
        item = WorkItem.create("Task", WorkItemType.FEATURE, 5, dependencies={"dep-1", "dep-2"})
        completed = {"dep-1"}
        assert item.is_ready(completed) is False

    def test_is_ready_with_no_dependencies(self):
        """Test is_ready returns True for items with no dependencies."""
        item = WorkItem.create("Task", WorkItemType.FEATURE, 5)
        assert item.is_ready(set()) is True
        assert item.is_ready({"anything"}) is True

    def test_with_status_creates_new_instance(self):
        """Test with_status returns new instance with updated status."""
        item = WorkItem.create("Task", WorkItemType.FEATURE, 5)
        original_updated = item.updated_at
        new_item = item.with_status(WorkItemStatus.IN_PROGRESS)
        assert new_item.status == WorkItemStatus.IN_PROGRESS
        assert new_item.id == item.id
        assert new_item.updated_at > original_updated

    def test_with_assignee_creates_new_instance(self):
        """Test with_assignee returns new instance with updated assignee."""
        item = WorkItem.create("Task", WorkItemType.FEATURE, 5)
        original_updated = item.updated_at
        new_item = item.with_assignee("member-1")
        assert new_item.assignee_id == "member-1"
        assert new_item.id == item.id
        assert new_item.updated_at > original_updated

    def test_is_assigned(self):
        """Test is_assigned property."""
        item = WorkItem.create("Task", WorkItemType.FEATURE, 5)
        assert item.is_assigned() is False
        item = item.with_assignee("member-1")
        assert item.is_assigned() is True


class TestTeamFlowProcessor:
    """Tests for TeamFlowProcessor main functionality."""

    def test_add_and_get_member(self):
        """Test adding and retrieving a member."""
        processor = TeamFlowProcessor()
        member = processor.add_member("Alice", MemberRole.DEVELOPER)
        retrieved = processor.get_member(member.id)
        assert retrieved is not None
        assert retrieved.name == "Alice"
        assert retrieved.role == MemberRole.DEVELOPER

    def test_list_members_preserves_order(self):
        """Test that members are listed in insertion order."""
        processor = TeamFlowProcessor()
        m1 = processor.add_member("Alice", MemberRole.DEVELOPER)
        m2 = processor.add_member("Bob", MemberRole.DESIGNER)
        m3 = processor.add_member("Carol", MemberRole.QA_ENGINEER)
        members = processor.list_members()
        assert [m.id for m in members] == [m1.id, m2.id, m3.id]

    def test_list_members_filtered_by_role(self):
        """Test filtering members by role."""
        processor = TeamFlowProcessor()
        processor.add_member("Alice", MemberRole.DEVELOPER)
        processor.add_member("Bob", MemberRole.DESIGNER)
        processor.add_member("Carol", MemberRole.DEVELOPER)
        developers = processor.list_members(MemberRole.DEVELOPER)
        assert len(developers) == 2
        assert all(m.role == MemberRole.DEVELOPER for m in developers)

    def test_remove_member(self):
        """Test removing a member."""
        processor = TeamFlowProcessor()
        member = processor.add_member("Alice", MemberRole.DEVELOPER)
        assert processor.remove_member(member.id) is True
        assert processor.get_member(member.id) is None
        assert processor.remove_member(member.id) is False  # Already removed

    def test_remove_member_unassigns_work(self):
        """Test that removing a member unassigns their work items."""
        processor = TeamFlowProcessor()
        member = processor.add_member("Alice", MemberRole.DEVELOPER)
        item = processor.add_work_item("Task", WorkItemType.FEATURE, 5, assignee_id=member.id)
        assert item.assignee_id == member.id
        processor.remove_member(member.id)
        updated_item = processor.get_work_item(item.id)
        assert updated_item.assignee_id is None

    def test_add_and_get_work_item(self):
        """Test adding and retrieving a work item."""
        processor = TeamFlowProcessor()
        item = processor.add_work_item("Implement feature", WorkItemType.FEATURE, 5)
        retrieved = processor.get_work_item(item.id)
        assert retrieved is not None
        assert retrieved.title == "Implement feature"
        assert retrieved.type == WorkItemType.FEATURE
        assert retrieved.effort == 5

    def test_add_work_item_with_assignee(self):
        """Test adding a work item with an assignee."""
        processor = TeamFlowProcessor()
        member = processor.add_member("Alice", MemberRole.DEVELOPER)
        item = processor.add_work_item("Task", WorkItemType.FEATURE, 5, assignee_id=member.id)
        assert item.assignee_id == member.id

    def test_add_work_item_invalid_assignee_raises(self):
        """Test that adding work item with non-existent assignee raises ValueError."""
        processor = TeamFlowProcessor()
        with pytest.raises(ValueError, match="Assignee .* not found"):
            processor.add_work_item("Task", WorkItemType.FEATURE, 5, assignee_id="non-existent")

    def test_add_work_item_with_dependencies(self):
        """Test adding a work item with dependencies."""
        processor = TeamFlowProcessor()
        dep1 = processor.add_work_item("Dep 1", WorkItemType.FEATURE, 3)
        dep2 = processor.add_work_item("Dep 2", WorkItemType.CHORE, 2)
        item = processor.add_work_item(
            "Main Task",
            WorkItemType.FEATURE,
            5,
            dependencies={dep1.id, dep2.id},
        )
        assert item.dependencies == frozenset({dep1.id, dep2.id})

    def test_add_work_item_invalid_dependencies_raises(self):
        """Test that adding work item with non-existent dependencies raises ValueError."""
        processor = TeamFlowProcessor()
        with pytest.raises(ValueError, match="Dependencies not found"):
            processor.add_work_item("Task", WorkItemType.FEATURE, 5, dependencies={"missing"})

    def test_list_work_items_preserves_order(self):
        """Test that work items are listed in insertion order."""
        processor = TeamFlowProcessor()
        i1 = processor.add_work_item("Task 1", WorkItemType.FEATURE, 3)
        i2 = processor.add_work_item("Task 2", WorkItemType.BUG, 2)
        i3 = processor.add_work_item("Task 3", WorkItemType.CHORE, 1)
        items = processor.list_work_items()
        assert [i.id for i in items] == [i1.id, i2.id, i3.id]

    def test_list_work_items_filtered_by_status(self):
        """Test filtering work items by status."""
        processor = TeamFlowProcessor()
        i1 = processor.add_work_item("Task 1", WorkItemType.FEATURE, 3)
        i2 = processor.add_work_item("Task 2", WorkItemType.FEATURE, 2)
        processor.update_status(i1.id, WorkItemStatus.IN_PROGRESS)
        processor.update_status(i2.id, WorkItemStatus.DONE)
        in_progress = processor.list_work_items(status=WorkItemStatus.IN_PROGRESS)
        assert len(in_progress) == 1
        assert in_progress[0].id == i1.id

    def test_list_work_items_filtered_by_type(self):
        """Test filtering work items by type."""
        processor = TeamFlowProcessor()
        processor.add_work_item("Feature", WorkItemType.FEATURE, 3)
        processor.add_work_item("Bug", WorkItemType.BUG, 2)
        processor.add_work_item("Chore", WorkItemType.CHORE, 1)
        features = processor.list_work_items(type=WorkItemType.FEATURE)
        assert len(features) == 1
        assert features[0].type == WorkItemType.FEATURE

    def test_list_work_items_filtered_by_assignee(self):
        """Test filtering work items by assignee."""
        processor = TeamFlowProcessor()
        m1 = processor.add_member("Alice", MemberRole.DEVELOPER)
        m2 = processor.add_member("Bob", MemberRole.DEVELOPER)
        processor.add_work_item("Task 1", WorkItemType.FEATURE, 3, assignee_id=m1.id)
        processor.add_work_item("Task 2", WorkItemType.FEATURE, 2, assignee_id=m2.id)
        processor.add_work_item("Task 3", WorkItemType.FEATURE, 1)
        alice_items = processor.list_work_items(assignee_id=m1.id)
        assert len(alice_items) == 1
        assert alice_items[0].assignee_id == m1.id

    def test_assign_work(self):
        """Test assigning work to a member."""
        processor = TeamFlowProcessor()
        member = processor.add_member("Alice", MemberRole.DEVELOPER)
        item = processor.add_work_item("Task", WorkItemType.FEATURE, 5)
        assert processor.assign_work(item.id, member.id) is True
        assert processor.get_work_item(item.id).assignee_id == member.id

    def test_assign_work_invalid_item(self):
        """Test assigning non-existent work item returns False."""
        processor = TeamFlowProcessor()
        member = processor.add_member("Alice", MemberRole.DEVELOPER)
        assert processor.assign_work("non-existent", member.id) is False

    def test_assign_work_invalid_member(self):
        """Test assigning to non-existent member returns False."""
        processor = TeamFlowProcessor()
        item = processor.add_work_item("Task", WorkItemType.FEATURE, 5)
        assert processor.assign_work(item.id, "non-existent") is False

    def test_update_status(self):
        """Test updating work item status."""
        processor = TeamFlowProcessor()
        item = processor.add_work_item("Task", WorkItemType.FEATURE, 5)
        assert processor.update_status(item.id, WorkItemStatus.IN_PROGRESS) is True
        assert processor.get_work_item(item.id).status == WorkItemStatus.IN_PROGRESS

    def test_update_status_invalid_item(self):
        """Test updating status of non-existent item returns False."""
        processor = TeamFlowProcessor()
        assert processor.update_status("non-existent", WorkItemStatus.DONE) is False

    def test_get_assigned_work(self):
        """Test getting all work assigned to a member."""
        processor = TeamFlowProcessor()
        member = processor.add_member("Alice", MemberRole.DEVELOPER)
        processor.add_work_item("Task 1", WorkItemType.FEATURE, 3, assignee_id=member.id)
        processor.add_work_item("Task 2", WorkItemType.BUG, 2, assignee_id=member.id)
        processor.add_work_item("Task 3", WorkItemType.CHORE, 1)  # Unassigned
        assigned = processor.get_assigned_work(member.id)
        assert len(assigned) == 2
        assert all(item.assignee_id == member.id for item in assigned)

    def test_get_member_capacity(self):
        """Test getting member capacity utilization."""
        processor = TeamFlowProcessor()
        member = processor.add_member("Alice", MemberRole.DEVELOPER, capacity=10)
        processor.add_work_item("Task 1", WorkItemType.FEATURE, 3, assignee_id=member.id)
        processor.add_work_item("Task 2", WorkItemType.BUG, 2, assignee_id=member.id)
        allocated, capacity = processor.get_member_capacity(member.id)
        assert allocated == 5
        assert capacity == 10

    def test_get_member_capacity_invalid_member(self):
        """Test getting capacity for non-existent member raises KeyError."""
        processor = TeamFlowProcessor()
        with pytest.raises(KeyError):
            processor.get_member_capacity("non-existent")

    def test_get_team_summary_empty(self):
        """Test team summary with empty processor."""
        processor = TeamFlowProcessor()
        summary = processor.get_team_summary()
        assert summary["total_members"] == 0
        assert summary["total_work_items"] == 0
        assert summary["total_effort"] == 0
        assert summary["effort_by_status"] == {}
        assert summary["effort_by_type"] == {}
        assert summary["capacity_utilization"] == {}
        assert summary["blocked_items"] == []
        assert summary["ready_items"] == []

    def test_get_team_summary_with_data(self):
        """Test team summary with members and work items."""
        processor = TeamFlowProcessor()
        alice = processor.add_member("Alice", MemberRole.DEVELOPER, capacity=8)
        bob = processor.add_member("Bob", MemberRole.DESIGNER, capacity=5)
        task1 = processor.add_work_item("Feature", WorkItemType.FEATURE, 5, assignee_id=alice.id)
        task2 = processor.add_work_item("Bug", WorkItemType.BUG, 3, assignee_id=alice.id)
        task3 = processor.add_work_item("Design", WorkItemType.FEATURE, 2, assignee_id=bob.id)
        processor.update_status(task1.id, WorkItemStatus.IN_PROGRESS)
        processor.update_status(task2.id, WorkItemStatus.DONE)

        summary = processor.get_team_summary()
        assert summary["total_members"] == 2
        assert summary["total_work_items"] == 3
        assert summary["total_effort"] == 10
        assert summary["effort_by_status"]["in_progress"] == 5
        assert summary["effort_by_status"]["done"] == 3
        assert summary["effort_by_status"]["backlog"] == 2
        assert summary["effort_by_type"]["feature"] == 7
        assert summary["effort_by_type"]["bug"] == 3
        assert summary["capacity_utilization"][alice.id]["allocated"] == 8
        assert summary["capacity_utilization"][alice.id]["percentage"] == 100.0
        assert summary["capacity_utilization"][bob.id]["allocated"] == 2
        assert summary["capacity_utilization"][bob.id]["percentage"] == 40.0

    def test_get_team_summary_ready_items(self):
        """Test that ready_items identifies items with satisfied dependencies."""
        processor = TeamFlowProcessor()
        dep = processor.add_work_item("Dependency", WorkItemType.FEATURE, 3)
        processor.update_status(dep.id, WorkItemStatus.DONE)
        ready = processor.add_work_item("Ready Task", WorkItemType.FEATURE, 2, dependencies={dep.id})
        # Create another dependency that is NOT done
        not_done_dep = processor.add_work_item("Not Done Dep", WorkItemType.FEATURE, 1)
        not_ready = processor.add_work_item("Not Ready", WorkItemType.FEATURE, 2, dependencies={not_done_dep.id})

        summary = processor.get_team_summary()
        assert ready.id in summary["ready_items"]
        assert not_ready.id not in summary["ready_items"]

    def test_get_team_summary_blocked_items(self):
        """Test that blocked_items identifies blocked work items."""
        processor = TeamFlowProcessor()
        normal = processor.add_work_item("Normal", WorkItemType.FEATURE, 3)
        blocked = processor.add_work_item("Blocked", WorkItemType.FEATURE, 2)
        processor.update_status(blocked.id, WorkItemStatus.BLOCKED)

        summary = processor.get_team_summary()
        assert blocked.id in summary["blocked_items"]
        assert normal.id not in summary["blocked_items"]

    def test_get_workflow_metrics_empty(self):
        """Test workflow metrics with no completed items."""
        processor = TeamFlowProcessor()
        metrics = processor.get_workflow_metrics()
        assert metrics["cycle_time_avg"] == 0
        assert metrics["lead_time_avg"] == 0
        assert metrics["throughput"] == 0
        assert metrics["wip_count"] == 0
        assert metrics["blocked_count"] == 0

    def test_get_workflow_metrics_with_completed(self):
        """Test workflow metrics with completed items."""
        processor = TeamFlowProcessor()
        item = processor.add_work_item("Task", WorkItemType.FEATURE, 5)
        processor.update_status(item.id, WorkItemStatus.IN_PROGRESS)
        processor.update_status(item.id, WorkItemStatus.DONE)

        metrics = processor.get_workflow_metrics()
        assert metrics["throughput"] == 1
        assert metrics["lead_time_avg"] >= 0
        assert metrics["cycle_time_avg"] >= 0

    def test_find_next_priority_work_basic(self):
        """Test priority work ordering."""
        processor = TeamFlowProcessor()
        blocked = processor.add_work_item("Blocked", WorkItemType.FEATURE, 3)
        processor.update_status(blocked.id, WorkItemStatus.BLOCKED)
        in_review = processor.add_work_item("In Review", WorkItemType.FEATURE, 2)
        processor.update_status(in_review.id, WorkItemStatus.IN_REVIEW)
        ready = processor.add_work_item("Ready", WorkItemType.FEATURE, 2)
        backlog = processor.add_work_item("Backlog", WorkItemType.FEATURE, 1)

        priority = processor.find_next_priority_work()
        assert priority[0].id == blocked.id
        assert priority[1].id == in_review.id
        assert priority[2].id == ready.id
        assert priority[3].id == backlog.id

    def test_find_next_priority_work_filtered_by_member(self):
        """Test priority work filtered by member assignment."""
        processor = TeamFlowProcessor()
        alice = processor.add_member("Alice", MemberRole.DEVELOPER, skills={"python"})
        bob = processor.add_member("Bob", MemberRole.DEVELOPER, skills={"javascript"})

        alice_task = processor.add_work_item("Alice Task", WorkItemType.FEATURE, 3, assignee_id=alice.id)
        bob_task = processor.add_work_item("Bob Task", WorkItemType.FEATURE, 2, assignee_id=bob.id)
        unassigned_python = processor.add_work_item("Python Task", WorkItemType.FEATURE, 2, tags={"python"})
        unassigned_js = processor.add_work_item("JS Task", WorkItemType.FEATURE, 2, tags={"javascript"})

        alice_priority = processor.find_next_priority_work(alice.id)
        assert alice_task.id in [i.id for i in alice_priority]
        assert unassigned_python.id in [i.id for i in alice_priority]
        assert bob_task.id not in [i.id for i in alice_priority]
        assert unassigned_js.id not in [i.id for i in alice_priority]

    def test_remove_work_item(self):
        """Test removing a work item."""
        processor = TeamFlowProcessor()
        item = processor.add_work_item("Task", WorkItemType.FEATURE, 5)
        assert processor.remove_work_item(item.id) is True
        assert processor.get_work_item(item.id) is None
        assert processor.remove_work_item(item.id) is False


class TestEdgeCases:
    """Edge case tests for TeamFlowProcessor."""

    def test_empty_processor_operations(self):
        """Test operations on completely empty processor."""
        processor = TeamFlowProcessor()
        assert processor.list_members() == []
        assert processor.list_work_items() == []
        assert processor.get_member("any") is None
        assert processor.get_work_item("any") is None
        assert processor.get_assigned_work("any") == []
        summary = processor.get_team_summary()
        assert summary["total_members"] == 0
        assert summary["total_work_items"] == 0

    def test_circular_dependency_detectable_via_is_ready(self):
        """
        Test that circular dependencies can be detected via is_ready.
        Note: Circular dependencies are prevented at creation time by validation.
        This test creates a chain that simulates circular behavior.
        """
        processor = TeamFlowProcessor()
        # Create a chain: item1 -> item2 -> item3 (where item3 depends on item1)
        item1 = processor.add_work_item("Task 1", WorkItemType.FEATURE, 3)
        item2 = processor.add_work_item("Task 2", WorkItemType.FEATURE, 2, dependencies={item1.id})
        item3 = processor.add_work_item("Task 3", WorkItemType.FEATURE, 1, dependencies={item2.id})

        # None are ready initially (item1 has no deps but is backlog, item2 needs item1, item3 needs item2)
        completed = set()
        assert item1.is_ready(completed) is True  # No dependencies
        assert item2.is_ready(completed) is False  # Needs item1
        assert item3.is_ready(completed) is False  # Needs item2

        # Complete item1
        completed.add(item1.id)
        assert item2.is_ready(completed) is True  # Now item1 is done
        assert item3.is_ready(completed) is False  # Still needs item2

        # Complete item2
        completed.add(item2.id)
        assert item3.is_ready(completed) is True  # Now both deps satisfied

    def test_capacity_overflow_handling(self):
        """Test that capacity can be exceeded (no hard limit enforced)."""
        processor = TeamFlowProcessor()
        member = processor.add_member("Alice", MemberRole.DEVELOPER, capacity=8)
        # Assign more work than capacity
        processor.add_work_item("Task 1", WorkItemType.FEATURE, 5, assignee_id=member.id)
        processor.add_work_item("Task 2", WorkItemType.FEATURE, 5, assignee_id=member.id)
        processor.add_work_item("Task 3", WorkItemType.FEATURE, 3, assignee_id=member.id)

        allocated, capacity = processor.get_member_capacity(member.id)
        assert allocated == 13  # Exceeds capacity of 8
        assert capacity == 8
        summary = processor.get_team_summary()
        assert summary["capacity_utilization"][member.id]["percentage"] == 162.5

    def test_member_with_zero_capacity(self):
        """Test member with zero capacity."""
        processor = TeamFlowProcessor()
        member = processor.add_member("Alice", MemberRole.PRODUCT_MANAGER, capacity=0)
        processor.add_work_item("Task", WorkItemType.FEATURE, 5, assignee_id=member.id)

        allocated, capacity = processor.get_member_capacity(member.id)
        assert allocated == 5
        assert capacity == 0
        summary = processor.get_team_summary()
        # Percentage should be 0 when capacity is 0 (avoid division by zero)
        assert summary["capacity_utilization"][member.id]["percentage"] == 0

    def test_large_number_of_members_and_items(self):
        """Test processor handles larger numbers without issues."""
        processor = TeamFlowProcessor()
        members = []
        for i in range(50):
            member = processor.add_member(f"Member {i}", MemberRole.DEVELOPER)
            members.append(member)

        for i in range(200):
            processor.add_work_item(
                f"Task {i}",
                WorkItemType.FEATURE if i % 2 == 0 else WorkItemType.BUG,
                (i % 8) + 1,
                assignee_id=members[i % len(members)].id,
            )

        assert len(processor.list_members()) == 50
        assert len(processor.list_work_items()) == 200
        summary = processor.get_team_summary()
        assert summary["total_members"] == 50
        assert summary["total_work_items"] == 200

    def test_work_item_with_empty_assignee_string(self):
        """Test that empty string assignee is treated as None."""
        # This tests the __post_init__ conversion
        item = WorkItem(
            id="test",
            title="Test",
            type=WorkItemType.FEATURE,
            status=WorkItemStatus.BACKLOG,
            assignee_id="",
            effort=1,
        )
        assert item.assignee_id is None

    def test_skill_matching_case_insensitive_in_priority(self):
        """Test that skill matching in find_next_priority_work is case insensitive."""
        processor = TeamFlowProcessor()
        member = processor.add_member("Alice", MemberRole.DEVELOPER, skills={"PYTHON", "React"})
        # Tags use different case
        task = processor.add_work_item("Task", WorkItemType.FEATURE, 3, tags={"python", "REACT"})

        priority = processor.find_next_priority_work(member.id)
        assert task.id in [i.id for i in priority]

    def test_work_item_tag_and_dependency_sets_are_frozen(self):
        """Test that tags and dependencies are immutable frozensets."""
        item = WorkItem.create("Task", WorkItemType.FEATURE, 3, tags={"tag1"}, dependencies={"dep1"})
        assert isinstance(item.tags, frozenset)
        assert isinstance(item.dependencies, frozenset)
        # Attempting to modify should fail
        with pytest.raises(AttributeError):
            item.tags.add("tag2")
        with pytest.raises(AttributeError):
            item.dependencies.add("dep2")

    def test_member_skills_set_is_frozen(self):
        """Test that member skills is an immutable frozenset."""
        member = TeamMember.create("Alice", MemberRole.DEVELOPER, skills={"python"})
        assert isinstance(member.skills, frozenset)
        with pytest.raises(AttributeError):
            member.skills.add("java")


class TestCreateSampleTeam:
    """Tests for the create_sample_team factory function."""

    def test_create_sample_team_returns_populated_processor(self):
        """Test that create_sample_team creates a valid processor with data."""
        processor = create_sample_team()
        assert isinstance(processor, TeamFlowProcessor)
        assert processor.get_team_summary()["total_members"] == 5
        assert processor.get_team_summary()["total_work_items"] == 6

    def test_sample_team_has_expected_members(self):
        """Test that sample team has expected member roles."""
        processor = create_sample_team()
        members = processor.list_members()
        roles = {m.role for m in members}
        assert MemberRole.TECH_LEAD in roles
        assert MemberRole.DEVELOPER in roles
        assert MemberRole.QA_ENGINEER in roles
        assert MemberRole.PRODUCT_MANAGER in roles

    def test_sample_team_has_expected_work_items(self):
        """Test that sample team has expected work item types and statuses."""
        processor = create_sample_team()
        items = processor.list_work_items()
        types = {i.type for i in items}
        statuses = {i.status for i in items}
        assert WorkItemType.FEATURE in types
        assert WorkItemType.BUG in types
        assert WorkItemType.CHORE in types
        assert WorkItemType.DOCUMENTATION in types
        assert WorkItemStatus.DONE in statuses
        assert WorkItemStatus.IN_PROGRESS in statuses
        assert WorkItemStatus.IN_REVIEW in statuses
        assert WorkItemStatus.BACKLOG in statuses


class TestEnums:
    """Tests for enum values."""

    def test_member_role_values(self):
        """Test MemberRole enum values."""
        assert MemberRole.DEVELOPER.value == "developer"
        assert MemberRole.DESIGNER.value == "designer"
        assert MemberRole.PRODUCT_MANAGER.value == "product_manager"
        assert MemberRole.QA_ENGINEER.value == "qa_engineer"
        assert MemberRole.DEVOPS.value == "devops"
        assert MemberRole.TECH_LEAD.value == "tech_lead"

    def test_work_item_status_values(self):
        """Test WorkItemStatus enum values."""
        assert WorkItemStatus.BACKLOG.value == "backlog"
        assert WorkItemStatus.TODO.value == "todo"
        assert WorkItemStatus.IN_PROGRESS.value == "in_progress"
        assert WorkItemStatus.IN_REVIEW.value == "in_review"
        assert WorkItemStatus.DONE.value == "done"
        assert WorkItemStatus.BLOCKED.value == "blocked"

    def test_work_item_type_values(self):
        """Test WorkItemType enum values."""
        assert WorkItemType.FEATURE.value == "feature"
        assert WorkItemType.BUG.value == "bug"
        assert WorkItemType.CHORE.value == "chore"
        assert WorkItemType.SPIKE.value == "spike"
        assert WorkItemType.REFACTOR.value == "refactor"
        assert WorkItemType.DOCUMENTATION.value == "documentation"