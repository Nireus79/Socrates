"""Note manager agent for handling project notes"""

from typing import Dict, Any
from socratic_system.agents.base import Agent
from socratic_system.models import ProjectNote


class NoteManagerAgent(Agent):
    """Agent for managing project notes"""

    def __init__(self, name: str, orchestrator: 'AgentOrchestrator'):
        """Initialize note manager agent"""
        super().__init__(name, orchestrator)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process note-related requests.

        Supported actions:
        - add_note: Add a new note to a project
        - list_notes: List notes for a project
        - search_notes: Search notes by content
        - delete_note: Delete a note by ID
        """
        action = request.get('action')

        if action == 'add_note':
            return self._add_note(request)
        elif action == 'list_notes':
            return self._list_notes(request)
        elif action == 'search_notes':
            return self._search_notes(request)
        elif action == 'delete_note':
            return self._delete_note(request)
        else:
            return {'status': 'error', 'message': f'Unknown action: {action}'}

    def _add_note(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new note to a project"""
        try:
            project_id = request.get('project_id')
            note_type = request.get('note_type')  # design, bug, idea, task, general
            title = request.get('title')
            content = request.get('content')
            created_by = request.get('created_by')
            tags = request.get('tags', [])

            if not all([project_id, note_type, title, content, created_by]):
                return {'status': 'error', 'message': 'Missing required fields'}

            # Validate note type
            valid_types = ['design', 'bug', 'idea', 'task', 'general']
            if note_type not in valid_types:
                return {'status': 'error', 'message': f'Invalid note type. Must be one of: {", ".join(valid_types)}'}

            # Create note
            note = ProjectNote.create(
                project_id=project_id,
                note_type=note_type,
                title=title,
                content=content,
                created_by=created_by,
                tags=tags
            )

            # Save to database
            if self.orchestrator.database.save_note(note):
                self.log(f'Note "{title}" added to project {project_id}')
                return {
                    'status': 'success',
                    'message': f'Note "{title}" added successfully',
                    'note': {
                        'note_id': note.note_id,
                        'title': note.title,
                        'type': note.note_type,
                        'created_at': note.created_at.isoformat()
                    }
                }
            else:
                return {'status': 'error', 'message': 'Failed to save note to database'}

        except Exception as e:
            self.log(f'Error adding note: {str(e)}', level='ERROR')
            return {'status': 'error', 'message': f'Error adding note: {str(e)}'}

    def _list_notes(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """List notes for a project"""
        try:
            project_id = request.get('project_id')
            note_type = request.get('note_type')  # Optional filter

            if not project_id:
                return {'status': 'error', 'message': 'project_id required'}

            # Get notes from database
            notes = self.orchestrator.database.get_project_notes(project_id, note_type)

            # Format for output
            notes_data = []
            for note in notes:
                notes_data.append({
                    'note_id': note.note_id,
                    'title': note.title,
                    'type': note.note_type,
                    'created_by': note.created_by,
                    'created_at': note.created_at.isoformat(),
                    'tags': note.tags,
                    'preview': note.content[:100] + ('...' if len(note.content) > 100 else '')
                })

            self.log(f'Retrieved {len(notes_data)} notes for project {project_id}')
            return {
                'status': 'success',
                'notes': notes_data,
                'count': len(notes_data)
            }

        except Exception as e:
            self.log(f'Error listing notes: {str(e)}', level='ERROR')
            return {'status': 'error', 'message': f'Error listing notes: {str(e)}'}

    def _search_notes(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Search notes by content"""
        try:
            project_id = request.get('project_id')
            query = request.get('query')

            if not project_id or not query:
                return {'status': 'error', 'message': 'project_id and query required'}

            # Search notes in database
            notes = self.orchestrator.database.search_notes(project_id, query)

            # Format for output
            notes_data = []
            for note in notes:
                notes_data.append({
                    'note_id': note.note_id,
                    'title': note.title,
                    'type': note.note_type,
                    'created_by': note.created_by,
                    'created_at': note.created_at.isoformat(),
                    'tags': note.tags,
                    'preview': note.content[:100] + ('...' if len(note.content) > 100 else '')
                })

            self.log(f'Found {len(notes_data)} notes matching "{query}" in project {project_id}')
            return {
                'status': 'success',
                'results': notes_data,
                'count': len(notes_data),
                'query': query
            }

        except Exception as e:
            self.log(f'Error searching notes: {str(e)}', level='ERROR')
            return {'status': 'error', 'message': f'Error searching notes: {str(e)}'}

    def _delete_note(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a note by ID"""
        try:
            note_id = request.get('note_id')
            project_id = request.get('project_id')  # Optional, for validation

            if not note_id:
                return {'status': 'error', 'message': 'note_id required'}

            # Delete from database
            if self.orchestrator.database.delete_note(note_id):
                self.log(f'Note {note_id} deleted')
                return {'status': 'success', 'message': f'Note deleted successfully'}
            else:
                return {'status': 'error', 'message': 'Failed to delete note'}

        except Exception as e:
            self.log(f'Error deleting note: {str(e)}', level='ERROR')
            return {'status': 'error', 'message': f'Error deleting note: {str(e)}'}
