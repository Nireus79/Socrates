"""
SkillComposer - Create and execute skill chains and compositions.

Provides:
- Skill composition/chaining
- Sequential and conditional execution
- Parameter passing between skills
- Error handling in chains
- Composition optimization
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from core.base_service import BaseService
from core.event_bus import EventBus


class SkillComposition:
    """Represents a composition of multiple skills."""

    def __init__(
        self,
        composition_id: str,
        name: str,
        skills: List[str],
        execution_type: str = "sequential",
    ):
        """Initialize skill composition."""
        self.composition_id = composition_id
        self.name = name
        self.skills = skills
        self.execution_type = execution_type  # sequential, parallel, conditional
        self.parameter_mappings: Dict[str, Dict[str, str]] = {}  # output->input mapping
        self.conditions: Dict[int, Dict[str, Any]] = {}  # index->condition
        self.error_handling: Dict[str, str] = {}  # skill_id->handler
        self.created_at = datetime.utcnow().isoformat()

    def add_parameter_mapping(
        self,
        from_skill_index: int,
        from_param: str,
        to_skill_index: int,
        to_param: str,
    ) -> None:
        """Map output from one skill to input of another."""
        key = f"{from_skill_index}_{from_param}"
        self.parameter_mappings[key] = {
            "to_skill": to_skill_index,
            "to_param": to_param,
        }

    def add_condition(self, skill_index: int, condition: Dict[str, Any]) -> None:
        """Add execution condition for a skill."""
        self.conditions[skill_index] = condition

    def add_error_handler(self, skill_id: str, handler: str) -> None:
        """Add error handler for a skill."""
        self.error_handling[skill_id] = handler

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "composition_id": self.composition_id,
            "name": self.name,
            "skills": self.skills,
            "execution_type": self.execution_type,
            "parameter_mappings": self.parameter_mappings,
            "conditions": self.conditions,
            "error_handling": self.error_handling,
            "created_at": self.created_at,
        }


class SkillComposer(BaseService):
    """Service for composing and executing skill chains."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize skill composer."""
        super().__init__("composition", config)
        self.compositions: Dict[str, SkillComposition] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.composition_metrics: Dict[str, Dict[str, Any]] = {}
        self.event_bus: Optional[EventBus] = None
        self.logger = logging.getLogger(f"socrates.{self.service_name}")

    async def initialize(self) -> None:
        """Initialize the composer."""
        try:
            self.logger.info("SkillComposer initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize composer: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the composer."""
        try:
            self.compositions.clear()
            self.execution_history.clear()
            self.composition_metrics.clear()
            self.logger.info("SkillComposer shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during composer shutdown: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        return {
            "compositions_defined": len(self.compositions),
            "executions_recorded": len(self.execution_history),
            "compositions_with_metrics": len(self.composition_metrics),
        }

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the event bus."""
        self.event_bus = event_bus
        self.logger.debug("Event bus set for composer")

    async def create_composition(
        self,
        composition_id: str,
        name: str,
        skills: List[str],
        execution_type: str = "sequential",
    ) -> bool:
        """
        Create a new skill composition.

        Args:
            composition_id: Unique composition ID
            name: Human-readable name
            skills: List of skill IDs in order
            execution_type: sequential, parallel, or conditional

        Returns:
            True if successful
        """
        try:
            if composition_id in self.compositions:
                self.logger.warning(f"Composition {composition_id} already exists")
                return False

            composition = SkillComposition(composition_id, name, skills, execution_type)
            self.compositions[composition_id] = composition
            self.composition_metrics[composition_id] = {
                "executions": 0,
                "successes": 0,
                "failures": 0,
                "avg_duration": 0.0,
            }

            self.logger.info(f"Created composition {composition_id}: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Error creating composition: {e}")
            return False

    async def add_parameter_mapping(
        self,
        composition_id: str,
        from_skill_index: int,
        from_param: str,
        to_skill_index: int,
        to_param: str,
    ) -> bool:
        """Add parameter mapping between skills in composition."""
        try:
            if composition_id not in self.compositions:
                return False

            composition = self.compositions[composition_id]
            composition.add_parameter_mapping(
                from_skill_index, from_param, to_skill_index, to_param
            )
            self.logger.debug(f"Added parameter mapping in {composition_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding parameter mapping: {e}")
            return False

    async def add_condition(
        self,
        composition_id: str,
        skill_index: int,
        condition_type: str,
        condition_value: Any,
    ) -> bool:
        """Add execution condition for a skill."""
        try:
            if composition_id not in self.compositions:
                return False

            composition = self.compositions[composition_id]
            condition = {
                "type": condition_type,  # if_success, if_failure, custom
                "value": condition_value,
            }
            composition.add_condition(skill_index, condition)
            self.logger.debug(f"Added condition to {composition_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding condition: {e}")
            return False

    async def add_error_handler(
        self,
        composition_id: str,
        skill_id: str,
        handler: str,
    ) -> bool:
        """Add error handler for a skill."""
        try:
            if composition_id not in self.compositions:
                return False

            composition = self.compositions[composition_id]
            composition.add_error_handler(skill_id, handler)
            self.logger.debug(f"Added error handler for {skill_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding error handler: {e}")
            return False

    async def execute_composition(
        self,
        composition_id: str,
        initial_context: Dict[str, Any],
        skill_executor: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute a skill composition.

        Args:
            composition_id: ID of composition to execute
            initial_context: Initial input data
            skill_executor: Function to execute individual skills

        Returns:
            Execution result with outputs
        """
        try:
            if composition_id not in self.compositions:
                return {
                    "status": "error",
                    "error": f"Composition {composition_id} not found",
                }

            composition = self.compositions[composition_id]
            execution_id = f"exec_{composition_id}_{len(self.execution_history)}"
            start_time = datetime.utcnow()

            # Execute based on type
            if composition.execution_type == "sequential":
                result = await self._execute_sequential(
                    composition, initial_context, skill_executor
                )
            elif composition.execution_type == "parallel":
                result = await self._execute_parallel(
                    composition, initial_context, skill_executor
                )
            elif composition.execution_type == "conditional":
                result = await self._execute_conditional(
                    composition, initial_context, skill_executor
                )
            else:
                result = {"status": "error", "error": "Unknown execution type"}

            # Record execution
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            execution_record = {
                "execution_id": execution_id,
                "composition_id": composition_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": duration,
                "status": result.get("status", "unknown"),
                "result": result,
            }
            self.execution_history.append(execution_record)

            # Update metrics
            metrics = self.composition_metrics[composition_id]
            metrics["executions"] += 1
            if result.get("status") == "success":
                metrics["successes"] += 1
            else:
                metrics["failures"] += 1
            metrics["avg_duration"] = (
                (metrics["avg_duration"] * (metrics["executions"] - 1) + duration)
                / metrics["executions"]
            )

            # Publish event
            if self.event_bus:
                try:
                    await self.event_bus.publish(
                        "composition_executed",
                        self.service_name,
                        {
                            "composition_id": composition_id,
                            "execution_id": execution_id,
                            "status": result.get("status"),
                            "duration": duration,
                        },
                    )
                except Exception as e:
                    self.logger.error(f"Error publishing event: {e}")

            self.logger.info(
                f"Executed composition {composition_id} ({execution_id}) "
                f"in {duration:.2f}s with status {result.get('status')}"
            )
            return result
        except Exception as e:
            self.logger.error(f"Error executing composition: {e}")
            return {
                "status": "error",
                "error": str(e),
                "composition_id": composition_id,
            }

    async def _execute_sequential(
        self,
        composition: SkillComposition,
        initial_context: Dict[str, Any],
        skill_executor: Optional[Callable],
    ) -> Dict[str, Any]:
        """Execute skills sequentially."""
        try:
            context = initial_context.copy()
            results = {}

            for idx, skill_id in enumerate(composition.skills):
                # Check conditions
                if idx in composition.conditions:
                    condition = composition.conditions[idx]
                    if not self._evaluate_condition(condition, context):
                        self.logger.debug(f"Skipping skill {skill_id} due to condition")
                        continue

                # Execute skill
                if skill_executor:
                    try:
                        skill_result = await skill_executor(skill_id, context)
                        results[skill_id] = skill_result

                        # Map outputs to next skill inputs
                        for key, mapping in composition.parameter_mappings.items():
                            if key.startswith(f"{idx}_"):
                                param = key.split("_", 1)[1]
                                if param in skill_result:
                                    context[mapping["to_param"]] = skill_result[param]

                        if skill_result.get("status") != "success":
                            # Handle error
                            if skill_id in composition.error_handling:
                                handler = composition.error_handling[skill_id]
                                self.logger.warning(
                                    f"Skill {skill_id} failed, applying handler: {handler}"
                                )
                            else:
                                return {
                                    "status": "error",
                                    "failed_skill": skill_id,
                                    "error": skill_result.get("error"),
                                    "results": results,
                                }
                    except Exception as e:
                        return {
                            "status": "error",
                            "failed_skill": skill_id,
                            "error": str(e),
                            "results": results,
                        }
                else:
                    results[skill_id] = {"status": "skipped"}

            return {
                "status": "success",
                "composition_id": composition.composition_id,
                "results": results,
                "final_context": context,
            }
        except Exception as e:
            self.logger.error(f"Error in sequential execution: {e}")
            return {"status": "error", "error": str(e)}

    async def _execute_parallel(
        self,
        composition: SkillComposition,
        initial_context: Dict[str, Any],
        skill_executor: Optional[Callable],
    ) -> Dict[str, Any]:
        """Execute skills in parallel."""
        try:
            # For now, execute sequentially but return as parallel results
            # In production, would use asyncio.gather
            context = initial_context.copy()
            results = {}

            for skill_id in composition.skills:
                if skill_executor:
                    try:
                        skill_result = await skill_executor(skill_id, context)
                        results[skill_id] = skill_result
                    except Exception as e:
                        results[skill_id] = {"status": "error", "error": str(e)}
                else:
                    results[skill_id] = {"status": "skipped"}

            return {
                "status": "success",
                "composition_id": composition.composition_id,
                "execution_type": "parallel",
                "results": results,
            }
        except Exception as e:
            self.logger.error(f"Error in parallel execution: {e}")
            return {"status": "error", "error": str(e)}

    async def _execute_conditional(
        self,
        composition: SkillComposition,
        initial_context: Dict[str, Any],
        skill_executor: Optional[Callable],
    ) -> Dict[str, Any]:
        """Execute skills with conditional branching."""
        try:
            context = initial_context.copy()
            results = {}
            skip_next = False

            for idx, skill_id in enumerate(composition.skills):
                # Check conditions
                if idx in composition.conditions:
                    condition = composition.conditions[idx]
                    if not self._evaluate_condition(condition, context):
                        skip_next = True
                        continue

                if skip_next:
                    skip_next = False
                    continue

                if skill_executor:
                    try:
                        skill_result = await skill_executor(skill_id, context)
                        results[skill_id] = skill_result

                        if skill_result.get("status") != "success":
                            skip_next = True
                    except Exception as e:
                        results[skill_id] = {"status": "error", "error": str(e)}
                        skip_next = True
                else:
                    results[skill_id] = {"status": "skipped"}

            return {
                "status": "success",
                "composition_id": composition.composition_id,
                "execution_type": "conditional",
                "results": results,
                "final_context": context,
            }
        except Exception as e:
            self.logger.error(f"Error in conditional execution: {e}")
            return {"status": "error", "error": str(e)}

    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate an execution condition."""
        try:
            condition_type = condition.get("type")
            condition_value = condition.get("value")

            if condition_type == "if_success":
                return context.get(condition_value, False)
            elif condition_type == "custom":
                # For custom conditions, check context value
                return context.get(condition_value, False)
            else:
                return True
        except Exception as e:
            self.logger.error(f"Error evaluating condition: {e}")
            return False

    async def get_composition(self, composition_id: str) -> Optional[Dict[str, Any]]:
        """Get composition details."""
        try:
            if composition_id not in self.compositions:
                return None
            return self.compositions[composition_id].to_dict()
        except Exception as e:
            self.logger.error(f"Error getting composition: {e}")
            return None

    async def get_composition_metrics(self, composition_id: str) -> Optional[Dict[str, Any]]:
        """Get execution metrics for a composition."""
        try:
            if composition_id not in self.composition_metrics:
                return None
            return self.composition_metrics[composition_id].copy()
        except Exception as e:
            self.logger.error(f"Error getting metrics: {e}")
            return None

    async def get_execution_history(
        self,
        composition_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get execution history."""
        try:
            history = self.execution_history.copy()
            if composition_id:
                history = [h for h in history if h.get("composition_id") == composition_id]
            return history[-limit:]
        except Exception as e:
            self.logger.error(f"Error getting history: {e}")
            return []

    async def list_compositions(self) -> List[Dict[str, Any]]:
        """List all compositions."""
        try:
            return [c.to_dict() for c in self.compositions.values()]
        except Exception as e:
            self.logger.error(f"Error listing compositions: {e}")
            return []

    async def get_composition_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics across all compositions."""
        try:
            if not self.composition_metrics:
                return {}

            total_executions = sum(m["executions"] for m in self.composition_metrics.values())
            total_successes = sum(m["successes"] for m in self.composition_metrics.values())
            avg_duration = (
                sum(m["avg_duration"] for m in self.composition_metrics.values())
                / len(self.composition_metrics)
                if self.composition_metrics
                else 0
            )

            return {
                "total_compositions": len(self.compositions),
                "total_executions": total_executions,
                "total_successes": total_successes,
                "success_rate": total_successes / total_executions if total_executions > 0 else 0,
                "average_duration": avg_duration,
            }
        except Exception as e:
            self.logger.error(f"Error getting performance stats: {e}")
            return {}
