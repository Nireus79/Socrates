from socrates_ai import SocraticAgent, KnowledgeBase
from socrates_ai.rag import ChromaVectorStore


class QuestionEngine:
    def __init__(self, workspace_root: Path, model: str = "claude-opus-4-6"):
        self.workspace_root = workspace_root
        self.vectors_dir = workspace_root / ".socrates-vectors"
        self.kb_dir = workspace_root / ".socrates-kb"

        # Initialize socrates-ai components
        self.vector_store = ChromaVectorStore(
            path=str(self.vectors_dir),
            collection_name="socratic_discovery"
        )
        self.knowledge_base = KnowledgeBase(
            persist_directory=str(self.kb_dir)
        )
        self.agent = SocraticAgent(
            model=model,
            vector_db=self.vector_store,
            knowledge_base=self.knowledge_base
        )

    def get_first_question(self, topic: str) -> str:
        """Generate opening question for topic"""
        try:
            questions = self.agent.generate_questions(
                session=None,
                phase="discovery",
                context=f"Topic: {topic}",
                count=1
            )
            return questions[0] if questions else self._fallback_question(topic, "first")
        except Exception as e:
            print(f"Warning: {e}")
            return self._fallback_question(topic, "first")

    def get_next_question(self, topic: str, context: str, num_asked: int) -> str:
        """Generate follow-up question based on context"""
        try:
            questions = self.agent.generate_questions(
                session=None,
                phase="discovery",
                context=context,
                count=1
            )
            return questions[0] if questions else self._fallback_question(topic, "follow-up")
        except Exception as e:
            print(f"Warning: {e}")
            return self._fallback_question(topic, "follow-up")

    def _fallback_question(self, topic: str, qtype: str) -> str:
        """Fallback questions if generation fails"""
        fallbacks = {
            "first": [
                f"What problem does '{topic}' solve?",
                f"What's the main goal of '{topic}'?",
            ],
            "follow-up": [
                "Who is your target user?",
                "What are the key features?",
                "What constraints or limitations exist?",
                "How will you measure success?",
            ]
        }
        return fallbacks.get(qtype, ["Tell me more."])[0]
