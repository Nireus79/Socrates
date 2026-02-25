class StorageHandler:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.projects_dir = workspace_root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def save_project(self, project_name: str, artifacts: Dict) -> Path:
        """Save all project artifacts"""
        project_dir = self.projects_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        # Save each artifact
        for filename, content in artifacts.items():
            (project_dir / filename).write_text(content)

        # Save metadata
        metadata = {
            "name": project_name,
            "created_at": datetime.now().isoformat(),
            "artifacts": list(artifacts.keys())
        }
        (project_dir / ".metadata.json").write_text(json.dumps(metadata, indent=2))

        return project_dir

    def load_project(self, project_name: str) -> Dict:
        """Load project artifacts"""
        project_dir = self.projects_dir / project_name

        artifacts = {}
        for file in project_dir.glob("*.md"):
            artifacts[file.name] = file.read_text()

        return artifacts

    def list_projects(self) -> List[str]:
        """List all projects"""
        return [d.name for d in self.projects_dir.iterdir() if d.is_dir()]

    def export_project(self, project_name: str, format: str = "markdown") -> str:
        """Export project in different format"""
        artifacts = self.load_project(project_name)

        if format == "markdown":
            # Combine all markdown files
            combined = ""
            for name, content in artifacts.items():
                combined += f"\n\n---\n\n# {name}\n\n{content}"
            return combined
        elif format == "json":
            return json.dumps(artifacts, indent=2)
        else:
            raise ValueError(f"Unknown format: {format}")
        