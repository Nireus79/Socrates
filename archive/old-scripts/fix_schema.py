#!/usr/bin/env python3
"""Fix all schema mismatches in project_db_v2.py"""

import re

# Read the file
with open('socratic_system/database/project_db_v2.py', 'r') as f:
    content = f.read()

# Fix 1: get_question_effectiveness SELECT statement
content = content.replace(
    'SELECT effectiveness_json FROM question_effectiveness_v2\n                WHERE user_id = ? AND question_template_id = ?',
    'SELECT id, user_id, question_template_id, effectiveness_score, times_asked,\n                       times_answered_well, last_asked_at, created_at, updated_at\n                FROM question_effectiveness_v2\n                WHERE user_id = ? AND question_template_id = ?'
)

# Fix 2: get_question_effectiveness parsing
old_parse = '''if result:
                effectiveness_dict = json.loads(result[0])
                # Deserialize datetimes
                if isinstance(effectiveness_dict.get("created_at"), str):
                    effectiveness_dict["created_at"] = deserialize_datetime(
                        effectiveness_dict["created_at"]
                    )
                if isinstance(effectiveness_dict.get("updated_at"), str):
                    effectiveness_dict["updated_at"] = deserialize_datetime(
                        effectiveness_dict["updated_at"]
                    )
                if effectiveness_dict.get("last_asked_at") and isinstance(
                    effectiveness_dict["last_asked_at"], str
                ):
                    effectiveness_dict["last_asked_at"] = deserialize_datetime(
                        effectiveness_dict["last_asked_at"]
                    )
                return effectiveness_dict'''

new_parse = '''if result:
                effectiveness_dict = {
                    "id": result[0],
                    "user_id": result[1],
                    "question_template_id": result[2],
                    "effectiveness_score": result[3],
                    "times_asked": result[4],
                    "times_answered_well": result[5],
                    "last_asked_at": deserialize_datetime(result[6]) if result[6] else None,
                    "created_at": deserialize_datetime(result[7]),
                    "updated_at": deserialize_datetime(result[8]),
                }
                return effectiveness_dict'''

content = content.replace(old_parse, new_parse)

# Fix 3: get_user_effectiveness_all SELECT
content = content.replace(
    '"SELECT effectiveness_json FROM question_effectiveness_v2 WHERE user_id = ?"',
    '"SELECT id, user_id, question_template_id, effectiveness_score, times_asked,\n                       times_answered_well, last_asked_at, created_at, updated_at\n                FROM question_effectiveness_v2 WHERE user_id = ?"'
)

# Fix 4: get_behavior_pattern SELECT - using pattern_json
content = re.sub(
    r'SELECT pattern_json FROM behavior_patterns_v2\s+WHERE user_id = \? AND pattern_type = \?',
    'SELECT id, user_id, pattern_type, pattern_data, frequency, learned_at, updated_at\n                FROM behavior_patterns_v2\n                WHERE user_id = ? AND pattern_type = ?',
    content
)

# Fix 5: Fix save_knowledge_document - most critical
# Change signature
old_sig = '''def save_knowledge_document(
        self, user_id: str, project_id: str, doc_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a knowledge document (entry).

        Args:
            user_id: Username
            project_id: Project ID
            doc_id: Document ID
            content: Document content
            metadata: Optional metadata dictionary

        Returns:
            True if successful, False otherwise
        """'''

new_sig = '''def save_knowledge_document(
        self,
        user_id: str,
        project_id: str,
        doc_id: str,
        title: str = "",
        content: str = "",
        source: Optional[str] = None,
        document_type: str = "document",
    ) -> bool:
        """
        Save a knowledge document (entry).

        Args:
            user_id: Username
            project_id: Project ID
            doc_id: Document ID
            title: Document title
            content: Document content
            source: Optional source reference
            document_type: Type of document

        Returns:
            True if successful, False otherwise
        """'''

content = content.replace(old_sig, new_sig)

# Fix the INSERT in save_knowledge_document
content = content.replace(
    '''now = datetime.now()
            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute(
                """
                INSERT OR REPLACE INTO knowledge_documents_v2
                (id, project_id, user_id, content, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    doc_id,
                    project_id,
                    user_id,
                    content,
                    metadata_json,
                    serialize_datetime(now),
                    serialize_datetime(now),
                ),
            )''',
    '''now = datetime.now()

            cursor.execute(
                """
                INSERT OR REPLACE INTO knowledge_documents_v2
                (id, project_id, user_id, title, content, source, document_type, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    doc_id,
                    project_id,
                    user_id,
                    title,
                    content,
                    source,
                    document_type,
                    serialize_datetime(now),
                ),
            )'''
)

# Fix 6: config_json to config_data
content = content.replace(
    '(id, user_id, provider, config_json, created_at, updated_at)',
    '(id, user_id, provider, config_data, created_at, updated_at)'
)

# Fix 7: get_knowledge_document
content = content.replace(
    '''SELECT id, project_id, user_id, content, metadata, created_at, updated_at
                FROM knowledge_documents_v2
                WHERE id = ?''',
    '''SELECT id, project_id, user_id, title, content, source, document_type, uploaded_at
                FROM knowledge_documents_v2
                WHERE id = ?'''
)

# Fix 8: get_knowledge_document return
content = content.replace(
    '''if row:
                metadata = json.loads(row[4]) if row[4] and isinstance(row[4], str) else row[4]
                return {
                    "id": row[0],
                    "project_id": row[1],
                    "user_id": row[2],
                    "content": row[3],
                    "metadata": metadata,
                    "created_at": row[5],
                    "updated_at": row[6],
                }''',
    '''if row:
                return {
                    "id": row[0],
                    "project_id": row[1],
                    "user_id": row[2],
                    "title": row[3],
                    "content": row[4],
                    "source": row[5],
                    "document_type": row[6],
                    "uploaded_at": row[7],
                }'''
)

# Fix 9: get_project_knowledge_documents
content = content.replace(
    '''SELECT id, project_id, user_id, content, metadata, created_at, updated_at
                FROM knowledge_documents_v2
                WHERE project_id = ?
                ORDER BY created_at DESC''',
    '''SELECT id, project_id, user_id, title, content, source, document_type, uploaded_at
                FROM knowledge_documents_v2
                WHERE project_id = ?
                ORDER BY uploaded_at DESC'''
)

# Write back
with open('socratic_system/database/project_db_v2.py', 'w') as f:
    f.write(content)

print("✓ All schema mismatches fixed!")
