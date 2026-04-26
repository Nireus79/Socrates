"""Documentation generation and code extraction - imported from socratic-docs library."""

from socratic_docs import (
    DocumentationGenerator,
    CodeExtractor,
    ArtifactSaver,
    ProjectTemplateGenerator,
    MultiFileCodeSplitter,
    GitInitializer,
)

# ProjectStructureGenerator is still in local utils - import from there
from socratic_system.utils.multi_file_splitter import ProjectStructureGenerator

__all__ = [
    "DocumentationGenerator",
    "CodeExtractor",
    "ArtifactSaver",
    "ProjectTemplateGenerator",
    "MultiFileCodeSplitter",
    "GitInitializer",
    "ProjectStructureGenerator",
]
