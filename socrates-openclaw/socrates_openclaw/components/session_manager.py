import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List


class SessionManager:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.sessions_file = workspace_root / ".socratic-sessions.json"
        self.projects_dir = workspace_root / "projects"
        self.sessions = self._load_sessions()

    def create_session(self, topic: str) -> str:
        """Create new discovery session"""
        session_id = f"discover_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        self.sessions[session_id] = {
            "topic": topic,
            "created_at": datetime.now().isoformat(),
            "questions": [],
            "responses": [],
            "phase": "discovery",
            "status": "active"
        }
        self.save()
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        return self.sessions.get(session_id)

    def add_response(self, session_id: str, question: str, response: str):
        """Record question and response"""
        if session_id in self.sessions:
            self.sessions[session_id]["questions"].append(question)
            self.sessions[session_id]["responses"].append(response)
            self.save()

    def save(self):
        """Save sessions to disk"""
        with open(self.sessions_file, "w") as f:
            json.dump(self.sessions, f, indent=2, default=str)

    def _load_sessions(self) -> Dict:
        """Load sessions from disk"""
        if self.sessions_file.exists():
            with open(self.sessions_file) as f:
                return json.load(f)
        return {}
