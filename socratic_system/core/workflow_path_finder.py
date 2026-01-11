"""
Workflow path finder using Depth-First Search (DFS) algorithm

Enumerates all valid paths through a workflow graph from start node
to any end node, handling cycles and multiple possible routes.
"""

import logging
from typing import Dict, List, Set, Tuple

from socratic_system.models.workflow import WorkflowDefinition, WorkflowPath

logger = logging.getLogger(__name__)


class WorkflowPathFinder:
    """Find all valid paths through a workflow graph using DFS"""

    def __init__(self, workflow: WorkflowDefinition):
        """
        Initialize path finder with a workflow definition.

        Args:
            workflow: WorkflowDefinition to analyze
        """
        self.workflow = workflow
        self.adjacency_list = self._build_adjacency_list()
        logger.debug(
            f"WorkflowPathFinder initialized for workflow {workflow.workflow_id} "
            f"with {len(workflow.nodes)} nodes and {len(workflow.edges)} edges"
        )

    def find_all_paths(self) -> List[WorkflowPath]:
        """
        Find all valid paths from start node to any end node.

        Uses DFS to enumerate all possible routes through the workflow,
        avoiding infinite loops by detecting visited nodes.

        Returns:
            List of WorkflowPath objects representing all valid routes
        """
        logger.debug(
            f"Finding all paths from '{self.workflow.start_node}' to {self.workflow.end_nodes}"
        )

        all_paths = []

        # Find paths to each end node
        for end_node in self.workflow.end_nodes:
            logger.debug(f"Searching for paths to end node: {end_node}")

            paths = self._dfs_paths(
                current=self.workflow.start_node,
                target=end_node,
                visited=set(),
                current_path_nodes=[],
                current_path_edges=[],
            )

            logger.debug(f"Found {len(paths)} paths to {end_node}")
            all_paths.extend(paths)

        # Convert raw paths to WorkflowPath objects
        workflow_paths = [
            self._create_workflow_path(nodes, edges) for nodes, edges in all_paths
        ]

        logger.info(
            f"Path enumeration complete: {len(workflow_paths)} total paths found "
            f"for workflow {self.workflow.workflow_id}"
        )

        return workflow_paths

    def _dfs_paths(
        self,
        current: str,
        target: str,
        visited: Set[str],
        current_path_nodes: List[str],
        current_path_edges: List[str],
    ) -> List[Tuple[List[str], List[str]]]:
        """
        Recursively find all paths from current node to target using DFS.

        Avoids cycles by tracking visited nodes.

        Args:
            current: Current node ID
            target: Target node ID
            visited: Set of already visited nodes (to avoid cycles)
            current_path_nodes: Ordered list of node IDs in current path
            current_path_edges: Ordered list of edge IDs in current path

        Returns:
            List of (node_list, edge_list) tuples representing complete paths
        """
        # Mark current node as visited
        visited.add(current)
        current_path_nodes.append(current)

        logger.debug(f"DFS at node {current}, visited: {visited}")

        # If we reached the target, return this path
        if current == target:
            logger.debug(f"Found complete path: {current_path_nodes}")
            return [(list(current_path_nodes), list(current_path_edges))]

        # Explore neighbors
        all_paths = []
        neighbors = self.adjacency_list.get(current, [])

        logger.debug(f"Node {current} has {len(neighbors)} neighbors")

        for neighbor_id, edge_id in neighbors:
            if neighbor_id not in visited:
                # Create new visited set for this branch (backtracking)
                new_visited = visited.copy()

                # Recursively explore this branch
                new_edges = current_path_edges + [edge_id]
                paths = self._dfs_paths(
                    current=neighbor_id,
                    target=target,
                    visited=new_visited,
                    current_path_nodes=list(current_path_nodes),
                    current_path_edges=new_edges,
                )

                all_paths.extend(paths)
            else:
                logger.debug(f"Skipping neighbor {neighbor_id} (already visited)")

        return all_paths

    def _build_adjacency_list(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Build adjacency list representation of the graph.

        Converts edges into a neighbor mapping for efficient DFS traversal.

        Returns:
            Dict mapping node ID -> list of (neighbor_node_id, edge_id) tuples
        """
        adjacency_list: Dict[str, List[Tuple[str, str]]] = {}

        for edge in self.workflow.edges:
            from_node = edge.from_node
            to_node = edge.to_node

            # Create entry if not exists
            if from_node not in adjacency_list:
                adjacency_list[from_node] = []

            # Add neighbor with edge ID
            adjacency_list[from_node].append((to_node, edge.from_node + "-" + to_node))

            logger.debug(f"Edge: {from_node} -> {to_node}")

        logger.debug(f"Built adjacency list with {len(adjacency_list)} nodes")
        return adjacency_list

    def _create_workflow_path(
        self, nodes: List[str], edges: List[str]
    ) -> WorkflowPath:
        """
        Create a WorkflowPath object from ordered node and edge lists.

        Args:
            nodes: Ordered list of node IDs in the path
            edges: Ordered list of edge IDs in the path

        Returns:
            WorkflowPath with basic structure (metrics calculated later)
        """
        path_id = f"{self.workflow.workflow_id}_path_{len(nodes)}nodes"

        logger.debug(f"Creating WorkflowPath {path_id}")

        return WorkflowPath(
            path_id=path_id,
            nodes=nodes,
            edges=edges,
        )
