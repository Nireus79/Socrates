"""
User Learning Agent - Background learning and personalization.

This agent orchestrates user behavior learning and question personalization:
1. Tracks question effectiveness from user responses
2. Learns behavior patterns over time
3. Recommends next questions based on learned data
4. Manages knowledge base documents
5. Builds comprehensive user learning profiles

Architecture:
- Agent handles: Database I/O, API orchestration, validation
- LearningEngine handles: Behavior analysis, metrics calculation, personalization
- Clear separation enables testing without database
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict

from socratic_system.agents.base import Agent
from socratic_system.core.learning_engine import LearningEngine
from socratic_system.models import KnowledgeBaseDocument, QuestionEffectiveness, UserBehaviorPattern


class UserLearningAgent(Agent):
    """
    User Learning Agent - learns and adapts to user behavior.

    Capabilities:
    - track_question_effectiveness: Track how effective questions are for each user
    - learn_behavior_pattern: Learn or update user behavior patterns
    - recommend_next_question: Recommend best question based on learned data
    - upload_knowledge_document: Upload and process knowledge base documents
    - get_user_profile: Get complete user learning profile

    Architecture:
    - This agent handles: Database I/O, API orchestration, validation, persistence
    - LearningEngine handles: Behavior analysis, metrics calculation, personalization
    - Clear separation enables testing without database and library extraction
    """

    def __init__(self, orchestrator):
        """Initialize agent with learning engine"""
        super().__init__("User Learning", orchestrator)
        self.learning_engine = LearningEngine(self.logger)
        self.logger.info("UserLearningAgent initialized")

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process learning-related requests.

        Args:
            request: Dict with 'action' key specifying the operation

        Returns:
            Dict with 'status' and operation-specific data
        """
        action = request.get("action")

        action_handlers = {
            "track_question_effectiveness": self._track_question_effectiveness,
            "learn_behavior_pattern": self._learn_behavior_pattern,
            "recommend_next_question": self._recommend_next_question,
            "upload_knowledge_document": self._upload_knowledge_document,
            "get_user_profile": self._get_user_profile,
        }

        handler = action_handlers.get(action)
        if handler:
            try:
                return handler(request)
            except Exception as e:
                self.logger.error(f"Error in {action}: {str(e)}", exc_info=True)
                return {"status": "error", "message": f"Failed to {action}: {str(e)}"}

        return {"status": "error", "message": f"Unknown action: {action}"}

    # ============================================================================
    # Core Actions
    # ============================================================================

    def _track_question_effectiveness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track how effective a question was for the user.

        Args:
            data: {
                'user_id': str,
                'question_template_id': str,
                'role': str (PM, BA, UX, etc.),
                'answer_length': int,
                'specs_extracted': int,
                'answer_quality': float (0-1)
            }

        Returns:
            {'status': 'success', 'effectiveness_score': float, ...}
        """
        user_id = data.get("user_id")
        question_template_id = data.get("question_template_id")
        role = data.get("role", "general")

        if not user_id or not question_template_id:
            return {"status": "error", "message": "user_id and question_template_id required"}

        self.logger.debug(
            f"Tracking effectiveness: user={user_id}, question={question_template_id}"
        )

        try:
            # Get or create effectiveness record
            effectiveness = self.orchestrator.database.get_question_effectiveness(
                user_id, question_template_id
            )

            if not effectiveness:
                effectiveness = QuestionEffectiveness(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    question_template_id=question_template_id,
                    role=role,
                    times_asked=0,
                    times_answered_well=0,
                    average_answer_length=0,
                    average_spec_extraction_count=Decimal("0.0"),
                    effectiveness_score=Decimal("0.5"),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )

            # Update metrics
            effectiveness.times_asked += 1
            self.logger.debug(f"Times asked incremented to {effectiveness.times_asked}")

            # Determine if answered well
            answer_quality = float(data.get("answer_quality", 0.5))
            specs_extracted = int(data.get("specs_extracted", 0))
            answered_well = specs_extracted > 0 and answer_quality > 0.6

            self.logger.debug(
                f"Answer evaluation: quality={answer_quality:.2f}, "
                f"specs={specs_extracted}, answered_well={answered_well}"
            )

            if answered_well:
                effectiveness.times_answered_well += 1
                self.logger.debug(
                    f"Good answer recorded, total well-answered: {effectiveness.times_answered_well}"
                )

            # Update averages (exponential moving average, alpha=0.3)
            alpha = 0.3
            answer_length = int(data.get("answer_length", 0))
            effectiveness.average_answer_length = int(
                alpha * answer_length + (1 - alpha) * (effectiveness.average_answer_length or 0)
            )

            effectiveness.average_spec_extraction_count = Decimal(
                str(
                    alpha * specs_extracted
                    + (1 - alpha) * float(effectiveness.average_spec_extraction_count)
                )
            )

            # Calculate effectiveness score
            if effectiveness.times_asked > 0:
                effectiveness.effectiveness_score = Decimal(
                    str(effectiveness.times_answered_well / effectiveness.times_asked)
                )
                self.logger.debug(
                    f"Effectiveness score calculated: "
                    f"{effectiveness.effectiveness_score} "
                    f"(well={effectiveness.times_answered_well}, asked={effectiveness.times_asked})"
                )
            else:
                effectiveness.effectiveness_score = Decimal("0.5")
                self.logger.debug("No questions asked yet, using default score 0.5")

            effectiveness.last_asked_at = datetime.now(timezone.utc)
            effectiveness.updated_at = datetime.now(timezone.utc)

            # Persist
            success = self.orchestrator.database.save_question_effectiveness(effectiveness)
            if success:
                self.logger.info(
                    f"Successfully tracked question effectiveness: "
                    f"user={user_id}, question={question_template_id}, "
                    f"score={float(effectiveness.effectiveness_score):.2f}, "
                    f"asked={effectiveness.times_asked}, "
                    f"well_answered={effectiveness.times_answered_well}"
                )
            else:
                self.logger.error(
                    f"Failed to persist effectiveness record for "
                    f"user={user_id}, question={question_template_id}"
                )

            # Emit event
            self.emit_event(
                "LEARNING_METRICS_UPDATED",
                {
                    "user_id": user_id,
                    "question_id": question_template_id,
                    "effectiveness_score": float(effectiveness.effectiveness_score),
                    "times_asked": effectiveness.times_asked,
                    "times_answered_well": effectiveness.times_answered_well,
                },
            )

            return {
                "status": "success",
                "effectiveness_score": float(effectiveness.effectiveness_score),
                "times_asked": effectiveness.times_asked,
                "times_answered_well": effectiveness.times_answered_well,
            }

        except Exception as e:
            self.logger.error(f"Error tracking effectiveness: {e}")
            return {"status": "error", "message": str(e)}

    def _learn_behavior_pattern(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Learn or update user behavior pattern.

        Args:
            data: {
                'user_id': str,
                'pattern_type': str (communication_style, detail_level, etc.),
                'pattern_data': dict,
                'confidence': float (0-1),
                'project_id': str
            }

        Returns:
            {'status': 'success', 'pattern_id': str, 'confidence': float}
        """
        user_id = data.get("user_id")
        pattern_type = data.get("pattern_type")
        pattern_data = data.get("pattern_data", {})
        confidence = float(data.get("confidence", 0.5))
        project_id = data.get("project_id")

        if not user_id or not pattern_type:
            return {"status": "error", "message": "user_id and pattern_type required"}

        self.logger.debug(
            f"Learning pattern: user={user_id}, type={pattern_type}, " f"confidence={confidence}"
        )

        try:
            # Get or create pattern
            pattern = self.orchestrator.database.get_behavior_pattern(user_id, pattern_type)

            if pattern:
                self.logger.debug(f"Updating existing pattern: {pattern_type} for user {user_id}")
                # Update existing pattern
                old_confidence = float(pattern.confidence or 0.5)
                pattern.pattern_data = self._merge_pattern_data(
                    pattern.pattern_data or {}, pattern_data
                )
                self.logger.debug(f"Pattern data merged, new keys: {list(pattern_data.keys())}")

                # Increase confidence gradually
                pattern.confidence = Decimal(str(min(1.0, float(pattern.confidence or 0.5) + 0.1)))
                new_confidence = float(pattern.confidence)
                self.logger.debug(
                    f"Confidence increased: {old_confidence:.2f} -> {new_confidence:.2f}"
                )

                # Add project to learned_from list
                current_projects = pattern.learned_from_projects or []
                if project_id and project_id not in current_projects:
                    pattern.learned_from_projects = current_projects + [project_id]
                    self.logger.debug(f"Added project {project_id} to pattern's project list")

                pattern.updated_at = datetime.now(timezone.utc)
            else:
                # Create new pattern
                self.logger.debug(f"Creating new pattern: {pattern_type} for user {user_id}")
                pattern = UserBehaviorPattern(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    pattern_type=pattern_type,
                    pattern_data=pattern_data,
                    confidence=Decimal(str(confidence)),
                    learned_from_projects=[project_id] if project_id else [],
                    learned_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                self.logger.debug(f"New pattern created with ID: {pattern.id}")

            # Persist
            success = self.orchestrator.database.save_behavior_pattern(pattern)
            if success:
                self.logger.info(
                    f"Successfully learned pattern: type={pattern_type}, user={user_id}, "
                    f"confidence={float(pattern.confidence):.2f}, projects={len(pattern.learned_from_projects)}"
                )
            else:
                self.logger.error(f"Failed to persist pattern: {pattern_type} for user {user_id}")

            return {
                "status": "success",
                "pattern_id": pattern.id,
                "confidence": float(pattern.confidence),
            }

        except Exception as e:
            self.logger.error(f"Error learning pattern: {e}")
            return {"status": "error", "message": str(e)}

    def _recommend_next_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend next question based on user learning.

        Args:
            data: {
                'user_id': str,
                'project_id': str,
                'available_questions': List[dict]
            }

        Returns:
            {
                'status': 'success|error',
                'recommended_question': dict (optional),
                'effectiveness_score': float (optional),
                'reason': str
            }
        """
        user_id = data.get("user_id")
        available_questions = data.get("available_questions", [])

        if not user_id:
            return {"status": "error", "message": "user_id required"}

        self.logger.debug(
            f"Recommending question for user {user_id} " f"({len(available_questions)} options)"
        )

        try:
            # Load user's question effectiveness data
            effectiveness_records = self.orchestrator.database.get_user_effectiveness_all(user_id)

            # Score each available question
            scored_questions = []
            for question in available_questions:
                template_id = question.get("id") or question.get("template_id")

                # Find effectiveness record
                effectiveness = next(
                    (e for e in effectiveness_records if e.question_template_id == template_id),
                    None,
                )

                if effectiveness:
                    score = float(effectiveness.effectiveness_score or 0.5)
                    times_asked = effectiveness.times_asked
                else:
                    score = 0.5  # Neutral for unknown questions
                    times_asked = 0

                scored_questions.append(
                    {"question": question, "score": score, "times_asked": times_asked}
                )

            # Sort by score (descending)
            scored_questions.sort(key=lambda x: x["score"], reverse=True)

            if scored_questions:
                best = scored_questions[0]
                self.logger.info(
                    f"Recommended question: {best['question'].get('id')}, "
                    f"score={best['score']:.2f}"
                )

                return {
                    "status": "success",
                    "recommended_question": best["question"],
                    "effectiveness_score": best["score"],
                    "reason": (
                        f"This question has {best['score']:.0%} effectiveness "
                        f"based on {best['times_asked']} previous interactions"
                    ),
                }

            return {
                "status": "success",
                "recommended_question": None,
                "reason": "No learning data yet, use default selection",
            }

        except Exception as e:
            self.logger.error(f"Error recommending question: {e}")
            return {"status": "error", "message": str(e)}

    def _upload_knowledge_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload and process knowledge base document.

        Args:
            data: {
                'project_id': str,
                'user_id': str,
                'filename': str,
                'content': str,
                'content_type': str,
                'file_size': int
            }

        Returns:
            {'status': 'success', 'document_id': str, 'filename': str, 'file_size': int}
        """
        project_id = data.get("project_id")
        user_id = data.get("user_id")
        filename = data.get("filename")
        content = data.get("content", "")
        content_type = data.get("content_type")
        file_size = int(data.get("file_size", 0))

        if not all([project_id, user_id, filename]):
            return {"status": "error", "message": "project_id, user_id, and filename required"}

        self.logger.debug(f"Uploading document: {filename} ({file_size} bytes)")

        try:
            # Create knowledge base document
            doc = KnowledgeBaseDocument(
                id=str(uuid.uuid4()),
                project_id=project_id,
                user_id=user_id,
                filename=filename,
                file_size=file_size,
                content_type=content_type,
                content=content,
                embedding=None,  # TODO: Generate embedding using sentence transformer
                uploaded_at=datetime.now(timezone.utc),
            )

            # Persist
            self.orchestrator.database.save_knowledge_document(doc)

            self.logger.info(f"Uploaded document: {doc.id}")

            return {
                "status": "success",
                "document_id": doc.id,
                "filename": filename,
                "file_size": file_size,
            }

        except Exception as e:
            self.logger.error(f"Error uploading document: {e}")
            return {"status": "error", "message": str(e)}

    def _get_user_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get complete user learning profile.

        Args:
            data: {'user_id': str}

        Returns:
            {
                'status': 'success',
                'user_id': str,
                'behavior_patterns': List[dict],
                'question_effectiveness': List[dict],
                'total_questions_asked': int,
                'overall_response_quality': float,
                'engagement_score': float,
                'learning_velocity': float,
                'experience_level': str,
                'topics_explored': int,
                'personalization_hints': dict
            }
        """
        user_id = data.get("user_id")

        if not user_id:
            return {"status": "error", "message": "user_id required"}

        self.logger.debug(f"Building profile for user {user_id}")

        try:
            # PHASE 1: Load data from database
            self.logger.debug(f"PHASE 1: Loading data for user {user_id} from database")
            patterns = self.orchestrator.database.get_user_behavior_patterns(user_id)
            effectiveness = self.orchestrator.database.get_user_effectiveness_all(user_id)
            self.logger.debug(
                f"Loaded {len(patterns)} behavior patterns and {len(effectiveness)} effectiveness records"
            )

            # PHASE 2: Convert to plain data models
            self.logger.debug("PHASE 2: Converting database data to plain data models")
            questions_asked = [
                {
                    "id": e.question_template_id,
                    "times_asked": e.times_asked,
                    "times_answered_well": e.times_answered_well,
                }
                for e in effectiveness
            ]

            response_qualities = [float(e.effectiveness_score or 0.5) for e in effectiveness]

            topic_interactions = [p.pattern_type for p in patterns] if patterns else []

            projects_completed = len(
                {
                    pid
                    for p in patterns
                    if p.learned_from_projects
                    for pid in p.learned_from_projects
                }
            )

            self.logger.debug(
                f"Converted data: questions={len(questions_asked)}, "
                f"topics={len(topic_interactions)}, projects={projects_completed}"
            )

            # PHASE 3: Use LearningEngine for pure business logic
            self.logger.debug("PHASE 3: Building profile using LearningEngine")
            user_behavior = self.learning_engine.build_user_profile(
                user_id=user_id,
                questions_asked=questions_asked,
                responses_quality=response_qualities,
                topic_interactions=topic_interactions,
                projects_completed=projects_completed,
            )
            self.logger.debug(
                f"Profile built: total_questions={user_behavior.total_questions_asked}"
            )

            # Calculate metrics
            self.logger.debug(f"Calculating learning metrics for user {user_id}")
            metrics = self.learning_engine.calculate_learning_metrics(user_behavior)

            # Get personalization hints
            self.logger.debug(f"Generating personalization hints for user {user_id}")
            hints = self.learning_engine.get_personalization_hints(user_behavior)

            self.logger.info(
                f"Successfully built user profile for {user_id}: "
                f"engagement={metrics['engagement_score']}, "
                f"velocity={metrics['learning_velocity']}, "
                f"level={metrics['experience_level']}, "
                f"questions={user_behavior.total_questions_asked}, "
                f"topics={user_behavior.topics_explored}"
            )

            return {
                "status": "success",
                "user_id": user_id,
                "behavior_patterns": [p.to_dict() for p in patterns],
                "question_effectiveness": [e.to_dict() for e in effectiveness],
                "total_questions_asked": user_behavior.total_questions_asked,
                "overall_response_quality": user_behavior.overall_response_quality,
                "engagement_score": metrics["engagement_score"],
                "learning_velocity": metrics["learning_velocity"],
                "experience_level": metrics["experience_level"],
                "topics_explored": metrics["topics_explored"],
                "personalization_hints": hints,
            }

        except Exception as e:
            self.logger.error(f"Error building profile: {e}")
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # Helpers
    # ============================================================================

    def _merge_pattern_data(self, existing: dict, new: dict) -> dict:
        """Merge new pattern data with existing."""
        merged = existing.copy()
        merged.update(new)
        return merged

    def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Emit learning event for other agents to listen to.

        Args:
            event_type: Type of event
            data: Event data
        """
        if not data.get("agent"):
            data["agent"] = self.name

        try:
            self.orchestrator.event_emitter.emit(event_type, data)
        except Exception as e:
            self.logger.debug(f"Could not emit event {event_type}: {e}")
