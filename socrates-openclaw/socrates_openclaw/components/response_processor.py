class ResponseProcessor:
    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        self.MIN_RESPONSES = 4  # Need at least 4 responses before spec
        self.MAX_RESPONSES = 15  # Stop at 15 responses

    def process_response(self, session_id: str, response: str, question: str) -> Dict:
        """Process a user response"""
        # Validate
        if not self._validate(response):
            return {
                "status": "invalid",
                "message": "Response too short. Please provide more detail."
            }

        # Store in KB for RAG
        try:
            self.kb.add_entry(
                session_id,
                f"Q: {question}\nA: {response}",
                metadata={
                    "type": "discovery_response",
                    "session": session_id
                }
            )
        except Exception as e:
            print(f"KB error: {e}")

        # Return status
        return {
            "status": "processed",
            "stored": True
        }

    def should_generate_spec(self, session: Dict) -> bool:
        """Determine if we have enough info for spec"""
        num_responses = len(session.get("responses", []))

        # Need minimum responses
        if num_responses < self.MIN_RESPONSES:
            return False

        # Check if user asked for it
        if session.get("requested_spec"):
            return True

        # Auto-generate after max responses
        if num_responses >= self.MAX_RESPONSES:
            return True

        return False

    def _validate(self, response: str) -> bool:
        """Basic validation"""
        return len(response.strip()) > 5
