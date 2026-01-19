"""
Workflow cost calculator for estimating API token consumption

Calculates total token costs for workflow paths including node processing
and edge transitions, with currency conversion.
"""

import logging
from typing import Any, Dict

from socratic_system.models.workflow import WorkflowDefinition, WorkflowPath

logger = logging.getLogger(__name__)


class WorkflowCostCalculator:
    """Calculate API token costs for workflow paths"""

    # Token cost constants (estimated based on Claude API usage patterns)
    COST_PER_QUESTION_GENERATION = 500  # Tokens to generate a question
    COST_PER_QUESTION_ANALYSIS = 1000  # Tokens to analyze user response
    COST_PER_VALIDATION = 800  # Tokens to validate specifications
    COST_PER_MATURITY_CALCULATION = 300  # Tokens for maturity calculation

    # Token to USD conversion
    INPUT_TOKEN_COST = 0.000015  # USD per input token
    OUTPUT_TOKEN_COST = 0.000075  # USD per output token
    AVG_TOKEN_COST = 0.000045  # Average USD per token (balanced estimate)

    def __init__(self):
        """Initialize cost calculator with token constants"""
        logger.debug("WorkflowCostCalculator initialized")

    def calculate_path_cost(
        self, path: WorkflowPath, workflow: WorkflowDefinition
    ) -> Dict[str, Any]:
        """
        Calculate total token cost for a workflow path.

        Sums estimated tokens from all nodes and edges in the path,
        then converts to USD.

        Args:
            path: WorkflowPath to calculate cost for
            workflow: WorkflowDefinition containing node definitions

        Returns:
            Dict with:
                - total_tokens: Total tokens for this path
                - total_cost_usd: USD cost
                - token_breakdown: Dict of node_id -> token_count
        """
        total_tokens = 0
        token_breakdown: Dict[str, int] = {}

        logger.debug(f"Calculating cost for path {path.path_id}")

        # Sum tokens from nodes
        for node_id in path.nodes:
            if node_id not in workflow.nodes:
                logger.warning(f"Node {node_id} not found in workflow")
                continue

            node = workflow.nodes[node_id]
            node_tokens = node.estimated_tokens

            total_tokens += node_tokens
            token_breakdown[node_id] = node_tokens

            logger.debug(f"  Node {node_id}: {node_tokens} tokens")

        # Sum tokens from edges
        for edge_id in path.edges:
            # Find edge in workflow
            edge_cost = self._find_edge_cost(workflow, edge_id)
            total_tokens += edge_cost

            logger.debug(f"  Edge {edge_id}: {edge_cost} tokens")

        # Calculate USD cost
        total_cost_usd = total_tokens * self.AVG_TOKEN_COST

        result = {
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost_usd, 6),  # Round to 6 decimals
            "token_breakdown": token_breakdown,
        }

        logger.info(f"Path {path.path_id} cost: {total_tokens} tokens (${total_cost_usd:.6f})")

        return result

    def _find_edge_cost(self, workflow: WorkflowDefinition, edge_id: str) -> int:
        """
        Find cost (tokens) for an edge by ID.

        Args:
            workflow: WorkflowDefinition containing edges
            edge_id: ID of edge to find cost for

        Returns:
            Token cost for the edge (0 if not found)
        """
        for edge in workflow.edges:
            # Edge ID is typically "from_node-to_node"
            potential_id = f"{edge.from_node}-{edge.to_node}"
            if potential_id == edge_id or edge_id == f"{edge.from_node}-{edge.to_node}":
                return edge.cost

        logger.warning(f"Edge {edge_id} not found, defaulting to 0 cost")
        return 0

    def estimate_cost_per_node_type(self, node_type: str) -> int:
        """
        Estimate token cost based on node type.

        Useful for creating workflows with realistic token estimates.

        Args:
            node_type: Type of node (from WorkflowNodeType enum)

        Returns:
            Estimated token count for that node type
        """
        cost_map = {
            "phase_start": 0,
            "question_set": self.COST_PER_QUESTION_GENERATION,
            "analysis": self.COST_PER_QUESTION_ANALYSIS,
            "decision": self.COST_PER_VALIDATION,
            "phase_end": 0,
            "validation": self.COST_PER_VALIDATION,
        }

        return cost_map.get(node_type, 0)

    def get_cost_breakdown(self, total_tokens: int) -> Dict[str, Any]:
        """
        Break down token cost into components.

        Useful for explaining cost estimates to users.

        Args:
            total_tokens: Total tokens in path

        Returns:
            Dict with cost breakdown details
        """
        cost_usd = total_tokens * self.AVG_TOKEN_COST

        return {
            "total_tokens": total_tokens,
            "cost_usd": round(cost_usd, 6),
            "cost_components": {
                "input_only": round(total_tokens * self.INPUT_TOKEN_COST, 6),
                "output_only": round(total_tokens * self.OUTPUT_TOKEN_COST, 6),
                "balanced": round(cost_usd, 6),
            },
        }
