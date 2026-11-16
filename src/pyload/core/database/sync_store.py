import json

from ..utils.struct.style import style


class SyncStoreMethods:

    @style.queue
    def sync_get_changes(
        self,
        database_id,
        since_revision,
        limit=1000,
    ):
        if not 1 <= limit <= 10000:
            raise ValueError("Invalid limit")

        self.c.execute(
            """
            SELECT value FROM sync_metadata
            WHERE key = 'database_id'
            """
        )
        current_database_id = self.c.fetchone()[0]

        self.c.execute(
            """
            SELECT value FROM sync_metadata
            WHERE key = 'minimum_revision'
            """
        )
        minimum_revision = int(self.c.fetchone()[0])

        self.c.execute(
            """
            SELECT COALESCE(MAX(revision), 0)
            FROM essential_changes
            """
        )
        current_revision = self.c.fetchone()[0]

        if (
            database_id != current_database_id
            or since_revision < minimum_revision
            or since_revision > current_revision
        ):
            return {
                "reset_required": True,
                "database_id": current_database_id,
                "minimum_revision": minimum_revision,
                "current_revision": current_revision,
            }

        self.c.execute(
            """
            SELECT revision, entity, operation,
                   entity_id, payload
            FROM essential_changes
            WHERE revision > ?
            ORDER BY revision
            LIMIT ?
            """,
            (since_revision, limit),
        )

        changes = [
            {
                "revision": revision,
                "entity": entity,
                "operation": operation,
                "id": entity_id,
                "payload": json.loads(payload)
                if payload is not None else None,
            }
            for revision, entity, operation,
                entity_id, payload in self.c.fetchall()
        ]

        next_revision = (
            changes[-1]["revision"]
            if changes else current_revision
        )

        return {
            "reset_required": False,
            "database_id": current_database_id,
            "revision": next_revision,
            "changes": changes,
            "has_more": next_revision < current_revision,
        }

    def sync_append_change(
        self, entity, operation, entity_id, payload=None
    ):
        """
        Must be called on the database thread inside the
        same transaction as the authoritative mutation.

        sync_append_change() is deliberately undecorated:
        it is an internal helper
        that should execute directly on the database thread,
        inside the caller's transaction.

        It should not be called as a standalone API operation.
        """
        self.c.execute(
            """
            INSERT INTO essential_changes
                (entity, operation, entity_id, payload)
            VALUES (?, ?, ?, ?)
            """,
            (
                entity,
                operation,
                entity_id,
                json.dumps(payload)
                if payload is not None else None,
            ),
        )
        return self.c.lastrowid
