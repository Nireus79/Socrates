"""
Code generation agent for Socrates AI
"""

from pathlib import Path
from typing import Any, Dict

from socratic_system.models import ProjectContext
from socratic_system.utils.artifact_saver import ArtifactSaver
from socratic_system.utils.code_structure_analyzer import CodeStructureAnalyzer
from socratic_system.utils.multi_file_splitter import (
    MultiFileCodeSplitter,
    ProjectStructureGenerator,
)

from .base import Agent


class CodeGeneratorAgent(Agent):
    """Generates code and documentation based on project context"""

    def __init__(self, orchestrator):
        super().__init__("CodeGenerator", orchestrator)
        self.current_user = None

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process artifact generation requests"""
        action = request.get("action")

        if action == "generate_artifact":
            return self._generate_artifact(request)
        elif action == "generate_documentation":
            return self._generate_documentation(request)
        # Legacy support
        elif action == "generate_script":
            return self._generate_artifact(request)

        return {"status": "error", "message": "Unknown action"}

    def _generate_artifact(self, request: Dict) -> Dict:
        """Generate project-type-appropriate artifact"""
        project = request.get("project")

        # Build comprehensive context
        context = self._build_generation_context(project)

        # Generate artifact based on project type
        # Get user's auth method
        user_auth_method = "api_key"
        if self.current_user:
            user_obj = self.orchestrator.database.load_user(self.current_user)
            if user_obj and hasattr(user_obj, "claude_auth_method"):
                user_auth_method = user_obj.claude_auth_method or "api_key"
        artifact = self.orchestrator.claude_client.generate_artifact(
            context, project.project_type, user_auth_method, user_id=self.current_user
        )

        # Determine artifact type for documentation
        artifact_type_map = {
            "software": "code",
            "business": "business_plan",
            "research": "research_protocol",
            "creative": "creative_brief",
            "marketing": "marketing_plan",
            "educational": "curriculum",
        }
        artifact_type = artifact_type_map.get(project.project_type, "code")

        self.log(f"Generated {artifact_type} for {project.project_type} project '{project.name}'")

        # Auto-save artifact to disk with multi-file organization
        save_path = None
        project_root = None
        try:
            data_dir = Path(self.orchestrator.config.data_dir)

            # For code artifacts, split into multiple files
            if artifact_type == "code" and project.project_type == "software":
                self.log("Organizing code into multi-file structure...")

                # Analyze code structure
                analyzer = CodeStructureAnalyzer(artifact, language="python")
                analysis = analyzer.analyze()
                self.log(
                    f"Analyzed code: {analysis['class_count']} classes, "
                    f"{analysis['function_count']} functions"
                )

                # Split code into organized files
                splitter = MultiFileCodeSplitter(
                    artifact, language="python", project_type=project.project_type
                )
                file_structure = splitter.split()

                # Create complete project structure
                complete_structure = ProjectStructureGenerator.create_structure(
                    project.name, file_structure, project.project_type
                )

                # Save multi-file project
                success, project_root = ArtifactSaver.save_multi_file_project(
                    file_structure=complete_structure,
                    project_id=project.project_id,
                    project_name=project.name,
                    data_dir=data_dir,
                )

                if success:
                    save_path = project_root
                    file_count = len(complete_structure)
                    self.log(
                        f"Auto-saved {artifact_type} as multi-file project "
                        f"({file_count} files) to {save_path}"
                    )

                    # NEW: Also save files to database for knowledge base integration
                    self.log("Saving generated files to database...")
                    try:
                        from socratic_system.database.project_file_manager import ProjectFileManager

                        file_manager = ProjectFileManager(self.orchestrator.database.db_path)

                        # Prepare files for batch insert
                        files_to_save = []
                        for file_path, content in complete_structure.items():
                            language = self._detect_language(file_path)
                            files_to_save.append(
                                {
                                    "path": file_path,
                                    "content": content,
                                    "language": language,
                                    "size": len(content.encode("utf-8")),
                                }
                            )

                        # Save all files to database
                        if files_to_save:
                            files_saved, save_msg = file_manager.save_files_batch(
                                project.project_id, files_to_save
                            )
                            self.log(save_msg)
                        else:
                            self.log("No files to save to database")

                    except Exception as e:
                        self.log(f"WARNING: Failed to save generated files to database: {str(e)}")
                        # Don't fail artifact generation if database save fails

                else:
                    self.log(f"WARNING: Failed to auto-save {artifact_type}")

            else:
                # For non-code artifacts, save as single file
                success, save_path = ArtifactSaver.save_artifact(
                    artifact=artifact,
                    artifact_type=artifact_type,
                    project_id=project.project_id,
                    project_name=project.name,
                    data_dir=data_dir,
                    timestamp=True,
                )
                if success:
                    self.log(f"Auto-saved {artifact_type} to {save_path}")
                else:
                    self.log(f"WARNING: Failed to auto-save {artifact_type}")

        except Exception as e:
            self.log(f"WARNING: Error auto-saving artifact: {e}")

        return {
            "status": "success",
            "artifact": artifact,
            "artifact_type": artifact_type,
            "script": artifact,  # Legacy compatibility
            "context_used": context,
            "save_path": save_path,  # Include save path in response
            "is_multi_file": project_root is not None,  # Indicate if multi-file project
        }

    def _generate_documentation(self, request: Dict) -> Dict:
        """Generate documentation for project artifact"""
        project = request.get("project")
        artifact = request.get("artifact") or request.get("script")  # Support both

        if not project:
            return {"status": "error", "message": "Project is required"}

        # Determine artifact type
        artifact_type_map = {
            "software": "code",
            "business": "business_plan",
            "research": "research_protocol",
            "creative": "creative_brief",
            "marketing": "marketing_plan",
            "educational": "curriculum",
        }
        artifact_type = artifact_type_map.get(project.project_type, "code")

        # Log when artifact is missing (but still try to generate)
        if not artifact:
            self.log(f"WARNING: Generating {artifact_type} documentation without artifact")

        try:
            documentation = self.orchestrator.claude_client.generate_documentation(
                project, artifact, artifact_type
            )

            self.log(f"Generated documentation for {artifact_type}")

            # Auto-save documentation to disk
            save_path = None
            try:
                data_dir = Path(self.orchestrator.config.data_dir)
                success, save_path = ArtifactSaver.save_artifact(
                    artifact=documentation,
                    artifact_type="documentation",
                    project_id=project.project_id,
                    project_name=project.name,
                    data_dir=data_dir,
                    timestamp=True,
                )
                if success:
                    self.log(f"Auto-saved documentation to {save_path}")
                else:
                    self.log("WARNING: Failed to auto-save documentation")
            except Exception as save_err:
                self.log(f"WARNING: Error auto-saving documentation: {save_err}")

            return {
                "status": "success",
                "documentation": documentation,
                "save_path": save_path,  # Include save path in response
            }
        except Exception as e:
            self.log(f"ERROR: Failed to generate documentation: {e}")
            return {
                "status": "error",
                "message": f"Documentation generation failed: {str(e)}",
            }

    def _build_generation_context(self, project: ProjectContext) -> str:
        """Build comprehensive context for code generation"""
        context_parts = [
            f"Project: {project.name}",
            f"Phase: {project.phase}",
        ]

        # Add optional fields with safe defaults
        if project.goals:
            context_parts.append(f"Goals: {project.goals}")

        if project.tech_stack:
            context_parts.append(f"Tech Stack: {', '.join(project.tech_stack)}")

        if project.requirements:
            context_parts.append(f"Requirements: {', '.join(project.requirements)}")

        if project.constraints:
            context_parts.append(f"Constraints: {', '.join(project.constraints)}")

        if project.deployment_target:
            context_parts.append(f"Target: {project.deployment_target}")

        if project.code_style:
            context_parts.append(f"Style: {project.code_style}")

        # Add conversation insights
        if project.conversation_history:
            recent_responses = project.conversation_history[-5:]
            context_parts.append("Recent Discussion:")
            for msg in recent_responses:
                if msg.get("type") == "user":
                    context_parts.append(f"- {msg['content']}")

        return "\n".join(context_parts)

    def _detect_language(self, file_path: str) -> str:
        """
        Detect programming language from file extension.

        Args:
            file_path: Path to the file as string

        Returns:
            Language name or 'Unknown' if not recognized
        """
        ext_to_lang = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "JSX",
            ".tsx": "TSX",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".cs": "C#",
            ".rb": "Ruby",
            ".go": "Go",
            ".rs": "Rust",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".sh": "Shell",
            ".bash": "Bash",
            ".sql": "SQL",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".less": "Less",
            ".json": "JSON",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".xml": "XML",
            ".md": "Markdown",
            ".rst": "ReStructuredText",
            ".txt": "Text",
            ".toml": "TOML",
            ".ini": "INI",
            ".cfg": "Config",
        }

        file_ext = Path(file_path).suffix.lower()
        return ext_to_lang.get(file_ext, "Unknown")
