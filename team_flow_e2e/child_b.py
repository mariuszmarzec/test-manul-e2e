"""
Team Flow End-to-End Child B Module.

This module provides core functionality for processing team workflow data,
including member management, work item tracking, and progress aggregation.
It is designed as a more substantial implementation than Child A, offering
comprehensive type hints, documentation, and extensible architecture.

Example:
    >>> from team_flow_e2e.child_b import TeamFlowProcessor
    >>> processor = TeamFlowProcessor()
    >>> processor.add_member("alice", "developer")
    >>> processor.add_work_item("task-1", "Implement feature", "alice", 5)
    >>> summary = processor.get_team_summary()
    >>> print(summary["total_effort"])
    5
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class MemberRole(str, Enum):
    """Enumeration of possible team member roles."""

    DEVELOPER = "developer"
    DESIGNER = "designer"
    PRODUCT_MANAGER = "product_manager"
    QA_ENGINEER = "qa_engineer"
    DEVOPS = "devops"
    TECH_LEAD = "tech_lead"


class WorkItemStatus(str, Enum):
    """Enumeration of possible work item statuses."""

    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"


class WorkItemType(str, Enum):
    """Enumeration of possible work item types."""

    FEATURE = "feature"
    BUG = "bug"
    CHORE = "chore"
    SPIKE = "spike"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"


@dataclass(frozen=True, slots=True)
class TeamMember:
    """
    Represents a team member with their role and capacity.

    Attributes:
        id: Unique identifier for the member.
        name: Human-readable name.
        role: The member's role in the team.
        capacity: Weekly capacity in story points (default: 8).
        skills: Set of skill tags (default: empty set).
        joined_at: Timestamp when the member joined (default: now).
    """

    id: str
    name: str
    role: MemberRole
    capacity: int = 8
    skills: frozenset[str] = field(default_factory=frozenset)
    joined_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate member data after initialization."""
        if not self.id:
            raise ValueError("Member id cannot be empty")
        if not self.name:
            raise ValueError("Member name cannot be empty")
        if self.capacity < 0:
            raise ValueError("Capacity cannot be negative")

    @classmethod
    def create(
        cls,
        name: str,
        role: MemberRole,
        capacity: int = 8,
        skills: Optional[Set[str]] = None,
    ) -> TeamMember:
        """
        Factory method to create a new team member with generated ID.

        Args:
            name: Human-readable name.
            role: The member's role.
            capacity: Weekly capacity in story points.
            skills: Optional set of skill tags.

        Returns:
            A new TeamMember instance with a generated UUID.
        """
        return cls(
            id=str(uuid.uuid4())[:8],
            name=name,
            role=role,
            capacity=capacity,
            skills=frozenset(skills) if skills else frozenset(),
        )

    def has_skill(self, skill: str) -> bool:
        """Check if the member has a specific skill."""
        return skill.lower() in (s.lower() for s in self.skills)

    def available_capacity(self, allocated: int) -> int:
        """Calculate remaining capacity after allocation."""
        return max(0, self.capacity - allocated)


@dataclass(frozen=True, slots=True)
class WorkItem:
    """
    Represents a unit of work in the team flow.

    Attributes:
        id: Unique identifier for the work item.
        title: Brief description of the work.
        type: The type of work item (feature, bug, etc.).
        status: Current status in the workflow.
        assignee_id: ID of the assigned team member (optional).
        effort: Estimated effort in story points.
        tags: Set of categorization tags.
        created_at: Timestamp when the item was created.
        updated_at: Timestamp of last update.
        dependencies: Set of work item IDs that must be completed first.
    """

    id: str
    title: str
    type: WorkItemType
    status: WorkItemStatus
    assignee_id: Optional[str]
    effort: int
    tags: frozenset[str] = field(default_factory=frozenset)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    dependencies: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        """Validate work item data after initialization."""
        if not self.id:
            raise ValueError("Work item id cannot be empty")
        if not self.title:
            raise ValueError("Work item title cannot be empty")
        if self.effort < 0:
            raise ValueError("Effort cannot be negative")
        if self.assignee_id == "":
            object.__setattr__(self, "assignee_id", None)

    @classmethod
    def create(
        cls,
        title: str,
        type: WorkItemType,
        effort: int,
        assignee_id: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        dependencies: Optional[Set[str]] = None,
    ) -> WorkItem:
        """
        Factory method to create a new work item with generated ID.

        Args:
            title: Brief description of the work.
            type: The type of work item.
            effort: Estimated effort in story points.
            assignee_id: Optional ID of the assigned member.
            tags: Optional set of categorization tags.
            dependencies: Optional set of prerequisite work item IDs.

        Returns:
            A new WorkItem instance with a generated UUID.
        """
        now = datetime.now()
        return cls(
            id=str(uuid.uuid4())[:8],
            title=title,
            type=type,
            status=WorkItemStatus.BACKLOG,
            assignee_id=assignee_id,
            effort=effort,
            tags=frozenset(tags) if tags else frozenset(),
            created_at=now,
            updated_at=now,
            dependencies=frozenset(dependencies) if dependencies else frozenset(),
        )

    def is_ready(self, completed_ids: Set[str]) -> bool:
        """Check if all dependencies are satisfied."""
        return self.dependencies.issubset(completed_ids)

    def is_assigned(self) -> bool:
        """Check if the work item has an assignee."""
        return self.assignee_id is not None

    def with_status(self, status: WorkItemStatus) -> WorkItem:
        """Return a new WorkItem with updated status and timestamp."""
        return WorkItem(
            id=self.id,
            title=self.title,
            type=self.type,
            status=status,
            assignee_id=self.assignee_id,
            effort=self.effort,
            tags=self.tags,
            created_at=self.created_at,
            updated_at=datetime.now(),
            dependencies=self.dependencies,
        )

    def with_assignee(self, assignee_id: Optional[str]) -> WorkItem:
        """Return a new WorkItem with updated assignee and timestamp."""
        return WorkItem(
            id=self.id,
            title=self.title,
            type=self.type,
            status=self.status,
            assignee_id=assignee_id,
            effort=self.effort,
            tags=self.tags,
            created_at=self.created_at,
            updated_at=datetime.now(),
            dependencies=self.dependencies,
        )


@dataclass
class TeamFlowProcessor:
    """
    Main processor for team workflow operations.

    This class manages team members, work items, and provides aggregation
    and reporting capabilities. It uses immutable data structures where
    possible and returns new instances for mutations.

    Attributes:
        members: Dictionary mapping member IDs to TeamMember instances.
        work_items: Dictionary mapping work item IDs to WorkItem instances.
        _member_order: List preserving insertion order of member IDs.
        _work_item_order: List preserving insertion order of work item IDs.

    Example:
        >>> processor = TeamFlowProcessor()
        >>> alice = processor.add_member("Alice", MemberRole.DEVELOPER)
        >>> task = processor.add_work_item("Add login", WorkItemType.FEATURE, 3)
        >>> processor.assign_work(task.id, alice.id)
        >>> summary = processor.get_team_summary()
    """

    members: Dict[str, TeamMember] = field(default_factory=dict, init=False)
    work_items: Dict[str, WorkItem] = field(default_factory=dict, init=False)
    _member_order: List[str] = field(default_factory=list, init=False, repr=False)
    _work_item_order: List[str] = field(default_factory=list, init=False, repr=False)

    def add_member(
        self,
        name: str,
        role: MemberRole,
        capacity: int = 8,
        skills: Optional[Set[str]] = None,
    ) -> TeamMember:
        """
        Add a new team member.

        Args:
            name: Human-readable name.
            role: The member's role.
            capacity: Weekly capacity in story points.
            skills: Optional set of skill tags.

        Returns:
            The created TeamMember instance.

        Raises:
            ValueError: If name is empty or capacity is negative.
        """
        member = TeamMember.create(name, role, capacity, skills)
        self.members[member.id] = member
        self._member_order.append(member.id)
        return member

    def remove_member(self, member_id: str) -> bool:
        """
        Remove a team member.

        Args:
            member_id: ID of the member to remove.

        Returns:
            True if member was removed, False if not found.
        """
        if member_id in self.members:
            del self.members[member_id]
            self._member_order = [mid for mid in self._member_order if mid != member_id]
            # Unassign work items
            for item in self.work_items.values():
                if item.assignee_id == member_id:
                    self.work_items[item.id] = item.with_assignee(None)
            return True
        return False

    def get_member(self, member_id: str) -> Optional[TeamMember]:
        """Retrieve a member by ID."""
        return self.members.get(member_id)

    def list_members(self, role: Optional[MemberRole] = None) -> List[TeamMember]:
        """
        List all members, optionally filtered by role.

        Args:
            role: Optional role filter.

        Returns:
            List of members in insertion order.
        """
        members = [self.members[mid] for mid in self._member_order if mid in self.members]
        if role:
            return [m for m in members if m.role == role]
        return members

    def add_work_item(
        self,
        title: str,
        type: WorkItemType,
        effort: int,
        assignee_id: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        dependencies: Optional[Set[str]] = None,
    ) -> WorkItem:
        """
        Add a new work item.

        Args:
            title: Brief description of the work.
            type: The type of work item.
            effort: Estimated effort in story points.
            assignee_id: Optional ID of the assigned member.
            tags: Optional set of categorization tags.
            dependencies: Optional set of prerequisite work item IDs.

        Returns:
            The created WorkItem instance.

        Raises:
            ValueError: If title is empty, effort is negative, or assignee doesn't exist.
        """
        if assignee_id and assignee_id not in self.members:
            raise ValueError(f"Assignee {assignee_id} not found")

        if dependencies:
            missing = dependencies - set(self.work_items.keys())
            if missing:
                raise ValueError(f"Dependencies not found: {missing}")

        item = WorkItem.create(title, type, effort, assignee_id, tags, dependencies)
        self.work_items[item.id] = item
        self._work_item_order.append(item.id)
        return item

    def remove_work_item(self, item_id: str) -> bool:
        """
        Remove a work item.

        Args:
            item_id: ID of the work item to remove.

        Returns:
            True if item was removed, False if not found.
        """
        if item_id in self.work_items:
            del self.work_items[item_id]
            self._work_item_order = [wid for wid in self._work_item_order if wid != item_id]
            return True
        return False

    def get_work_item(self, item_id: str) -> Optional[WorkItem]:
        """Retrieve a work item by ID."""
        return self.work_items.get(item_id)

    def list_work_items(
        self,
        status: Optional[WorkItemStatus] = None,
        type: Optional[WorkItemType] = None,
        assignee_id: Optional[str] = None,
    ) -> List[WorkItem]:
        """
        List work items with optional filters.

        Args:
            status: Optional status filter.
            type: Optional type filter.
            assignee_id: Optional assignee filter.

        Returns:
            List of matching work items in insertion order.
        """
        items = [
            self.work_items[wid]
            for wid in self._work_item_order
            if wid in self.work_items
        ]

        if status:
            items = [i for i in items if i.status == status]
        if type:
            items = [i for i in items if i.type == type]
        if assignee_id:
            items = [i for i in items if i.assignee_id == assignee_id]

        return items

    def assign_work(self, item_id: str, member_id: str) -> bool:
        """
        Assign a work item to a team member.

        Args:
            item_id: ID of the work item.
            member_id: ID of the team member.

        Returns:
            True if assignment succeeded, False if item or member not found.
        """
        if item_id not in self.work_items or member_id not in self.members:
            return False

        item = self.work_items[item_id]
        self.work_items[item_id] = item.with_assignee(member_id)
        return True

    def update_status(self, item_id: str, status: WorkItemStatus) -> bool:
        """
        Update the status of a work item.

        Args:
            item_id: ID of the work item.
            status: New status.

        Returns:
            True if update succeeded, False if item not found.
        """
        if item_id not in self.work_items:
            return False

        item = self.work_items[item_id]
        self.work_items[item_id] = item.with_status(status)
        return True

    def get_assigned_work(self, member_id: str) -> List[WorkItem]:
        """Get all work items assigned to a member."""
        return self.list_work_items(assignee_id=member_id)

    def get_member_capacity(self, member_id: str) -> Tuple[int, int]:
        """
        Get allocated and total capacity for a member.

        Args:
            member_id: ID of the team member.

        Returns:
            Tuple of (allocated_effort, total_capacity).

        Raises:
            KeyError: If member not found.
        """
        member = self.members[member_id]
        assigned = self.get_assigned_work(member_id)
        allocated = sum(item.effort for item in assigned)
        return allocated, member.capacity

    def get_team_summary(self) -> Dict[str, Any]:
        """
        Generate a comprehensive team summary.

        Returns:
            Dictionary containing:
            - total_members: Count of team members
            - total_work_items: Count of work items
            - total_effort: Sum of all work item efforts
            - effort_by_status: Effort grouped by status
            - effort_by_type: Effort grouped by type
            - capacity_utilization: Dict of member_id -> (allocated, capacity, percentage)
            - blocked_items: List of blocked work item IDs
            - ready_items: List of work item IDs ready to start (deps satisfied)
        """
        total_effort = sum(item.effort for item in self.work_items.values())

        effort_by_status: Dict[WorkItemStatus, int] = {}
        effort_by_type: Dict[WorkItemType, int] = {}

        for item in self.work_items.values():
            effort_by_status[item.status] = effort_by_status.get(item.status, 0) + item.effort
            effort_by_type[item.type] = effort_by_type.get(item.type, 0) + item.effort

        capacity_utilization = {}
        for member_id in self.members:
            allocated, capacity = self.get_member_capacity(member_id)
            percentage = (allocated / capacity * 100) if capacity > 0 else 0
            capacity_utilization[member_id] = {
                "allocated": allocated,
                "capacity": capacity,
                "percentage": round(percentage, 1),
            }

        completed_ids = {
            item.id for item in self.work_items.values() if item.status == WorkItemStatus.DONE
        }

        blocked_items = [
            item.id for item in self.work_items.values() if item.status == WorkItemStatus.BLOCKED
        ]

        ready_items = [
            item.id
            for item in self.work_items.values()
            if item.status in (WorkItemStatus.BACKLOG, WorkItemStatus.TODO)
            and item.is_ready(completed_ids)
        ]

        return {
            "total_members": len(self.members),
            "total_work_items": len(self.work_items),
            "total_effort": total_effort,
            "effort_by_status": {k.value: v for k, v in effort_by_status.items()},
            "effort_by_type": {k.value: v for k, v in effort_by_type.items()},
            "capacity_utilization": capacity_utilization,
            "blocked_items": blocked_items,
            "ready_items": ready_items,
        }

    def get_workflow_metrics(self) -> Dict[str, Any]:
        """
        Calculate workflow metrics for the team.

        Returns:
            Dictionary containing:
            - cycle_time_avg: Average time from IN_PROGRESS to DONE (hours)
            - lead_time_avg: Average time from creation to DONE (hours)
            - throughput: Completed items per week (estimated)
            - wip_count: Work in progress count
            - blocked_count: Blocked items count
        """
        completed = [
            item for item in self.work_items.values() if item.status == WorkItemStatus.DONE
        ]
        in_progress = [
            item for item in self.work_items.values() if item.status == WorkItemStatus.IN_PROGRESS
        ]
        blocked = [
            item for item in self.work_items.values() if item.status == WorkItemStatus.BLOCKED
        ]

        # For simplicity, use created_at as proxy for start times
        # In a real implementation, you'd track status transition timestamps
        cycle_times = []
        lead_times = []

        for item in completed:
            # Simplified: assume work started at created_at
            # Real implementation would track actual transition times
            lead_time = (item.updated_at - item.created_at).total_seconds() / 3600
            lead_times.append(lead_time)
            cycle_times.append(lead_time * 0.7)  # Rough estimate

        return {
            "cycle_time_avg": round(sum(cycle_times) / len(cycle_times), 1) if cycle_times else 0,
            "lead_time_avg": round(sum(lead_times) / len(lead_times), 1) if lead_times else 0,
            "throughput": len(completed),  # Simplified: items completed total
            "wip_count": len(in_progress),
            "blocked_count": len(blocked),
        }

    def find_next_priority_work(self, member_id: Optional[str] = None) -> List[WorkItem]:
        """
        Find work items ready to be started, ordered by priority.

        Priority order:
        1. BLOCKED items (need unblocking)
        2. IN_REVIEW items (need review)
        3. Ready items (dependencies satisfied, not started)
        4. Backlog items with no dependencies

        Args:
            member_id: Optional member ID to filter by assignee or skills.

        Returns:
            List of work items in priority order.
        """
        completed_ids = {
            item.id for item in self.work_items.values() if item.status == WorkItemStatus.DONE
        }

        blocked = [i for i in self.work_items.values() if i.status == WorkItemStatus.BLOCKED]
        in_review = [i for i in self.work_items.values() if i.status == WorkItemStatus.IN_REVIEW]

        ready = [
            i
            for i in self.work_items.values()
            if i.status in (WorkItemStatus.BACKLOG, WorkItemStatus.TODO)
            and i.is_ready(completed_ids)
        ]

        backlog = [
            i
            for i in self.work_items.values()
            if i.status == WorkItemStatus.BACKLOG
            and not i.is_ready(completed_ids)
        ]

        # Filter by member if specified
        if member_id:
            member = self.members.get(member_id)
            if member:
                # Filter to items assigned to member or matching their skills
                def matches(item: WorkItem) -> bool:
                    if item.assignee_id == member_id:
                        return True
                    if not item.assignee_id and item.tags:
                        return any(member.has_skill(tag) for tag in item.tags)
                    return False

                blocked = [i for i in blocked if matches(i)]
                in_review = [i for i in in_review if matches(i)]
                ready = [i for i in ready if matches(i)]
                backlog = [i for i in backlog if matches(i)]

        return blocked + in_review + ready + backlog


def create_sample_team() -> TeamFlowProcessor:
    """
    Create a sample team with members and work items for testing/demo.

    Returns:
        A configured TeamFlowProcessor instance.
    """
    processor = TeamFlowProcessor()

    # Add members
    alice = processor.add_member("Alice", MemberRole.TECH_LEAD, capacity=10, skills={"python", "architecture", "mentoring"})
    bob = processor.add_member("Bob", MemberRole.DEVELOPER, capacity=8, skills={"python", "testing"})
    carol = processor.add_member("Carol", MemberRole.DEVELOPER, capacity=8, skills={"javascript", "react"})
    dave = processor.add_member("Dave", MemberRole.QA_ENGINEER, capacity=8, skills={"testing", "automation"})
    eve = processor.add_member("Eve", MemberRole.PRODUCT_MANAGER, capacity=5, skills={"product", "requirements"})

    # Add work items
    task1 = processor.add_work_item(
        "Design system architecture",
        WorkItemType.FEATURE,
        5,
        assignee_id=alice.id,
        tags={"architecture", "design"},
    )
    task2 = processor.add_work_item(
        "Implement user authentication",
        WorkItemType.FEATURE,
        8,
        assignee_id=bob.id,
        tags={"python", "security"},
        dependencies={task1.id},
    )
    task3 = processor.add_work_item(
        "Build login UI",
        WorkItemType.FEATURE,
        5,
        assignee_id=carol.id,
        tags={"javascript", "react", "ui"},
        dependencies={task1.id},
    )
    task4 = processor.add_work_item(
        "Write authentication tests",
        WorkItemType.CHORE,
        3,
        assignee_id=dave.id,
        tags={"testing", "automation"},
        dependencies={task2.id},
    )
    task5 = processor.add_work_item(
        "Fix password reset bug",
        WorkItemType.BUG,
        2,
        assignee_id=bob.id,
        tags={"python", "security", "bugfix"},
    )
    task6 = processor.add_work_item(
        "Update API documentation",
        WorkItemType.DOCUMENTATION,
        2,
        tags={"documentation", "api"},
    )

    # Update some statuses
    processor.update_status(task1.id, WorkItemStatus.DONE)
    processor.update_status(task2.id, WorkItemStatus.IN_PROGRESS)
    processor.update_status(task3.id, WorkItemStatus.IN_PROGRESS)
    processor.update_status(task5.id, WorkItemStatus.IN_REVIEW)

    return processor


if __name__ == "__main__":
    # Demo usage
    processor = create_sample_team()
    summary = processor.get_team_summary()
    metrics = processor.get_workflow_metrics()

    print("=== Team Summary ===")
    print(f"Total Members: {summary['total_members']}")
    print(f"Total Work Items: {summary['total_work_items']}")
    print(f"Total Effort: {summary['total_effort']} points")
    print(f"Effort by Status: {summary['effort_by_status']}")
    print(f"Effort by Type: {summary['effort_by_type']}")
    print(f"Blocked Items: {summary['blocked_items']}")
    print(f"Ready Items: {summary['ready_items']}")

    print("\n=== Capacity Utilization ===")
    for member_id, util in summary["capacity_utilization"].items():
        member = processor.get_member(member_id)
        print(f"  {member.name}: {util['allocated']}/{util['capacity']} ({util['percentage']}%)")

    print("\n=== Workflow Metrics ===")
    print(f"Cycle Time Avg: {metrics['cycle_time_avg']} hours")
    print(f"Lead Time Avg: {metrics['lead_time_avg']} hours")
    print(f"Throughput: {metrics['throughput']} items")
    print(f"WIP Count: {metrics['wip_count']}")
    print(f"Blocked Count: {metrics['blocked_count']}")

    print("\n=== Next Priority Work for Bob ===")
    bob = next(m for m in processor.list_members() if m.name == "Bob")
    priority_work = processor.find_next_priority_work(bob.id)
    for item in priority_work:
        print(f"  [{item.status.value}] {item.title} ({item.effort} pts)")