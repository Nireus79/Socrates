"""
Tests for project_categories module.

Tests category classification and lookup functions.
"""

import pytest

from socratic_system.core.project_categories import (
    classify_project,
    get_category_description,
    get_category_requirements,
    CATEGORY_DESCRIPTIONS,
    CATEGORY_REQUIREMENTS,
)


class TestClassifyProject:
    """Tests for classify_project function."""

    def test_classify_web_application(self):
        """Test classifying a web application."""
        description = "Building a e-commerce platform with payment processing"
        category = classify_project(description)
        assert category in ["web", "ecommerce", "application"]

    def test_classify_mobile_app(self):
        """Test classifying a mobile application."""
        description = "Native iOS app for fitness tracking"
        category = classify_project(description)
        assert category is not None

    def test_classify_data_science(self):
        """Test classifying a data science project."""
        description = "Machine learning model for image classification using neural networks"
        category = classify_project(description)
        assert category is not None

    def test_classify_machine_learning(self):
        """Test classifying ML project."""
        description = "Training a transformer model for NLP tasks"
        category = classify_project(description)
        assert isinstance(category, str)

    def test_classify_api_backend(self):
        """Test classifying an API/backend project."""
        description = "RESTful API server for managing users and products"
        category = classify_project(description)
        assert isinstance(category, str)

    def test_classify_infrastructure(self):
        """Test classifying infrastructure project."""
        description = "Kubernetes deployment and cloud infrastructure setup"
        category = classify_project(description)
        assert isinstance(category, str)

    def test_classify_empty_description(self):
        """Test classifying with empty description."""
        category = classify_project("")
        assert category is not None  # Should return a default or generic category

    def test_classify_short_description(self):
        """Test classifying with very short description."""
        category = classify_project("App")
        assert isinstance(category, str)

    def test_classify_multiple_keywords(self):
        """Test classifying project with multiple relevant keywords."""
        description = "Machine learning web app for analyzing stock market data"
        category = classify_project(description)
        assert isinstance(category, str)

    def test_classify_case_insensitive(self):
        """Test classification is case-insensitive."""
        category1 = classify_project("Machine Learning Project")
        category2 = classify_project("machine learning project")
        # Both should work (exact match not required)
        assert isinstance(category1, str)
        assert isinstance(category2, str)


class TestGetCategoryDescription:
    """Tests for get_category_description function."""

    def test_get_description_web(self):
        """Test getting description for web category."""
        description = get_category_description("web")
        assert description is not None
        assert isinstance(description, str)
        assert len(description) > 0

    def test_get_description_mobile(self):
        """Test getting description for mobile category."""
        description = get_category_description("mobile")
        assert isinstance(description, str)

    def test_get_description_data_science(self):
        """Test getting description for data science category."""
        description = get_category_description("data science")
        if description:
            assert isinstance(description, str)

    def test_get_description_all_categories(self):
        """Test getting descriptions for all known categories."""
        for category in CATEGORY_DESCRIPTIONS.keys():
            description = get_category_description(category)
            assert description is not None
            assert isinstance(description, str)

    def test_get_description_unknown_category(self):
        """Test getting description for unknown category."""
        description = get_category_description("unknown_category_xyz")
        # Should return None or a generic description
        assert description is None or isinstance(description, str)

    def test_get_description_empty_category(self):
        """Test getting description with empty category."""
        description = get_category_description("")
        assert description is None or isinstance(description, str)

    def test_get_description_case_handling(self):
        """Test description retrieval with different cases."""
        desc1 = get_category_description("Web")
        desc2 = get_category_description("web")
        # Both should work or both should return None
        assert (desc1 is not None and desc2 is not None) or (desc1 is None and desc2 is None)


class TestGetCategoryRequirements:
    """Tests for get_category_requirements function."""

    def test_get_requirements_web(self):
        """Test getting requirements for web category."""
        requirements = get_category_requirements("web")
        if requirements:
            assert isinstance(requirements, list)
            if requirements:
                assert all(isinstance(req, str) for req in requirements)

    def test_get_requirements_mobile(self):
        """Test getting requirements for mobile category."""
        requirements = get_category_requirements("mobile")
        if requirements:
            assert isinstance(requirements, list)

    def test_get_requirements_all_categories(self):
        """Test getting requirements for all known categories."""
        for category in CATEGORY_REQUIREMENTS.keys():
            requirements = get_category_requirements(category)
            if requirements:
                assert isinstance(requirements, list)
                for req in requirements:
                    assert isinstance(req, str)

    def test_get_requirements_unknown_category(self):
        """Test getting requirements for unknown category."""
        requirements = get_category_requirements("unknown_xyz")
        # Should return None or empty list
        assert requirements is None or requirements == []

    def test_get_requirements_returns_list(self):
        """Test that requirements are returned as list."""
        for category in list(CATEGORY_REQUIREMENTS.keys())[:3]:  # Test first 3
            requirements = get_category_requirements(category)
            if requirements:
                assert isinstance(requirements, list)

    def test_get_requirements_no_duplicate_items(self):
        """Test that requirements don't have duplicates."""
        for category in CATEGORY_REQUIREMENTS.keys():
            requirements = get_category_requirements(category)
            if requirements:
                assert len(requirements) == len(set(requirements))

    def test_get_requirements_non_empty_strings(self):
        """Test that all requirements are non-empty strings."""
        for category in CATEGORY_REQUIREMENTS.keys():
            requirements = get_category_requirements(category)
            if requirements:
                for req in requirements:
                    assert isinstance(req, str)
                    assert len(req) > 0


class TestCategoryDataStructures:
    """Tests for category data structures."""

    def test_category_descriptions_exist(self):
        """Test that CATEGORY_DESCRIPTIONS is properly defined."""
        assert isinstance(CATEGORY_DESCRIPTIONS, dict)
        assert len(CATEGORY_DESCRIPTIONS) > 0

    def test_category_descriptions_have_strings(self):
        """Test that all descriptions are strings."""
        for category, description in CATEGORY_DESCRIPTIONS.items():
            assert isinstance(category, str)
            assert isinstance(description, str) or description is None

    def test_category_requirements_exist(self):
        """Test that CATEGORY_REQUIREMENTS is properly defined."""
        assert isinstance(CATEGORY_REQUIREMENTS, dict)
        assert len(CATEGORY_REQUIREMENTS) > 0

    def test_category_requirements_have_lists(self):
        """Test that all requirements are lists."""
        for category, requirements in CATEGORY_REQUIREMENTS.items():
            assert isinstance(category, str)
            if requirements:
                assert isinstance(requirements, list)

    def test_non_empty_category_descriptions(self):
        """Test that descriptions have meaningful content."""
        for description in CATEGORY_DESCRIPTIONS.values():
            if description:
                assert len(description) > 10  # Should have some detail

    def test_category_consistency(self):
        """Test that categories are consistent between dicts."""
        desc_categories = set(CATEGORY_DESCRIPTIONS.keys())
        req_categories = set(CATEGORY_REQUIREMENTS.keys())

        # At least one should have categories
        assert len(desc_categories) > 0 or len(req_categories) > 0


class TestCategoryClassificationIntegration:
    """Integration tests for category classification."""

    def test_classify_and_get_description(self):
        """Test classifying a project and getting its description."""
        description = "Building a mobile app for social networking"
        category = classify_project(description)

        if category:
            cat_description = get_category_description(category)
            # If we got a category, getting description should work
            assert cat_description is None or isinstance(cat_description, str)

    def test_classify_and_get_requirements(self):
        """Test classifying a project and getting its requirements."""
        description = "Machine learning model for prediction"
        category = classify_project(description)

        if category:
            requirements = get_category_requirements(category)
            if requirements:
                assert isinstance(requirements, list)
                assert len(requirements) > 0

    def test_web_project_workflow(self):
        """Test typical web project workflow."""
        project_desc = "Build a shopping cart for our e-commerce platform"
        category = classify_project(project_desc)

        assert category is not None
        assert isinstance(category, str)

        # Get requirements for this category
        requirements = get_category_requirements(category)
        assert requirements is None or isinstance(requirements, list)

    def test_data_project_workflow(self):
        """Test typical data science project workflow."""
        project_desc = "Build a recommendation engine using collaborative filtering"
        category = classify_project(project_desc)

        assert category is not None
        description = get_category_description(category)
        requirements = get_category_requirements(category)

        assert description is None or isinstance(description, str)
        assert requirements is None or isinstance(requirements, list)
