"""
Team Flow E2E Package.

This package provides team workflow processing capabilities
for end-to-end testing scenarios.
"""

from .child_b import (
    TeamFlowProcessor,
    TeamMember,
    WorkItem,
    MemberRole,
    WorkItemStatus,
    WorkItemType,
    create_sample_team,
)

__all__ = [
    "TeamFlowProcessor",
    "TeamMember",
    "WorkItem",
    "MemberRole",
    "WorkItemStatus",
    "WorkItemType",
    "create_sample_team",
]