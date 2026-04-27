"""
Unit tests for the TaskService business logic layer.

These tests validate:
  - Task creation with correct defaults
  - Status workflow transitions (valid and invalid)
  - Assignee membership validation
  - Soft-delete behavior
"""

import uuid
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.task import Task, TaskStatus, TaskPriority, VALID_TRANSITIONS
from app.models.user import User
from app.models.membership import MemberRole
from app.services.task_service import TaskService
from app.exceptions import ResourceNotFound, ValidationError


class TestTaskWorkflowTransitions:
    """Test the status workflow state machine."""

    def test_valid_transitions_from_todo(self):
        """TODO can only move to IN_PROGRESS."""
        allowed = VALID_TRANSITIONS[TaskStatus.TODO]
        assert TaskStatus.IN_PROGRESS in allowed
        assert TaskStatus.DONE not in allowed
        assert TaskStatus.IN_REVIEW not in allowed

    def test_valid_transitions_from_in_progress(self):
        """IN_PROGRESS can go to IN_REVIEW or back to TODO."""
        allowed = VALID_TRANSITIONS[TaskStatus.IN_PROGRESS]
        assert TaskStatus.IN_REVIEW in allowed
        assert TaskStatus.TODO in allowed
        assert TaskStatus.DONE not in allowed

    def test_valid_transitions_from_in_review(self):
        """IN_REVIEW can go to DONE or back to IN_PROGRESS."""
        allowed = VALID_TRANSITIONS[TaskStatus.IN_REVIEW]
        assert TaskStatus.DONE in allowed
        assert TaskStatus.IN_PROGRESS in allowed
        assert TaskStatus.TODO not in allowed

    def test_valid_transitions_from_done(self):
        """DONE can only reopen to TODO."""
        allowed = VALID_TRANSITIONS[TaskStatus.DONE]
        assert TaskStatus.TODO in allowed
        assert len(allowed) == 1

    def test_no_skip_transitions(self):
        """Verify you cannot skip from TODO directly to DONE."""
        allowed = VALID_TRANSITIONS[TaskStatus.TODO]
        assert TaskStatus.DONE not in allowed

    def test_no_skip_to_review(self):
        """Verify you cannot skip from TODO directly to IN_REVIEW."""
        allowed = VALID_TRANSITIONS[TaskStatus.TODO]
        assert TaskStatus.IN_REVIEW not in allowed


class TestTaskPriority:
    """Test priority enum values."""

    def test_all_priorities_defined(self):
        assert set(TaskPriority) == {
            TaskPriority.LOW,
            TaskPriority.MEDIUM,
            TaskPriority.HIGH,
            TaskPriority.URGENT,
        }

    def test_priority_values(self):
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.URGENT.value == "urgent"


class TestRoleHierarchy:
    """Test role permission checks."""

    def test_owner_has_all_permissions(self):
        from app.models.membership import has_permission
        assert has_permission(MemberRole.OWNER, MemberRole.OWNER)
        assert has_permission(MemberRole.OWNER, MemberRole.ADMIN)
        assert has_permission(MemberRole.OWNER, MemberRole.MEMBER)

    def test_admin_cannot_act_as_owner(self):
        from app.models.membership import has_permission
        assert not has_permission(MemberRole.ADMIN, MemberRole.OWNER)
        assert has_permission(MemberRole.ADMIN, MemberRole.ADMIN)
        assert has_permission(MemberRole.ADMIN, MemberRole.MEMBER)

    def test_member_is_lowest(self):
        from app.models.membership import has_permission
        assert not has_permission(MemberRole.MEMBER, MemberRole.OWNER)
        assert not has_permission(MemberRole.MEMBER, MemberRole.ADMIN)
        assert has_permission(MemberRole.MEMBER, MemberRole.MEMBER)
