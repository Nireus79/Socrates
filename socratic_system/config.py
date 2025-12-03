"""
Socratic RAG System Configuration
"""

CONFIG = {
    'MAX_CONTEXT_LENGTH': 8000,
    'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',
    'CLAUDE_MODEL': 'claude-sonnet-4-5-20250929',
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 1,
    'TOKEN_WARNING_THRESHOLD': 0.8,
    'SESSION_TIMEOUT': 3600,  # 1 hour
    'DATA_DIR': 'socratic_data'
}
