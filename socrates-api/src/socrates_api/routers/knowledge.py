"""
Knowledge Base Management API endpoints for Socrates.

Provides document import, search, and knowledge management functionality.
"""

import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, status, Depends, Body, Form

from socratic_system.database import ProjectDatabaseV2
from socrates_api.models import SuccessResponse, ErrorResponse
from socrates_api.auth import get_current_user
from socrates_api.database import get_database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _get_orchestrator():
    """Get the global orchestrator instance for agent-based processing."""
    from socrates_api.main import app_state

    if app_state.get("orchestrator") is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Orchestrator not initialized. Please call /initialize first."
        )
    return app_state["orchestrator"]


@router.get(
    "/documents",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="List documents",
    responses={
        200: {"description": "Documents retrieved"},
        400: {"description": "Invalid project ID", "model": ErrorResponse},
    },
)
async def list_documents(
    project_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    List knowledge base documents.

    Args:
        project_id: Optional project ID to filter documents
        current_user: Current authenticated user
        db: Database connection

    Returns:
        SuccessResponse with list of documents
    """
    try:
        if project_id:
            # Verify user has access to project
            project = db.load_project(project_id)
            if not project or project.owner != current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this project"
                )
            documents = db.get_project_knowledge_documents(project_id)
        else:
            # Get all documents for user
            documents = db.get_user_knowledge_documents(current_user)

        # Transform to frontend format
        doc_list = []
        for doc in documents:
            doc_list.append({
                "id": doc["id"],
                "title": doc["title"],
                "source_type": doc["document_type"],
                "created_at": doc["uploaded_at"],
                "chunk_count": 0,
            })

        return SuccessResponse(
            success=True,
            message="Documents retrieved successfully",
            data={
                "documents": doc_list,
                "total": len(doc_list)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )


@router.post(
    "/import/file",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import file to knowledge base",
    responses={
        201: {"description": "File imported successfully"},
        400: {"description": "Invalid file", "model": ErrorResponse},
        500: {"description": "Server error during import", "model": ErrorResponse},
    },
)
async def import_file(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    current_user: str = Depends(get_current_user),
    orchestrator = Depends(_get_orchestrator),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Import a file to the knowledge base.

    Args:
        file: File to import
        project_id: Optional project ID to associate document
        current_user: Current authenticated user
        orchestrator: Orchestrator instance
        db: Database connection

    Returns:
        SuccessResponse with import details
    """
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is required",
            )

        logger.info(f"Importing file: {file.filename} for user {current_user}")

        # Verify project access if provided
        if project_id:
            project = db.load_project(project_id)
            if not project or project.owner != current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this project"
                )

        # Save uploaded file temporarily
        temp_dir = Path(tempfile.gettempdir()) / "socrates_uploads"
        temp_dir.mkdir(exist_ok=True, parents=True)
        temp_file = temp_dir / f"{uuid.uuid4()}_{file.filename}"

        # Write file content
        content = await file.read()
        temp_file.write_bytes(content)

        logger.debug(f"Saved temp file: {temp_file}")

        try:
            # Process via DocumentProcessorAgent
            result = orchestrator.process_request(
                "document_agent",
                {
                    "action": "import_file",
                    "file_path": str(temp_file),
                    "project_id": project_id,
                }
            )

            logger.debug(f"DocumentProcessor result: {result}")

            # Save metadata to database
            doc_id = str(uuid.uuid4())
            db.save_knowledge_document(
                user_id=current_user,
                project_id=project_id,
                doc_id=doc_id,
                title=file.filename,
                content="",
                source=file.filename,
                document_type="file"
            )

            logger.info(f"File imported successfully: {file.filename}")

            # Emit DOCUMENT_IMPORTED event to trigger knowledge analysis and question regeneration
            try:
                from socratic_system.events import EventType
                orchestrator.event_emitter.emit(
                    EventType.DOCUMENT_IMPORTED,
                    {
                        "project_id": project_id,
                        "file_name": file.filename,
                        "source_type": "file",
                        "words_extracted": result.get("words_extracted", 0),
                        "chunks_created": result.get("chunks_added", 0),
                        "user_id": current_user,
                    }
                )
                logger.debug(f"Emitted DOCUMENT_IMPORTED event for {file.filename}")
            except Exception as e:
                logger.warning(f"Failed to emit DOCUMENT_IMPORTED event: {e}")
                # Don't fail the import if event emission fails

            return SuccessResponse(
                success=True,
                message=f"File '{file.filename}' imported successfully",
                data={
                    "filename": file.filename,
                    "size": len(content),
                    "chunks": result.get("chunks_added", 0),
                    "entries": result.get("entries_added", 0),
                },
            )

        finally:
            # Clean up temp file
            try:
                temp_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file}: {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import file: {str(e)}",
        )


@router.post(
    "/import/url",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import URL to knowledge base",
    responses={
        201: {"description": "URL imported successfully"},
        400: {"description": "Invalid URL", "model": ErrorResponse},
        500: {"description": "Server error during import", "model": ErrorResponse},
    },
)
async def import_url(
    body: dict = Body(...),
    current_user: str = Depends(get_current_user),
    orchestrator = Depends(_get_orchestrator),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Import content from URL to knowledge base.

    Args:
        body: JSON body with url and optional projectId
        current_user: Current authenticated user
        orchestrator: Orchestrator instance
        db: Database connection

    Returns:
        SuccessResponse with import details
    """
    try:
        url = body.get('url')
        project_id = body.get('projectId')

        if not url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL is required",
            )

        logger.info(f"Importing from URL: {url} for user {current_user}")

        # Verify project access if provided
        if project_id:
            project = db.load_project(project_id)
            if not project or project.owner != current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this project"
                )

        # Process via DocumentProcessorAgent
        result = orchestrator.process_request(
            "document_agent",
            {
                "action": "import_url",
                "url": url,
                "project_id": project_id,
            }
        )

        logger.debug(f"DocumentProcessor result: {result}")

        # Save metadata
        doc_id = str(uuid.uuid4())
        db.save_knowledge_document(
            user_id=current_user,
            project_id=project_id,
            doc_id=doc_id,
            title=url,
            source=url,
            document_type="url"
        )

        logger.info(f"URL imported successfully: {url}")

        # Emit DOCUMENT_IMPORTED event to trigger knowledge analysis and question regeneration
        try:
            from socratic_system.events import EventType
            orchestrator.event_emitter.emit(
                EventType.DOCUMENT_IMPORTED,
                {
                    "project_id": project_id,
                    "file_name": url,
                    "source_type": "url",
                    "words_extracted": result.get("words_extracted", 0),
                    "chunks_created": result.get("chunks_added", 0),
                    "user_id": current_user,
                }
            )
            logger.debug(f"Emitted DOCUMENT_IMPORTED event for {url}")
        except Exception as e:
            logger.warning(f"Failed to emit DOCUMENT_IMPORTED event: {e}")
            # Don't fail the import if event emission fails

        return SuccessResponse(
            success=True,
            message=f"Content from '{url}' imported successfully",
            data={
                "url": url,
                "chunks": result.get("chunks_added", 0),
                "entries": result.get("entries_added", 0),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import URL: {str(e)}",
        )


@router.post(
    "/import/text",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import pasted text to knowledge base",
    responses={
        201: {"description": "Text imported successfully"},
        400: {"description": "Invalid text", "model": ErrorResponse},
        500: {"description": "Server error during import", "model": ErrorResponse},
    },
)
async def import_text(
    body: dict = Body(...),
    current_user: str = Depends(get_current_user),
    orchestrator = Depends(_get_orchestrator),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Import pasted text to knowledge base.

    Args:
        body: JSON body with title, content, and optional projectId
        current_user: Current authenticated user
        orchestrator: Orchestrator instance
        db: Database connection

    Returns:
        SuccessResponse with import details
    """
    try:
        title = body.get('title')
        content = body.get('content')
        project_id = body.get('projectId')

        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content is required",
            )

        logger.info(f"Importing text document: {title} for user {current_user}")

        # Verify project access if provided
        if project_id:
            project = db.load_project(project_id)
            if not project or project.owner != current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this project"
                )

        # Process via DocumentProcessorAgent
        result = orchestrator.process_request(
            "document_agent",
            {
                "action": "import_text",
                "content": content,
                "title": title or "Untitled",
                "project_id": project_id,
            }
        )

        logger.debug(f"DocumentProcessor result: {result}")

        # Save metadata
        doc_id = str(uuid.uuid4())
        db.save_knowledge_document(
            user_id=current_user,
            project_id=project_id,
            doc_id=doc_id,
            title=title or "Untitled",
            content=content[:1000],
            source="pasted_text",
            document_type="text"
        )

        logger.info(f"Text document imported successfully: {title}")

        # Emit DOCUMENT_IMPORTED event to trigger knowledge analysis and question regeneration
        word_count = len(content.split())
        try:
            from socratic_system.events import EventType
            orchestrator.event_emitter.emit(
                EventType.DOCUMENT_IMPORTED,
                {
                    "project_id": project_id,
                    "file_name": title or "Untitled",
                    "source_type": "text",
                    "words_extracted": word_count,
                    "chunks_created": result.get("chunks_added", 0),
                    "user_id": current_user,
                }
            )
            logger.debug(f"Emitted DOCUMENT_IMPORTED event for {title}")
        except Exception as e:
            logger.warning(f"Failed to emit DOCUMENT_IMPORTED event: {e}")
            # Don't fail the import if event emission fails

        return SuccessResponse(
            success=True,
            message=f"Text document '{title or 'Untitled'}' imported successfully",
            data={
                "title": title,
                "word_count": word_count,
                "chunks": result.get("chunks_added", 0),
                "entries": result.get("entries_added", 0),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import text: {str(e)}",
        )


@router.get(
    "/search",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Search knowledge base",
    responses={
        200: {"description": "Search results"},
        400: {"description": "Invalid search query", "model": ErrorResponse},
    },
)
async def search_knowledge(
    q: Optional[str] = None,
    query: Optional[str] = None,
    project_id: Optional[str] = None,
    top_k: int = 10,
    current_user: str = Depends(get_current_user),
    orchestrator = Depends(_get_orchestrator),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Search knowledge base using semantic search.

    Args:
        q: Search query (alternative parameter name)
        query: Search query
        project_id: Optional project ID to filter
        top_k: Number of results to return
        current_user: Current authenticated user
        orchestrator: Orchestrator instance
        db: Database connection

    Returns:
        SuccessResponse with search results
    """
    try:
        search_query = q or query
        if not search_query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query is required",
            )

        logger.info(f"Searching knowledge base: {search_query} for user {current_user}")

        # Verify project access if provided
        if project_id:
            project = db.load_project(project_id)
            if not project or project.owner != current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this project"
                )

        # Use VectorDatabase via orchestrator
        vector_db = orchestrator.vector_db
        if not vector_db:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vector database not initialized"
            )

        # Perform semantic search
        results = vector_db.search_similar(
            query=search_query,
            top_k=top_k,
            project_id=project_id
        )

        logger.debug(f"Found {len(results)} search results")

        # Transform results to frontend format
        search_results = []
        for result in results:
            metadata = result.get("metadata", {})
            search_results.append({
                "document_id": metadata.get("source", "unknown"),
                "title": metadata.get("source", "Unknown"),
                "excerpt": result.get("content", "")[:200],
                "relevance_score": max(0, min(1, 1 - result.get("distance", 1))),
                "source": metadata.get("source_type", "unknown")
            })

        logger.info(f"Search completed: found {len(search_results)} results")

        return SuccessResponse(
            success=True,
            message=f"Search completed for '{search_query}'",
            data={
                "query": search_query,
                "results": search_results,
                "total": len(search_results)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search: {str(e)}",
        )


@router.delete(
    "/documents/{document_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete document",
    responses={
        200: {"description": "Document deleted"},
        404: {"description": "Document not found", "model": ErrorResponse},
    },
)
async def delete_document(
    document_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Delete a document from knowledge base.

    Args:
        document_id: ID of document to delete
        current_user: Current authenticated user
        db: Database connection

    Returns:
        SuccessResponse confirming deletion
    """
    try:
        logger.info(f"Deleting document: {document_id} by user {current_user}")

        # Get document to verify ownership
        doc = db.get_knowledge_document(document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}",
            )

        if doc["user_id"] != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this document",
            )

        # Delete from database
        success = db.delete_knowledge_document(document_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document",
            )

        logger.info(f"Document deleted successfully: {document_id}")

        return SuccessResponse(
            success=True,
            message="Document deleted successfully",
            data={"document_id": document_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )


@router.post(
    "/entries",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add knowledge entry",
    responses={
        201: {"description": "Entry added"},
        400: {"description": "Invalid entry", "model": ErrorResponse},
    },
)
async def add_knowledge_entry(
    body: dict = Body(...),
    current_user: str = Depends(get_current_user),
    orchestrator = Depends(_get_orchestrator),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Add a new knowledge entry.

    Args:
        body: JSON body with content, category, and optional projectId
        current_user: Current authenticated user
        orchestrator: Orchestrator instance
        db: Database connection

    Returns:
        SuccessResponse with entry details
    """
    try:
        content = body.get('content')
        category = body.get('category')
        project_id = body.get('projectId')

        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content is required",
            )

        logger.info(f"Adding knowledge entry in category: {category} for user {current_user}")

        # Verify project access if provided
        if project_id:
            project = db.load_project(project_id)
            if not project or project.owner != current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this project"
                )

        # Process as text import with category metadata
        result = orchestrator.process_request(
            "document_agent",
            {
                "action": "import_text",
                "content": content,
                "title": f"{category} entry",
                "project_id": project_id,
            }
        )

        logger.debug(f"DocumentProcessor result: {result}")

        # Save metadata
        entry_id = str(uuid.uuid4())
        db.save_knowledge_document(
            user_id=current_user,
            project_id=project_id,
            doc_id=entry_id,
            title=f"{category} entry",
            content=content[:1000],
            source="manual_entry",
            document_type=category
        )

        logger.info(f"Knowledge entry added successfully: {category}")

        return SuccessResponse(
            success=True,
            message="Knowledge entry added successfully",
            data={
                "category": category,
                "content_length": len(content),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding knowledge entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add entry: {str(e)}",
        )
