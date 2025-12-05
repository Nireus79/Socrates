"""
Conflict rules and categories for Socratic RAG System
"""

from typing import Optional

# Categorized conflict rules for tech stack detection
CONFLICT_RULES = {
    "databases": [
        "mysql",
        "postgresql",
        "mongodb",
        "sqlite",
        "oracle",
        "redis",
        "cassandra",
        "dynamodb",
        "elasticsearch",
        "neo4j",
        "firestore",
    ],
    "frontend_frameworks": [
        "react",
        "vue",
        "angular",
        "svelte",
        "ember",
        "backbone",
        "next.js",
        "nuxt",
        "gatsby",
        "astro",
        "quasar",
    ],
    "backend_frameworks": [
        "django",
        "flask",
        "fastapi",
        "express",
        "spring",
        "rails",
        "laravel",
        "asp.net",
        "go",
        "rust-actix",
        "java-spring",
    ],
    "languages": [
        "python",
        "javascript",
        "typescript",
        "java",
        "go",
        "rust",
        "c#",
        "php",
        "ruby",
        "kotlin",
        "scala",
    ],
    "package_managers": ["npm", "yarn", "pip", "poetry", "cargo", "maven", "gradle"],
    "testing_frameworks": ["pytest", "jest", "jasmine", "mocha", "unittest", "testng"],
    "build_tools": ["webpack", "vite", "rollup", "parcel", "maven", "gradle"],
}


def find_conflict_category(item1: str, item2: str) -> Optional[str]:
    """
    Find if two items belong to the same conflicting category.

    Returns the category name if both items are in the same category,
    None otherwise.
    """
    if not item1 or not item2:
        return None

    item1_str = str(item1).lower().strip()
    item2_str = str(item2).lower().strip()

    for category, items in CONFLICT_RULES.items():
        # Check if both items are in the same category
        item1_in_category = any(
            item1_str in tech.lower() or tech.lower() in item1_str for tech in items
        )
        item2_in_category = any(
            item2_str in tech.lower() or tech.lower() in item2_str for tech in items
        )

        if item1_in_category and item2_in_category:
            return category

    return None
