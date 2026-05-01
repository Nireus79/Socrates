"""Background event handlers for Phase 3 non-blocking processing.

Implements async background processing for quality, conflict, and insight analysis.
Handlers are triggered by events and run non-blocking in the background.
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class BackgroundHandlers:
    """Background event handlers for async processing.

    Listens for response events and triggers background analysis
    for quality, conflicts, and insights. Results are cached for
    client polling.
    """

    def __init__(self, orchestrator, cache, job_tracker, websocket_broadcaster=None):
        """Initialize background handlers.

        Args:
            orchestrator: AgentOrchestrator instance
            cache: AnalysisCache instance for storing results
            job_tracker: JobTracker instance for tracking jobs
            websocket_broadcaster: Optional function to broadcast WebSocket updates
        """
        self.orchestrator = orchestrator
        self.cache = cache
        self.job_tracker = job_tracker
        self.websocket_broadcaster = websocket_broadcaster
        self._register_handlers()
        logger.info("BackgroundHandlers initialized")

    def _register_handlers(self):
        """Register all background event handlers with event emitter"""
        # Register response handling
        self.orchestrator.event_emitter.on(
            "response.received",
            self._on_response_received
        )

        # Register quality analysis
        self.orchestrator.event_emitter.on(
            "quality.analysis.requested",
            self._on_quality_analysis_requested
        )

        # Register conflict analysis
        self.orchestrator.event_emitter.on(
            "conflict.analysis.requested",
            self._on_conflict_analysis_requested
        )

        logger.debug("Background event handlers registered")

    async def _on_response_received(self, data: Dict[str, Any]):
        """Background processing when response is received.

        Triggered by response.received event. Schedules background tasks
        without blocking the main response path.

        Args:
            data: Event data containing project_id and response content
        """
        project_id = data.get("project_id")

        if not project_id:
            logger.warning("response.received event missing project_id")
            return

        logger.info(f"[BACKGROUND] Processing response for project {project_id}")

        # Schedule background tasks (fire and forget)
        asyncio.create_task(self._process_quality_async(project_id))
        asyncio.create_task(self._process_conflicts_async(project_id))
        asyncio.create_task(self._process_insights_async(project_id))

    async def _on_quality_analysis_requested(self, data: Dict[str, Any]):
        """Handle explicit quality analysis request.

        Args:
            data: Event data containing project_id
        """
        project_id = data.get("project_id")
        if project_id:
            await self._process_quality_async(project_id)

    async def _on_conflict_analysis_requested(self, data: Dict[str, Any]):
        """Handle explicit conflict analysis request.

        Args:
            data: Event data containing project_id
        """
        project_id = data.get("project_id")
        if project_id:
            await self._process_conflicts_async(project_id)

    async def _process_quality_async(self, project_id: str):
        """Non-blocking quality analysis in background.

        Calls quality controller asynchronously via thread pool,
        caches results, and emits completion events.

        Args:
            project_id: Project identifier
        """
        try:
            logger.debug(f"[BACKGROUND] Starting quality analysis for {project_id}")

            # Load project
            project = await asyncio.to_thread(
                self.orchestrator.database.load_project,
                project_id
            )

            if not project:
                logger.warning(f"[BACKGROUND] Project not found: {project_id}")
                return

            # Call quality controller in thread pool (non-blocking)
            quality_result = await asyncio.to_thread(
                self.orchestrator.quality_controller.process,
                {
                    "action": "get_phase_maturity",
                    "project": project
                }
            )

            # Cache result for polling
            cache_key = f"analysis:quality:{project_id}"
            self.cache.set(cache_key, quality_result)

            # Emit completion event
            self.orchestrator.event_emitter.emit(
                "quality.analysis.completed",
                {
                    "project_id": project_id,
                    "result": quality_result,
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Broadcast WebSocket update if available
            if self.websocket_broadcaster:
                try:
                    await self.websocket_broadcaster(
                        project_id, "quality", quality_result
                    )
                except Exception as e:
                    logger.warning(f"[BACKGROUND] WebSocket broadcast failed: {e}")

            logger.info(f"[BACKGROUND] Quality analysis completed for {project_id}")

        except Exception as e:
            logger.error(
                f"[BACKGROUND] Quality analysis failed for {project_id}: {str(e)}"
            )

            # Emit failure event
            self.orchestrator.event_emitter.emit(
                "quality.analysis.failed",
                {
                    "project_id": project_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )

    async def _process_conflicts_async(self, project_id: str):
        """Non-blocking conflict analysis in background.

        Calls conflict detector asynchronously via thread pool,
        caches results, and emits completion events.

        Args:
            project_id: Project identifier
        """
        try:
            logger.debug(f"[BACKGROUND] Starting conflict analysis for {project_id}")

            # Load project
            project = await asyncio.to_thread(
                self.orchestrator.database.load_project,
                project_id
            )

            if not project:
                logger.warning(f"[BACKGROUND] Project not found: {project_id}")
                return

            # Call conflict detector in thread pool (non-blocking)
            conflicts_result = await asyncio.to_thread(
                self.orchestrator.conflict_detector.process,
                {
                    "action": "detect_conflicts",
                    "project": project
                }
            )

            # Cache result for polling
            cache_key = f"analysis:conflicts:{project_id}"
            self.cache.set(cache_key, conflicts_result)

            # Emit completion event
            self.orchestrator.event_emitter.emit(
                "conflict.analysis.completed",
                {
                    "project_id": project_id,
                    "result": conflicts_result,
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Broadcast WebSocket update if available
            if self.websocket_broadcaster:
                try:
                    await self.websocket_broadcaster(
                        project_id, "conflicts", conflicts_result
                    )
                except Exception as e:
                    logger.warning(f"[BACKGROUND] WebSocket broadcast failed: {e}")

            logger.info(f"[BACKGROUND] Conflict analysis completed for {project_id}")

        except Exception as e:
            logger.error(
                f"[BACKGROUND] Conflict analysis failed for {project_id}: {str(e)}"
            )

            # Emit failure event
            self.orchestrator.event_emitter.emit(
                "conflict.analysis.failed",
                {
                    "project_id": project_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )

    async def _process_insights_async(self, project_id: str):
        """Non-blocking insight extraction in background.

        Calls context analyzer asynchronously via thread pool,
        caches results, and emits completion events.

        Args:
            project_id: Project identifier
        """
        try:
            logger.debug(f"[BACKGROUND] Starting insight analysis for {project_id}")

            # Load project
            project = await asyncio.to_thread(
                self.orchestrator.database.load_project,
                project_id
            )

            if not project:
                logger.warning(f"[BACKGROUND] Project not found: {project_id}")
                return

            # Call context analyzer in thread pool (non-blocking)
            insights_result = await asyncio.to_thread(
                self.orchestrator.context_analyzer.process,
                {
                    "action": "analyze_context",
                    "project": project
                }
            )

            # Cache result for polling
            cache_key = f"analysis:insights:{project_id}"
            self.cache.set(cache_key, insights_result)

            # Emit completion event
            self.orchestrator.event_emitter.emit(
                "insights.analysis.completed",
                {
                    "project_id": project_id,
                    "result": insights_result,
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Broadcast WebSocket update if available
            if self.websocket_broadcaster:
                try:
                    await self.websocket_broadcaster(
                        project_id, "insights", insights_result
                    )
                except Exception as e:
                    logger.warning(f"[BACKGROUND] WebSocket broadcast failed: {e}")

            logger.info(f"[BACKGROUND] Insight analysis completed for {project_id}")

        except Exception as e:
            logger.error(
                f"[BACKGROUND] Insight analysis failed for {project_id}: {str(e)}"
            )

            # Emit failure event
            self.orchestrator.event_emitter.emit(
                "insights.analysis.failed",
                {
                    "project_id": project_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
