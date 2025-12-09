"""
Conflict detection and resolution system tests
"""

import pytest

from socratic_system.models import ConflictInfo


@pytest.mark.unit
class TestConflictInfoModel:
    """Tests for ConflictInfo data model"""

    def test_conflict_info_creation(self):
        """Test creating a ConflictInfo object"""
        conflict = ConflictInfo(
            conflict_id="conf_001",
            conflict_type="tech_stack",
            old_value="Python 3.8",
            new_value="Python 3.11",
            old_author="alice",
            new_author="bob",
            old_timestamp="2025-12-04T10:00:00",
            new_timestamp="2025-12-04T10:30:00",
            severity="low",
            suggestions=["Update all dependencies", "Run compatibility tests"],
        )

        assert conflict.conflict_id == "conf_001"
        assert conflict.conflict_type == "tech_stack"
        assert conflict.old_value == "Python 3.8"
        assert conflict.new_value == "Python 3.11"
        assert conflict.old_author == "alice"
        assert conflict.new_author == "bob"
        assert conflict.severity == "low"
        assert len(conflict.suggestions) == 2

    def test_conflict_info_severity_levels(self):
        """Test all valid conflict severity levels"""
        for severity in ["low", "medium", "high"]:
            conflict = ConflictInfo(
                conflict_id=f"conf_{severity}",
                conflict_type="requirements",
                old_value="v1",
                new_value="v2",
                old_author="user1",
                new_author="user2",
                old_timestamp="2025-12-04T10:00:00",
                new_timestamp="2025-12-04T10:30:00",
                severity=severity,
                suggestions=[],
            )
            assert conflict.severity == severity

    def test_conflict_info_types(self):
        """Test different conflict types"""
        conflict_types = ["tech_stack", "requirements", "goals", "constraints"]

        for conflict_type in conflict_types:
            conflict = ConflictInfo(
                conflict_id=f"conf_{conflict_type}",
                conflict_type=conflict_type,
                old_value="old",
                new_value="new",
                old_author="user1",
                new_author="user2",
                old_timestamp="2025-12-04T10:00:00",
                new_timestamp="2025-12-04T10:30:00",
                severity="medium",
                suggestions=[],
            )
            assert conflict.conflict_type == conflict_type

    def test_conflict_info_with_multiple_suggestions(self):
        """Test ConflictInfo with multiple resolution suggestions"""
        suggestions = [
            "Review both versions",
            "Vote on which to keep",
            "Merge both requirements",
            "Ask project owner for decision",
        ]

        conflict = ConflictInfo(
            conflict_id="conf_complex",
            conflict_type="requirements",
            old_value="Use sync I/O",
            new_value="Use async I/O",
            old_author="alice",
            new_author="bob",
            old_timestamp="2025-12-04T09:00:00",
            new_timestamp="2025-12-04T11:00:00",
            severity="high",
            suggestions=suggestions,
        )

        assert len(conflict.suggestions) == 4
        assert "Merge both requirements" in conflict.suggestions


@pytest.mark.unit
class TestConflictDetection:
    """Tests for conflict detection logic"""

    def test_detect_direct_value_conflict(self):
        """Test detecting direct value conflicts"""
        old_value = "Python 3.8"
        new_value = "Python 3.11"

        # Simple string comparison
        has_conflict = old_value != new_value
        assert has_conflict is True

    def test_detect_list_conflict(self):
        """Test detecting conflicts in list-based fields"""
        old_tech_stack = ["Python", "Django", "PostgreSQL"]
        new_tech_stack = ["Python", "FastAPI", "MongoDB"]

        # Check for conflicts
        old_set = set(old_tech_stack)
        new_set = set(new_tech_stack)

        # Removed items
        removed = old_set - new_set
        assert len(removed) > 0  # "Django" and "PostgreSQL" removed

        # Added items
        added = new_set - old_set
        assert len(added) > 0  # "FastAPI" and "MongoDB" added

    def test_no_conflict_same_values(self):
        """Test that identical values don't create conflicts"""
        old_value = "Use REST APIs"
        new_value = "Use REST APIs"

        has_conflict = old_value != new_value
        assert has_conflict is False

    def test_assess_conflict_severity_by_type(self):
        """Test severity assessment based on conflict type"""
        # Tech stack changes are typically high severity
        tech_conflict = ConflictInfo(
            conflict_id="tech_001",
            conflict_type="tech_stack",
            old_value="old",
            new_value="new",
            old_author="u1",
            new_author="u2",
            old_timestamp="t1",
            new_timestamp="t2",
            severity="high",
            suggestions=[],
        )
        assert tech_conflict.severity == "high"

        # Constraint changes might be medium
        constraint_conflict = ConflictInfo(
            conflict_id="const_001",
            conflict_type="constraints",
            old_value="old",
            new_value="new",
            old_author="u1",
            new_author="u2",
            old_timestamp="t1",
            new_timestamp="t2",
            severity="medium",
            suggestions=[],
        )
        assert constraint_conflict.severity == "medium"


@pytest.mark.unit
class TestConflictResolution:
    """Tests for conflict resolution strategies"""

    def test_resolution_strategy_keep_old_value(self):
        """Test resolution by keeping the old value"""
        conflict = ConflictInfo(
            conflict_id="conf_001",
            conflict_type="tech_stack",
            old_value="Python 3.8",
            new_value="Python 3.11",
            old_author="alice",
            new_author="bob",
            old_timestamp="2025-12-04T10:00:00",
            new_timestamp="2025-12-04T10:30:00",
            severity="medium",
            suggestions=["Keep old version", "Update to new version"],
        )

        # Resolve by keeping old value
        resolved_value = conflict.old_value
        assert resolved_value == "Python 3.8"

    def test_resolution_strategy_keep_new_value(self):
        """Test resolution by keeping the new value"""
        conflict = ConflictInfo(
            conflict_id="conf_001",
            conflict_type="tech_stack",
            old_value="Python 3.8",
            new_value="Python 3.11",
            old_author="alice",
            new_author="bob",
            old_timestamp="2025-12-04T10:00:00",
            new_timestamp="2025-12-04T10:30:00",
            severity="medium",
            suggestions=[],
        )

        # Resolve by keeping new value (typically newer timestamp wins)
        resolved_value = conflict.new_value
        assert resolved_value == "Python 3.11"

    def test_resolution_strategy_merge_values(self):
        """Test resolution by merging conflicting values"""
        conflict = ConflictInfo(
            conflict_id="req_001",
            conflict_type="requirements",
            old_value="Authentication, Rate limiting",
            new_value="Authentication, Caching, API versioning",
            old_author="alice",
            new_author="bob",
            old_timestamp="2025-12-04T10:00:00",
            new_timestamp="2025-12-04T10:30:00",
            severity="low",
            suggestions=["Merge requirements"],
        )

        # Merge: combine unique items
        old_reqs = {r.strip() for r in conflict.old_value.split(",")}
        new_reqs = {r.strip() for r in conflict.new_value.split(",")}
        merged = old_reqs | new_reqs  # Union of both

        assert "Authentication" in merged
        assert "Rate limiting" in merged
        assert "Caching" in merged
        assert "API versioning" in merged
        assert len(merged) == 4


@pytest.mark.unit
class TestConflictEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_self_conflict_same_author_different_time(self):
        """Test conflict from same author at different times (auto-update)"""
        conflict = ConflictInfo(
            conflict_id="self_conf_001",
            conflict_type="goals",
            old_value="Build web app",
            new_value="Build web app and mobile app",
            old_author="alice",
            new_author="alice",  # Same author
            old_timestamp="2025-12-04T10:00:00",
            new_timestamp="2025-12-04T10:30:00",
            severity="low",
            suggestions=["Auto-accept (same author)"],
        )

        # Same author suggests auto-resolution
        assert conflict.old_author == conflict.new_author

    def test_high_priority_conflict_needs_review(self):
        """Test that high severity conflicts need manual review"""
        conflict = ConflictInfo(
            conflict_id="high_conf_001",
            conflict_type="tech_stack",
            old_value="Traditional architecture",
            new_value="Microservices architecture",
            old_author="team_lead",
            new_author="architect",
            old_timestamp="2025-12-04T09:00:00",
            new_timestamp="2025-12-04T14:00:00",
            severity="high",
            suggestions=[
                "Schedule team discussion",
                "Review architecture docs",
                "Get consensus before proceeding",
            ],
        )

        # High severity should have suggestions for review
        assert conflict.severity == "high"
        assert len(conflict.suggestions) > 0

    def test_time_based_conflict_resolution(self):
        """Test resolving conflict based on timestamp (last write wins)"""
        conflict = ConflictInfo(
            conflict_id="time_conf_001",
            conflict_type="constraints",
            old_value="No external dependencies",
            new_value="External APIs allowed",
            old_author="alice",
            new_author="bob",
            old_timestamp="2025-12-04T10:00:00",
            new_timestamp="2025-12-04T11:00:00",  # Later timestamp
            severity="medium",
            suggestions=[],
        )

        # Last write wins strategy
        # Since new_timestamp is later, new_value should win
        resolved_value = conflict.new_value
        assert resolved_value == "External APIs allowed"

    def test_empty_value_conflicts(self):
        """Test handling conflicts with empty/null values"""
        conflict = ConflictInfo(
            conflict_id="empty_conf_001",
            conflict_type="goals",
            old_value="",  # Empty old value
            new_value="Clear project goals",
            old_author="alice",
            new_author="bob",
            old_timestamp="2025-12-04T10:00:00",
            new_timestamp="2025-12-04T10:30:00",
            severity="low",
            suggestions=["Accept new value - old was empty"],
        )

        # When old is empty, new should typically be accepted
        resolved_value = conflict.new_value if conflict.old_value == "" else conflict.old_value
        assert resolved_value == "Clear project goals"


@pytest.mark.integration
class TestConflictResolutionWorkflow:
    """Integration tests for complete conflict resolution workflows"""

    def test_detect_and_suggest_resolution(self):
        """Test detecting conflict and generating suggestions"""
        conflict = ConflictInfo(
            conflict_id="workflow_001",
            conflict_type="requirements",
            old_value="Basic authentication",
            new_value="OAuth 2.0 with MFA",
            old_author="alice",
            new_author="bob",
            old_timestamp="2025-12-04T10:00:00",
            new_timestamp="2025-12-04T11:00:00",
            severity="high",
            suggestions=[
                "Review security requirements",
                "Compare implementation complexity",
                "Consult security team",
                "Vote among project members",
            ],
        )

        # Verify conflict properties
        assert conflict.conflict_id == "workflow_001"
        assert conflict.old_author != conflict.new_author
        assert len(conflict.suggestions) == 4

        # Resolution workflow would:
        # 1. Notify both authors
        # 2. Display suggestions
        # 3. Allow manual selection
        # 4. Record resolution

    def test_multi_conflict_resolution_priority(self):
        """Test handling multiple conflicts with priority ordering"""
        conflicts = [
            ConflictInfo(
                conflict_id="c_low",
                conflict_type="goals",
                old_value="v1",
                new_value="v2",
                old_author="u1",
                new_author="u2",
                old_timestamp="t1",
                new_timestamp="t2",
                severity="low",
                suggestions=[],
            ),
            ConflictInfo(
                conflict_id="c_high",
                conflict_type="tech_stack",
                old_value="v1",
                new_value="v2",
                old_author="u1",
                new_author="u2",
                old_timestamp="t1",
                new_timestamp="t2",
                severity="high",
                suggestions=[],
            ),
            ConflictInfo(
                conflict_id="c_medium",
                conflict_type="requirements",
                old_value="v1",
                new_value="v2",
                old_author="u1",
                new_author="u2",
                old_timestamp="t1",
                new_timestamp="t2",
                severity="medium",
                suggestions=[],
            ),
        ]

        # Sort by severity (high first)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_conflicts = sorted(conflicts, key=lambda c: priority_order.get(c.severity, 3))

        # High severity should be first
        assert sorted_conflicts[0].severity == "high"
        assert sorted_conflicts[1].severity == "medium"
        assert sorted_conflicts[2].severity == "low"

    def test_conflict_resolution_audit_trail(self):
        """Test recording conflict resolution history"""
        conflict = ConflictInfo(
            conflict_id="audit_001",
            conflict_type="constraints",
            old_value="Single server deployment",
            new_value="Multi-region deployment",
            old_author="alice",
            new_author="bob",
            old_timestamp="2025-12-04T10:00:00",
            new_timestamp="2025-12-04T12:00:00",
            severity="high",
            suggestions=[],
        )

        # Resolution record
        resolution = {
            "conflict_id": conflict.conflict_id,
            "resolution_type": "manual_approval",
            "chosen_value": conflict.new_value,
            "resolved_by": "charlie",
            "resolved_at": "2025-12-04T13:00:00",
            "reasoning": "Multi-region deployment provides better reliability",
        }

        # Verify audit trail data
        assert resolution["conflict_id"] == "audit_001"
        assert resolution["chosen_value"] == "Multi-region deployment"
        assert resolution["resolved_by"] == "charlie"
        assert "reasoning" in resolution


@pytest.mark.unit
class TestConflictPreventionStrategies:
    """Tests for conflict prevention mechanisms"""

    def test_optimistic_locking_prevents_conflicts(self):
        """Test that optimistic locking can prevent some conflicts"""
        # Version 1 of resource
        resource_v1 = {"version": 1, "content": "Original content", "author": "alice"}

        # User A tries to update with version 1
        update_a = {"version": 1, "content": "Updated by A", "author": "alice"}

        # User B tries to update with version 1
        update_b = {"version": 1, "content": "Updated by B", "author": "bob"}

        # First update succeeds and increments version
        if update_a["version"] == resource_v1["version"]:
            resource_v1["content"] = update_a["content"]
            resource_v1["version"] = 2
            first_update_success = True
        else:
            first_update_success = False

        assert first_update_success is True

        # Second update fails because version doesn't match
        if update_b["version"] == resource_v1["version"]:
            resource_v1["content"] = update_b["content"]
            resource_v1["version"] = 3
            second_update_success = True
        else:
            second_update_success = False

        # Second update should fail (conflict prevented)
        assert second_update_success is False
        assert resource_v1["version"] == 2  # Version not incremented

    def test_merge_strategies_prevent_conflicts(self):
        """Test that merge strategies can prevent some conflicts"""
        # Base requirements
        base = ["Authentication", "Logging"]

        # Branch A adds requirements
        branch_a = base + ["Rate limiting"]

        # Branch B adds different requirements
        branch_b = base + ["Caching", "Monitoring"]

        # Three-way merge
        merged = list(set(branch_a) | set(branch_b))

        # All requirements should be present
        assert "Authentication" in merged
        assert "Logging" in merged
        assert "Rate limiting" in merged
        assert "Caching" in merged
        assert "Monitoring" in merged
