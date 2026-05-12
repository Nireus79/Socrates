"""
Database schema for audit logging.

Creates immutable, encrypted audit trail tables for compliance and forensics.
"""

import sqlite3


def create_audit_log_table(connection: sqlite3.Connection) -> None:
    """Create audit_logs table for immutable logging.

    Args:
        connection: SQLite database connection

    Raises:
        sqlite3.Error: If table creation fails
    """
    cursor = connection.cursor()

    # Create audit_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT,
            actor_id TEXT,
            actor_type TEXT,
            action TEXT,
            resource TEXT,
            resource_type TEXT,
            status TEXT,
            result_code TEXT,
            details TEXT,
            request_id TEXT,
            session_id TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Immutability: once inserted, never modified
            UNIQUE(id)
        )
    """)

    # Create indexes for common queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_id, timestamp DESC)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource, timestamp DESC)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_logs(severity, timestamp DESC)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_logs(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_request_id ON audit_logs(request_id)")

    connection.commit()


def create_agent_identity_table(connection: sqlite3.Connection) -> None:
    """Create agent_identities table for zero-trust authentication.

    Args:
        connection: SQLite database connection
    """
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_identities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL UNIQUE,
            agent_id TEXT NOT NULL UNIQUE,
            public_key TEXT NOT NULL,
            issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active INTEGER DEFAULT 1,

            -- Capabilities granted to this agent
            capabilities TEXT,  -- JSON array

            -- Resource limits for this agent
            resource_limits TEXT,  -- JSON object

            -- Signature for tamper-evident verification
            signature TEXT,

            created_by TEXT,
            revoked_at TIMESTAMP,
            revocation_reason TEXT
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON agent_identities(agent_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_name ON agent_identities(agent_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_active ON agent_identities(is_active)")

    connection.commit()


def create_capability_tokens_table(connection: sqlite3.Connection) -> None:
    """Create capability_tokens table for capability-based access control.

    Args:
        connection: SQLite database connection
    """
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS capability_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_id TEXT NOT NULL UNIQUE,
            agent_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,

            -- What this token allows
            capabilities TEXT NOT NULL,  -- JSON array

            -- Resource access restrictions
            resource_access TEXT,  -- JSON object
            resource_limits TEXT,  -- JSON object

            -- Token validity
            issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,

            -- Token state
            is_active INTEGER DEFAULT 1,
            is_revoked INTEGER DEFAULT 0,
            revoked_at TIMESTAMP,
            revocation_reason TEXT,

            -- Cryptographic integrity
            signature TEXT NOT NULL,

            -- Usage tracking
            last_used TIMESTAMP,
            use_count INTEGER DEFAULT 0,

            -- Audit
            created_by TEXT,
            created_context TEXT
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_id ON capability_tokens(token_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_agent ON capability_tokens(agent_id)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_token_active ON capability_tokens(is_active, expires_at)"
    )

    connection.commit()


def create_security_events_table(connection: sqlite3.Connection) -> None:
    """Create security_events table for security incidents and alerts.

    Args:
        connection: SQLite database connection
    """
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,

            -- What triggered the event
            trigger_source TEXT,
            trigger_details TEXT,  -- JSON

            -- Resources involved
            affected_agents TEXT,  -- JSON array
            affected_resources TEXT,  -- JSON array
            affected_users TEXT,  -- JSON array

            -- Response
            response_action TEXT,
            response_timestamp TIMESTAMP,
            response_details TEXT,  -- JSON

            -- Status
            status TEXT DEFAULT 'open',
            resolved_at TIMESTAMP,
            resolution TEXT,

            -- Investigation
            investigation_notes TEXT,
            investigated_by TEXT
        )
    """)

    # Create indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_security_timestamp ON security_events(timestamp DESC)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_severity ON security_events(severity)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_status ON security_events(status)")

    connection.commit()


def create_all_audit_tables(connection: sqlite3.Connection) -> None:
    """Create all audit and security-related tables.

    Args:
        connection: SQLite database connection
    """
    create_audit_log_table(connection)
    create_agent_identity_table(connection)
    create_capability_tokens_table(connection)
    create_security_events_table(connection)


def add_audit_log_methods_to_db(db_class) -> None:
    """Add audit logging methods to database class.

    Args:
        db_class: Database class to extend
    """

    def insert_audit_log(self, entry_data: dict) -> int | None:
        """Insert audit log entry.

        Args:
            entry_data: Dictionary with audit entry data

        Returns:
            Inserted row ID or None
        """
        try:
            cursor = self.get_connection().cursor()
            cursor.execute(
                """
                INSERT INTO audit_logs (
                    timestamp, event_type, severity, actor_id, actor_type,
                    action, resource, resource_type, status, result_code,
                    details, request_id, session_id, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entry_data.get("timestamp"),
                    entry_data.get("event_type"),
                    entry_data.get("severity"),
                    entry_data.get("actor_id"),
                    entry_data.get("actor_type"),
                    entry_data.get("action"),
                    entry_data.get("resource"),
                    entry_data.get("resource_type"),
                    entry_data.get("status"),
                    entry_data.get("result_code"),
                    entry_data.get("details"),  # JSON string
                    entry_data.get("request_id"),
                    entry_data.get("session_id"),
                    entry_data.get("ip_address"),
                    entry_data.get("user_agent"),
                ),
            )
            self.get_connection().commit()
            return cursor.lastrowid
        except Exception as e:
            self._logger.error(f"Failed to insert audit log: {e}")
            return None

    def query_audit_logs(
        self, filters: dict = None, start_date=None, end_date=None, limit: int = 100
    ):
        """Query audit logs.

        Args:
            filters: Dictionary of filter criteria
            start_date: Start date for range query
            end_date: End date for range query
            limit: Maximum results

        Returns:
            List of matching audit entries
        """
        try:
            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []

            if filters:
                if "event_type" in filters:
                    query += " AND event_type = ?"
                    params.append(filters["event_type"])
                if "actor_id" in filters:
                    query += " AND actor_id = ?"
                    params.append(filters["actor_id"])
                if "resource" in filters:
                    query += " AND resource = ?"
                    params.append(filters["resource"])

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = self.get_connection().cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            self._logger.error(f"Failed to query audit logs: {e}")
            return []

    def purge_old_audit_logs(self, cutoff_date, dry_run=False):
        """Remove audit logs older than cutoff date.

        Args:
            cutoff_date: Date before which to delete
            dry_run: If True, just count, don't delete

        Returns:
            Number of entries purged
        """
        try:
            cursor = self.get_connection().cursor()

            # Count entries to be deleted
            cursor.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE timestamp < ?", (cutoff_date.isoformat(),)
            )
            count = cursor.fetchone()[0]

            if not dry_run and count > 0:
                cursor.execute(
                    "DELETE FROM audit_logs WHERE timestamp < ?", (cutoff_date.isoformat(),)
                )
                self.get_connection().commit()
                self._logger.info(f"Purged {count} old audit logs")

            return count
        except Exception as e:
            self._logger.error(f"Failed to purge old audit logs: {e}")
            return 0

    # Add methods to class
    db_class.insert_audit_log = insert_audit_log
    db_class.query_audit_logs = query_audit_logs
    db_class.purge_old_audit_logs = purge_old_audit_logs
