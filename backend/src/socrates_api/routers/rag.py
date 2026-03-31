"""
RAG (Retrieval-Augmented Generation) API endpoints for Socrates.

Provides REST endpoints for managing document indexing and context retrieval
for augmented code generation and knowledge-based responses.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from socrates_api.auth import get_current_user
from socrates_api.models import APIResponse, ErrorResponse
from socrates_api.models_local import RAGIntegration
from socrates_api.library_cache import get_rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class IndexDocumentRequest(BaseModel):
    """Request to index a document in RAG"""
    doc_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    doc_type: Optional[str] = Field("text", description="Document type (text, code, markdown, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata for the document"
    )


class RetrieveContextRequest(BaseModel):
    """Request to retrieve context for a query"""
    query: str = Field(..., description="Query to find relevant documents")
    limit: int = Field(5, ge=1, le=20, description="Maximum number of documents to retrieve")
    threshold: float = Field(0.5, ge=0.0, le=1.0, description="Minimum relevance threshold")


class AugmentPromptRequest(BaseModel):
    """Request to augment a prompt with context"""
    prompt: str = Field(..., description="Original prompt to augment")
    context_limit: int = Field(5, ge=1, le=20, description="Maximum number of context documents")
    include_metadata: bool = Field(True, description="Include document metadata in augmented prompt")


class DocumentMetadata(BaseModel):
    """Document metadata in search results"""
    doc_id: str
    title: str
    doc_type: str
    score: Optional[float] = None


class RetrievedDocument(BaseModel):
    """Retrieved document with context"""
    doc_id: str
    title: str
    content: str
    doc_type: str
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post(
    "/index",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Index document for RAG",
    responses={
        201: {"description": "Document indexed successfully"},
        400: {"description": "Invalid input", "model": ErrorResponse},
        503: {"description": "RAG service unavailable", "model": ErrorResponse},
    },
)
async def index_document(
    request: IndexDocumentRequest,
    current_user: str = Depends(get_current_user),
    rag: RAGIntegration = Depends(get_rag_service),
) -> APIResponse:
    """
    Index a document in the RAG system for retrieval.

    Documents are indexed to enable semantic search and context retrieval
    for augmented code generation and knowledge-based responses.

    Args:
        request: Document to index with id, title, content, type, metadata
        current_user: Authenticated user
        rag: RAGIntegration singleton (injected)

    Returns:
        APIResponse with indexed document details
    """
    try:
        logger.info(f"Indexing document: {request.doc_id} for user {current_user}")
        # Index the document using RAG system
        success = rag.index_document(
            doc_id=request.doc_id,
            title=request.title,
            content=request.content,
            doc_type=request.doc_type,
            metadata=request.metadata
        )

        logger.info(f"Successfully indexed document: {request.doc_id}")

        return APIResponse(
            success=True,
            status="created",
            message=f"Document indexed successfully: {request.title}",
            data={
                "doc_id": request.doc_id,
                "title": request.title,
                "doc_type": request.doc_type,
                "content_length": len(request.content),
                "metadata_keys": list(request.metadata.keys()) if request.metadata else [],
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.post(
    "/retrieve",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve context for query",
    responses={
        200: {"description": "Context retrieved successfully"},
        400: {"description": "Invalid input", "model": ErrorResponse},
        503: {"description": "RAG service unavailable", "model": ErrorResponse},
    },
)
async def retrieve_context(
    request: RetrieveContextRequest,
    current_user: str = Depends(get_current_user),
    rag: RAGIntegration = Depends(get_rag_service),
) -> APIResponse:
    """
    Retrieve relevant documents for a given query.

    Uses semantic search to find documents most relevant to the query.

    Args:
        request: Query parameters with query, limit, threshold
        current_user: Authenticated user
        rag: RAGIntegration singleton (injected)

    Returns:
        APIResponse with list of relevant documents and relevance scores
    """
    try:
        logger.info(f"Retrieving context for: {request.query[:50]}... (limit: {request.limit})")
        # Retrieve context using RAG system
        results = rag.retrieve_context(
            query=request.query,
            limit=request.limit,
            threshold=request.threshold
        )

        logger.info(f"Retrieved {len(results)} documents for query")

        return APIResponse(
            success=True,
            status="success",
            message=f"Retrieved {len(results)} relevant documents",
            data={
                "query": request.query,
                "count": len(results),
                "limit": request.limit,
                "threshold": request.threshold,
                "documents": results,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving context: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.post(
    "/augment",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Augment prompt with context",
    responses={
        200: {"description": "Prompt augmented successfully"},
        400: {"description": "Invalid input", "model": ErrorResponse},
        503: {"description": "RAG service unavailable", "model": ErrorResponse},
    },
)
async def augment_prompt(
    request: AugmentPromptRequest,
    current_user: str = Depends(get_current_user),
    rag: RAGIntegration = Depends(get_rag_service),
) -> APIResponse:
    """
    Augment a prompt with relevant context from indexed documents.

    The augmented prompt includes the original prompt plus relevant document
    excerpts, enabling more informed code generation and responses.

    Args:
        request: Prompt to augment with context limit
        current_user: Authenticated user
        rag: RAGIntegration singleton (injected)

    Returns:
        APIResponse with augmented prompt and context sources
    """
    try:
        logger.info(f"Augmenting prompt (context_limit: {request.context_limit})")
        # Augment the prompt using RAG system
        augmented = rag.augment_prompt(
            prompt=request.prompt,
            context_limit=request.context_limit,
            include_metadata=request.include_metadata
        )

        # Count how much context was added
        context_added = augmented != request.prompt
        context_count = request.context_limit if context_added else 0

        logger.info(f"Prompt augmented with {context_count} documents")

        return APIResponse(
            success=True,
            status="success",
            message="Prompt augmented with context" if context_added else "No relevant context found",
            data={
                "original_prompt": request.prompt,
                "augmented_prompt": augmented,
                "context_count": context_count,
                "context_limit": request.context_limit,
                "augmented": context_added,
            },
        )

    except Exception as e:
        logger.error(f"Error augmenting prompt: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/search",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Search documents",
    responses={
        200: {"description": "Search completed"},
        400: {"description": "Invalid input", "model": ErrorResponse},
        503: {"description": "RAG service unavailable", "model": ErrorResponse},
    },
)
async def search_documents(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    current_user: str = Depends(get_current_user),
    rag: RAGIntegration = Depends(get_rag_service),
) -> APIResponse:
    """
    Search indexed documents by query.

    Performs semantic search to find documents matching the query.

    Args:
        query: Search query string
        limit: Maximum number of results (default: 10, max: 50)
        current_user: Authenticated user
        rag: RAGIntegration singleton (injected)

    Returns:
        APIResponse with search results
    """
    try:
        logger.info(f"Searching documents for: {query[:50]}... (limit: {limit})")
        # Search documents using RAG system
        results = rag.search_documents(query=query, limit=limit)

        logger.info(f"Search returned {len(results)} results")

        return APIResponse(
            success=True,
            status="success",
            message=f"Found {len(results)} documents matching query",
            data={
                "query": query,
                "count": len(results),
                "limit": limit,
                "documents": results,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/status",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get RAG status",
    responses={
        200: {"description": "RAG status retrieved"},
    },
)
async def get_rag_status(
    current_user: str = Depends(get_current_user),
    rag: RAGIntegration = Depends(get_rag_service),
) -> APIResponse:
    """
    Get the status of the RAG system.

    Returns availability of RAG components including document store and retriever.

    Args:
        current_user: Authenticated user
        rag: RAGIntegration singleton (injected)

    Returns:
        APIResponse with RAG system status
    """
    try:
        status_info = rag.get_status()

        logger.info(f"RAG status requested by {current_user}: {status_info}")

        capabilities = []
        if status_info.get("document_store"):
            capabilities.append("document_indexing")
        if status_info.get("retriever"):
            capabilities.extend(["context_retrieval", "semantic_search", "prompt_augmentation"])

        return APIResponse(
            success=True,
            status="operational",
            message="RAG system operational and ready to use",
            data={
                "available": True,
                "library_available": status_info.get("rag_client", True),
                "document_store_available": status_info.get("document_store", True),
                "retriever_available": status_info.get("retriever", True),
                "capabilities": capabilities,
                "features": {
                    "index_documents": True,
                    "retrieve_context": True,
                    "search_documents": True,
                    "augment_prompts": True,
                }
            },
        )

    except Exception as e:
        logger.error(f"Error getting RAG status: {str(e)}", exc_info=True)
        return APIResponse(
            success=False,
            status="error",
            message=f"Failed to get RAG status: {str(e)}",
            data={
                "available": False,
                "capabilities": [],
            },
        )


@router.delete(
    "/index/{doc_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove document from RAG",
    responses={
        200: {"description": "Document removed successfully"},
        404: {"description": "Document not found", "model": ErrorResponse},
        503: {"description": "RAG service unavailable", "model": ErrorResponse},
    },
)
async def remove_document(
    doc_id: str,
    current_user: str = Depends(get_current_user),
    rag: RAGIntegration = Depends(get_rag_service),
) -> APIResponse:
    """
    Remove a document from the RAG index.

    Args:
        doc_id: Document identifier to remove
        current_user: Authenticated user
        rag: RAGIntegration singleton (injected)

    Returns:
        APIResponse with removal status
    """
    try:
        logger.info(f"Removing document from RAG: {doc_id}")
        # Remove the document from RAG system
        success = rag.remove_document(doc_id)

        logger.info(f"Successfully removed document from RAG: {doc_id}")

        return APIResponse(
            success=True,
            status="success",
            message=f"Document removed from RAG index: {doc_id}",
            data={"doc_id": doc_id, "removed": True},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )
