# Phase 3.2 - Quick Integration Reference Guide

Quick start guide for integrating GitHubSyncHandler into existing GitHub routers.

---

## Import the Handler

```python
from socratic_system.agents.github_sync_handler import (
    create_github_sync_handler,
    TokenExpiredError,
    PermissionDeniedError,
    RepositoryNotFoundError,
    NetworkSyncFailedError,
    ConflictResolutionError,
    FileSizeExceededError
)
```

---

## 1. Permission-Safe Sync Pattern

For any endpoint that syncs a repository:

```python
@router.post("/projects/{project_id}/sync-github")
async def sync_github(project_id: str) -> APIResponse:
    handler = create_github_sync_handler(db=db)

    try:
        # Step 1: Verify access
        has_access, reason = handler.check_repo_access(repo_url, token)

        if not has_access:
            return APIResponse(
                success=False,
                status="error",
                error_code="ACCESS_DENIED",
                message=reason
            )

        # Step 2: Perform sync with retry
        result = handler.sync_with_retry_and_resume(
            repo_url=repo_url,
            sync_function=your_sync_function,
            max_retries=3
        )

        return APIResponse(
            success=True,
            status="success",
            data={"synced": True, "attempt": result["attempt"]}
        )

    except RepositoryNotFoundError:
        db.mark_project_github_sync_broken(project_id)
        return APIResponse(
            success=False,
            status="error",
            error_code="REPO_NOT_FOUND",
            message="Repository has been deleted"
        )

    except PermissionDeniedError:
        return APIResponse(
            success=False,
            status="error",
            error_code="PERMISSION_DENIED",
            message="Access to repository has been revoked"
        )

    except NetworkSyncFailedError:
        return APIResponse(
            success=False,
            status="error",
            error_code="NETWORK_ERROR",
            message="Sync failed after retries. Please try again later."
        )
```

---

## 2. Token Refresh Pattern

For endpoints that need to handle token expiry:

```python
@router.post("/sync-with-refresh")
async def sync_with_token_refresh(project_id: str) -> APIResponse:
    handler = create_github_sync_handler(db=db)

    def refresh_callback():
        # Your OAuth refresh logic
        new_token = oauth.refresh_github_token(user_id)
        db.update_github_token(user_id, new_token)
        return new_token

    try:
        result = handler.sync_with_token_refresh(
            repo_url=repo_url,
            token=current_token,
            refresh_callback=refresh_callback
        )

        if result["token_refreshed"]:
            return APIResponse(
                success=True,
                status="success",
                data={"synced": True, "token_refreshed": True}
            )

        return APIResponse(
            success=result["status"] == "success",
            status=result["status"],
            data={"synced": result["status"] == "success"}
        )

    except TokenExpiredError:
        return APIResponse(
            success=False,
            status="error",
            error_code="TOKEN_EXPIRED",
            message="GitHub token expired. Please re-authenticate."
        )
```

---

## 3. Conflict Resolution Pattern

For endpoints that handle merge conflicts:

```python
@router.post("/resolve-conflicts")
async def resolve_conflicts(repo_id: str) -> APIResponse:
    handler = create_github_sync_handler(db=db)

    try:
        # Detect and resolve conflicts
        result = handler.handle_merge_conflicts(
            repo_path=repo_local_path,
            conflict_info={},
            default_strategy="ours"  # or "theirs"
        )

        if result["status"] == "success":
            return APIResponse(
                success=True,
                status="success",
                data={
                    "conflicts_resolved": len(result["resolved"]),
                    "resolved_files": result["resolved"]
                }
            )

        elif result["status"] == "partial":
            return APIResponse(
                success=True,
                status="success",
                data={
                    "conflicts_resolved": len(result["resolved"]),
                    "manual_review_required": result["manual_required"],
                    "message": "Some conflicts require manual review"
                }
            )

        else:
            return APIResponse(
                success=False,
                status="error",
                error_code="CONFLICT_ERROR",
                message=result.get("error", "Failed to resolve conflicts")
            )

    except ConflictResolutionError as e:
        return APIResponse(
            success=False,
            status="error",
            error_code="CONFLICT_RESOLUTION_FAILED",
            message=str(e)
        )
```

---

## 4. Large File Handling Pattern

For endpoints that validate files before pushing:

```python
@router.post("/validate-push")
async def validate_before_push(project_id: str) -> APIResponse:
    handler = create_github_sync_handler()

    # Get files to push
    files_to_push = get_modified_files(repo_path)

    # Validate file sizes
    result = handler.handle_large_files(
        files_to_push=files_to_push,
        strategy="exclude"  # or "lfs"
    )

    if result["status"] == "error":
        return APIResponse(
            success=False,
            status="error",
            error_code="FILE_SIZE_ERROR",
            message=result["message"]
        )

    if result["status"] == "partial":
        # Some files excluded
        return APIResponse(
            success=True,
            status="success",
            data={
                "all_files_valid": False,
                "valid_files": result.get("valid_files", []),
                "excluded_files": result.get("excluded_files", []),
                "message": f"Excluding {len(result['excluded_files'])} large files"
            }
        )

    # All files valid
    return APIResponse(
        success=True,
        status="success",
        data={"all_files_valid": True}
    )
```

---

## 5. Combined Pattern (Recommended for Main Sync Endpoint)

For your primary sync endpoint:

```python
@router.post("/projects/{project_id}/full-sync")
async def full_sync_github(project_id: str) -> APIResponse:
    """
    Complete GitHub sync with all edge case handling
    """
    handler = create_github_sync_handler(db=db)

    try:
        project = db.get_project(project_id)
        user = db.get_user(project.user_id)

        # 1. Check token validity
        if not handler.check_token_validity(
            user.github_token,
            token_expiry=user.github_token_expiry
        ):
            return APIResponse(
                success=False,
                status="error",
                error_code="TOKEN_INVALID",
                message="GitHub token is invalid"
            )

        # 2. Check repository access
        has_access, reason = handler.check_repo_access(
            project.github_url,
            user.github_token
        )

        if not has_access:
            return APIResponse(
                success=False,
                status="error",
                error_code="ACCESS_DENIED",
                message=reason
            )

        # 3. Perform sync with retry
        sync_result = handler.sync_with_retry_and_resume(
            repo_url=project.github_url,
            sync_function=perform_git_sync,
            max_retries=3
        )

        # 4. Handle conflicts
        conflict_result = handler.handle_merge_conflicts(
            repo_path=project.local_path,
            conflict_info={},
            default_strategy="ours"
        )

        # 5. Validate files before push
        files = get_modified_files(project.local_path)
        file_result = handler.handle_large_files(
            files_to_push=files,
            strategy="exclude"
        )

        # Return success with details
        return APIResponse(
            success=True,
            status="success",
            data={
                "synced": True,
                "attempt": sync_result["attempt"],
                "conflicts": {
                    "found": conflict_result["conflicts_found"],
                    "resolved": len(conflict_result["resolved"]),
                    "manual_review": conflict_result.get("manual_required", [])
                },
                "files": {
                    "total": len(files),
                    "valid": len(file_result.get("valid_files", files)),
                    "excluded": len(file_result.get("excluded_files", []))
                }
            }
        )

    except RepositoryNotFoundError:
        db.mark_project_github_sync_broken(project_id)
        return APIResponse(
            success=False,
            status="error",
            error_code="REPO_DELETED",
            message="Repository has been deleted"
        )

    except PermissionDeniedError:
        return APIResponse(
            success=False,
            status="error",
            error_code="PERMISSION_DENIED",
            message="Access to repository has been revoked"
        )

    except NetworkSyncFailedError:
        return APIResponse(
            success=False,
            status="error",
            error_code="NETWORK_ERROR",
            message="Sync failed after retries"
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return APIResponse(
            success=False,
            status="error",
            error_code="UNEXPECTED_ERROR",
            message="An unexpected error occurred"
        )
```

---

## Async/Background Job Pattern

For long-running syncs:

```python
@router.post("/projects/{project_id}/sync-async")
async def sync_github_async(project_id: str) -> APIResponse:
    """Queue sync as background job"""

    # Queue the sync
    job = background_queue.enqueue(
        perform_full_sync,
        project_id=project_id,
        job_timeout=300  # 5 minutes
    )

    return APIResponse(
        success=True,
        status="pending",
        data={"job_id": job.id}
    )


def perform_full_sync(project_id: str):
    """Background job for full sync"""
    handler = create_github_sync_handler(db=db)
    # ... (same logic as full_sync_github)
    # Update job status in queue


@router.get("/sync-status/{job_id}")
async def get_sync_status(job_id: str) -> APIResponse:
    """Check async sync status"""
    job = background_queue.fetch_job(job_id)

    return APIResponse(
        success=True,
        status="success",
        data={
            "job_id": job_id,
            "status": job.get_status(),
            "progress": job.meta.get("progress", 0)
        }
    )
```

---

## Command Integration Pattern

For updating `github_commands.py`:

```python
async def sync_repo_command(repo_id: str):
    """CLI command to sync repository"""
    handler = create_github_sync_handler(db=db)

    try:
        result = handler.sync_with_retry_and_resume(
            repo_url=repo_url,
            sync_function=your_sync_func,
            max_retries=3
        )

        console.print(f"[green]Synced on attempt {result['attempt']}[/green]")
        return True

    except NetworkSyncFailedError:
        console.print("[red]Sync failed after retries. Try again later.[/red]")
        return False

    except PermissionDeniedError:
        console.print("[red]Access denied. Check repository permissions.[/red]")
        return False

    except RepositoryNotFoundError:
        console.print("[red]Repository not found.[/red]")
        return False
```

---

## Error Handling Checklist

When integrating, ensure you handle:

- [ ] TokenExpiredError - Request re-authentication
- [ ] PermissionDeniedError - Show "re-authenticate" prompt
- [ ] RepositoryNotFoundError - Show "repository deleted" message
- [ ] NetworkSyncFailedError - Suggest retry or contact support
- [ ] ConflictResolutionError - Show conflict resolution UI
- [ ] FileSizeExceededError - Show file size warnings
- [ ] Generic exceptions - Log and show generic error message

---

## Testing Integration

Test each edge case in your integration:

```python
# Test 1: Successful sync
def test_sync_success():
    result = handler.sync_with_retry_and_resume(repo_url, mock_sync)
    assert result["status"] == "success"
    assert result["attempt"] == 1

# Test 2: Token expiry
def test_token_refresh():
    result = handler.sync_with_token_refresh(
        repo_url, expired_token, refresh_callback
    )
    assert result["token_refreshed"] == True

# Test 3: Permission denied
def test_permission_denied():
    with pytest.raises(PermissionDeniedError):
        handler.check_repo_access(repo_url, invalid_token)

# Test 4: Conflict resolution
def test_conflicts():
    result = handler.handle_merge_conflicts(repo_path, {}, "ours")
    assert result["status"] in ["success", "partial"]

# Test 5: Large files
def test_large_files():
    result = handler.handle_large_files(files, strategy="exclude")
    assert "excluded_files" in result
```

---

## Performance Tips

1. **Cache Token Validity** - Don't check every sync, cache for 1 hour
2. **Batch File Validation** - Validate all files in one call, not individually
3. **Async Operations** - Use background jobs for long-running syncs
4. **Progress Tracking** - Enable database logging for monitoring
5. **Timeout Configuration** - Adjust timeouts based on network/repo size

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Token validation takes too long" | Reduce timeout_per_attempt, cache token validity |
| "Retries keep failing" | Check network connectivity, increase MAX_RETRIES |
| "Conflicts never resolve" | Use "theirs" strategy instead of "ours" |
| "Large file handling excludes all files" | Check MAX_FILE_SIZE setting, enable LFS |
| "Permission errors not caught" | Ensure you're catching PermissionDeniedError |

---

## Summary

1. Import the handler
2. Create handler instance with optional db
3. Call appropriate method for your use case
4. Handle specific exceptions
5. Return APIResponse with proper status/error codes
6. Log to database for monitoring

**That's it!** The handler takes care of all the edge cases.
