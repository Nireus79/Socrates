"""
Claude-powered insight categorization for intelligent spec mapping.

Uses Claude to understand insight content and map to appropriate categories
based on project type and phase context.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List

from socratic_system.core.project_categories import (
    get_phase_categories,
    get_project_type_description,
)

logger = logging.getLogger(__name__)


class InsightCategorizer:
    """
    Uses Claude to intelligently categorize insights into phase-specific categories.

    Instead of simple field mapping, analyzes insight content semantically to
    understand what category it belongs to, considering project type and phase.
    """

    def __init__(self, claude_client):
        """
        Initialize with Claude client.

        Args:
            claude_client: Claude API client for making categorization requests
        """
        logger.debug(
            f"Initializing InsightCategorizer with Claude client: {claude_client is not None}"
        )
        self.claude_client = claude_client
        logger.info("InsightCategorizer initialized successfully")

    def categorize_insights(
        self, insights: Dict, phase: str, project_type: str = "software", user_id: str = None
    ) -> List[Dict]:
        """
        Categorize insights using Claude intelligence.

        Claude analyzes the semantic meaning of insights to map them to the most
        appropriate categories for the given project type and phase.

        Args:
            insights: Dict of insights (e.g., goals, requirements, constraints)
            phase: Current phase (discovery, analysis, design, implementation)
            project_type: Type of project for context (software, business, etc.)
            user_id: Optional user ID for API key lookup in Claude client

        Returns:
            List of categorized spec dicts with category, content, confidence, etc.
        """
        logger.debug(
            f"Starting insight categorization: phase={phase}, project_type={project_type}, fields={list(insights.keys())}, user_id={user_id}"
        )

        if not insights:
            logger.debug("No insights provided, returning empty list")
            return []

        # Get valid categories for this phase and project type
        phase_categories = get_phase_categories(project_type)
        valid_categories = list(phase_categories.get(phase, {}).keys())

        logger.debug(f"Valid categories for {project_type}/{phase}: {valid_categories}")

        if not valid_categories:
            logger.warning(f"No categories found for {project_type}/{phase}, using fallback")
            return self._fallback_categorization(insights, phase, project_type)

        try:
            # Prepare insights for Claude
            logger.debug("Formatting insights for Claude API")
            insights_text = self._format_insights_for_claude(insights)
            logger.debug(f"Insights formatted: {len(insights_text)} characters")

            # Create prompt for Claude
            logger.debug("Creating categorization prompt")
            prompt = self._create_categorization_prompt(
                insights_text, phase, project_type, valid_categories
            )
            logger.debug(f"Prompt created: {len(prompt)} characters")

            # Call Claude (pass user_id for API key lookup)
            logger.debug("Sending request to Claude API")
            response = self.claude_client.generate_response(prompt, user_id=user_id)
            logger.debug(f"Received response from Claude: {len(response)} characters")

            # Parse Claude's response
            logger.debug("Parsing Claude's response")
            categorized = self._parse_claude_response(response, insights)

            if categorized:
                unique_categories = len({c["category"] for c in categorized})
                logger.info(
                    f"Claude categorization successful: {len(categorized)} specs into {unique_categories} categories"
                )
                return categorized
            else:
                logger.warning("Claude returned empty categorization, using fallback")
                return self._fallback_categorization(insights, phase, project_type)

        except Exception as e:
            logger.error(f"Claude categorization failed: {type(e).__name__}: {e}, using fallback")
            return self._fallback_categorization(insights, phase, project_type)

    def _format_insights_for_claude(self, insights: Dict) -> str:
        """Format insights dict into readable text for Claude"""
        logger.debug(f"Formatting {len(insights)} insight fields for Claude")
        lines = []
        for field, values in insights.items():
            if not values:
                logger.debug(f"Skipping empty field: {field}")
                continue

            if isinstance(values, list):
                values_text = ", ".join(str(v) for v in values if v)
            else:
                values_text = str(values)

            if values_text:
                lines.append(f"- {field}: {values_text}")
                logger.debug(f"Added field '{field}' with {len(values_text)} characters")

        result = "\n".join(lines) if lines else ""
        logger.debug(
            f"Formatted insights into {len(lines)} fields ({len(result)} total characters)"
        )
        return result

    def _create_categorization_prompt(
        self, insights_text: str, phase: str, project_type: str, valid_categories: List[str]
    ) -> str:
        """Create Claude prompt for categorizing insights"""
        logger.debug(
            f"Creating prompt for {project_type}/{phase} with {len(valid_categories)} categories"
        )
        project_description = get_project_type_description(project_type)
        categories_list = ", ".join(valid_categories)

        prompt = f"""You are helping categorize project specifications for a {project_type} project.

PROJECT TYPE: {project_description}
PHASE: {phase}
VALID CATEGORIES: {categories_list}

Below are insights extracted from user input. Your task is to map each insight to the most appropriate category from the valid categories above.

INSIGHTS:
{insights_text}

For each insight, provide:
1. The exact text of the insight
2. The best matching category from VALID CATEGORIES
3. Your confidence (0.0-1.0) that this is the right category

Return ONLY valid JSON (no markdown, no code blocks), in this exact format:
[
  {{
    "content": "exact insight text",
    "category": "category name",
    "confidence": 0.95
  }},
  {{
    "content": "another insight",
    "category": "category name",
    "confidence": 0.87
  }}
]

Rules:
- Each insight gets exactly one category
- Confidence should reflect how well the category matches the insight
- Use only categories from VALID CATEGORIES list
- If an insight doesn't clearly match any category, use the most general match with lower confidence
- Return empty array [] if there are no insights to categorize"""

        return prompt

    def _parse_claude_response(self, response: str, original_insights: Dict) -> List[Dict]:
        """
        Parse Claude's JSON response into categorized specs.

        Args:
            response: Claude's response text containing JSON
            original_insights: Original insights dict for reference

        Returns:
            List of categorized spec dicts
        """
        logger.debug(f"Parsing Claude response ({len(response)} characters)")

        try:
            # Extract JSON from response
            json_str = response.strip()
            logger.debug("Extracting JSON from response")

            # Remove markdown code blocks if present
            if json_str.startswith("```"):
                logger.debug("Detected markdown code block, extracting JSON")
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                json_str = json_str.strip()

            # Parse JSON
            logger.debug("Parsing JSON")
            categorized_raw = json.loads(json_str)

            if not isinstance(categorized_raw, list):
                logger.warning(f"Claude response is not a list: {type(categorized_raw)}")
                return []

            logger.debug(f"Parsed {len(categorized_raw)} items from Claude response")

            # Convert to spec format
            categorized = []
            for i, item in enumerate(categorized_raw):
                if not isinstance(item, dict):
                    logger.debug(f"Item {i} is not dict, skipping")
                    continue

                spec = {
                    "category": item.get("category", ""),
                    "content": item.get("content", ""),
                    "confidence": float(item.get("confidence", 0.9)),
                    "value": 1.0,  # Default value
                    "source_field": self._find_source_field(
                        item.get("content", ""), original_insights
                    ),
                    "timestamp": datetime.now().isoformat(),
                }

                # Only include if we have content and category
                if spec["content"] and spec["category"]:
                    logger.debug(
                        f"Added spec: {spec['category']} (confidence={spec['confidence']:.2f}, source={spec['source_field']})"
                    )
                    categorized.append(spec)
                else:
                    logger.debug(f"Skipping item {i}: missing content or category")

            logger.info(f"Parsed {len(categorized)} valid specs from {len(categorized_raw)} items")
            return categorized

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude's JSON response: {type(e).__name__}: {e}")
            logger.debug(f"Response was: {response[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Error processing Claude response: {type(e).__name__}: {e}")
            return []

    def _find_source_field(self, content: str, original_insights: Dict) -> str:
        """Try to find which field this content came from"""
        logger.debug(f"Finding source field for content: {content[:50]}...")
        content_lower = content.lower()

        for field, values in original_insights.items():
            if not values:
                continue

            if isinstance(values, list):
                for val in values:
                    if val and str(val).lower() in content_lower:
                        logger.debug(f"Matched to field: {field}")
                        return field
            else:
                if str(values).lower() in content_lower:
                    logger.debug(f"Matched to field: {field}")
                    return field

        logger.debug("No matching field found, returning 'unknown'")
        return "unknown"

    def _fallback_categorization(self, insights: Dict, phase: str, project_type: str) -> List[Dict]:
        """
        Fallback simple categorization if Claude fails.

        Uses basic field-to-category mapping for robustness.
        """
        logger.debug(f"Using fallback categorization for {project_type}/{phase}")

        categorized = []
        valid_categories = set(get_phase_categories(project_type).get(phase, {}).keys())
        logger.debug(f"Valid categories for fallback: {valid_categories}")

        # Basic field mapping (fallback)
        field_to_category = {
            "goals": "goals",
            "objectives": "objectives",
            "requirements": "requirements",
            "tech_stack": "tech_stack",
            "technology": "tech_stack",
            "constraints": "constraints",
            "scope": "scope",
            "budget": "constraints",
            "timeline": "timeline",
            "team_structure": "team_structure",
            "resources": "resources",
            "assumptions": "assumptions",
            "risks": "risks",
            "dependencies": "dependencies",
        }

        for field, values in insights.items():
            if not values:
                logger.debug(f"Skipping empty field in fallback: {field}")
                continue

            # Map field to category with confidence tracking
            category = field_to_category.get(field, field)
            is_direct_map = field in field_to_category  # Exact match in mapping
            confidence = 0.85 if is_direct_map else 0.75  # Higher confidence for direct maps
            logger.debug(f"Fallback mapping: {field} -> {category} (confidence={confidence:.2f})")

            # Ensure category is valid for this phase
            if category not in valid_categories:
                # Try to find closest match
                matching = [c for c in valid_categories if field.lower() in c.lower()]
                if matching:
                    logger.debug(f"Found matching category for '{field}': {matching[0]}")
                    category = matching[0]
                    confidence = 0.70  # Lower confidence for fuzzy match
                else:
                    logger.debug(f"No valid category found for '{field}' in fallback, skipping")
                    continue

            # Create specs with confidence based on mapping quality
            spec_count = 0
            if isinstance(values, list):
                for value in values:
                    if value:
                        categorized.append(
                            {
                                "category": category,
                                "content": str(value),
                                "confidence": confidence,  # Use computed confidence
                                "value": 1.0,
                                "source_field": field,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        spec_count += 1
                if spec_count > 0:
                    logger.debug(f"Created {spec_count} fallback specs for field '{field}' (confidence={confidence:.2f})")
            else:
                if values:
                    categorized.append(
                        {
                            "category": category,
                            "content": str(values),
                            "confidence": confidence,  # Use computed confidence
                            "value": 1.0,
                            "source_field": field,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    logger.debug(f"Created 1 fallback spec for field '{field}' (confidence={confidence:.2f})")

        logger.info(f"Fallback categorization complete: {len(categorized)} specs created")
        return categorized
