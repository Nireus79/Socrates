"""
Document processing for importing files into projects
"""

from typing import Dict, Any

from .base import Agent


class DocumentAgent(Agent):
    """Handles document import and processing"""

    def __init__(self, orchestrator):
        super().__init__("DocumentAgent", orchestrator)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process document import requests"""
        action = request.get('action')

        if action == 'import_file':
            return self._import_file(request)
        elif action == 'import_directory':
            return self._import_directory(request)
        elif action == 'list_documents':
            return self._list_documents(request)

        return {'status': 'error', 'message': 'Unknown action'}

    def _import_file(self, request: Dict) -> Dict:
        """Import a single file"""
        file_path = request.get('file_path')
        project_id = request.get('project_id')

        self.log(f"Importing file: {file_path}")

        return {
            'status': 'success',
            'file': file_path,
            'project_id': project_id,
            'imported': True
        }

    def _import_directory(self, request: Dict) -> Dict:
        """Import an entire directory"""
        directory_path = request.get('directory_path')
        project_id = request.get('project_id')
        recursive = request.get('recursive', True)

        self.log(f"Importing directory: {directory_path} (recursive={recursive})")

        return {
            'status': 'success',
            'directory': directory_path,
            'project_id': project_id,
            'recursive': recursive,
            'imported': True
        }

    def _list_documents(self, request: Dict) -> Dict:
        """List imported documents"""
        project_id = request.get('project_id')

        return {
            'status': 'success',
            'project_id': project_id,
            'documents': []
        }
