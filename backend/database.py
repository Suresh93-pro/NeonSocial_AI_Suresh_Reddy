
# ============================================================
# NEONSOCIAL AI — DATABASE
# Built by SURESH REDDY
# ============================================================

import sqlite3
from pathlib import Path
from datetime import datetime, timezone


class Database:

    # ========================================================
    # INITIALIZE
    # ========================================================

    def __init__(self, path):

        self.path = Path(path)

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.init()

    # ========================================================
    # DATABASE CONNECTION
    # ========================================================

    def con(self):

        connection = sqlite3.connect(
            self.path,
            check_same_thread=False
        )

        connection.row_factory = sqlite3.Row

        return connection

    # ========================================================
    # CURRENT TIME
    # ========================================================

    def now(self):

        return datetime.now(
            timezone.utc
        ).isoformat()

    # ========================================================
    # INITIALIZE TABLES
    # ========================================================

    def init(self):

        connection = self.con()

        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT,
                title TEXT,
                content TEXT,
                status TEXT DEFAULT 'draft',
                scheduled_at TEXT,
                published_at TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                message TEXT,
                level TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS connections (
                platform TEXT PRIMARY KEY,
                account TEXT,
                status TEXT
            );

            CREATE TABLE IF NOT EXISTS chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                message TEXT,
                created_at TEXT
            );
            """
        )

        connection.commit()
        connection.close()

    # ========================================================
    # ACTIVITY
    # ========================================================

    def activity(
        self,
        action,
        message,
        level="info"
    ):

        connection = self.con()

        connection.execute(
            """
            INSERT INTO activity
            (action, message, level, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                action,
                message,
                level,
                self.now()
            )
        )

        connection.commit()
        connection.close()

    # ========================================================
    # CREATE POST
    # ========================================================

    def create(
        self,
        platform,
        title,
        content
    ):

        current_time = self.now()

        connection = self.con()

        cursor = connection.execute(
            """
            INSERT INTO posts
            (
                platform,
                title,
                content,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                platform,
                title,
                content,
                "pending_approval",
                current_time,
                current_time
            )
        )

        connection.commit()

        post_id = cursor.lastrowid

        connection.close()

        return post_id

    # ========================================================
    # GET ONE POST
    # ========================================================

    def get(self, post_id):

        connection = self.con()

        row = connection.execute(
            """
            SELECT *
            FROM posts
            WHERE id = ?
            """,
            (post_id,)
        ).fetchone()

        connection.close()

        if row:

            return dict(row)

        return None

    # ========================================================
    # GET ALL POSTS
    # ========================================================

    def posts(self):

        connection = self.con()

        rows = connection.execute(
            """
            SELECT *
            FROM posts
            ORDER BY id DESC
            """
        ).fetchall()

        connection.close()

        return [
            dict(row)
            for row in rows
        ]

    # ========================================================
    # UPDATE POST
    # ========================================================

    def update(
        self,
        post_id,
        **kwargs
    ):

        if not kwargs:

            return

        kwargs["updated_at"] = self.now()

        keys = list(kwargs.keys())

        assignments = ", ".join(
            f"{key} = ?"
            for key in keys
        )

        values = [
            kwargs[key]
            for key in keys
        ]

        values.append(post_id)

        connection = self.con()

        connection.execute(
            f"""
            UPDATE posts
            SET {assignments}
            WHERE id = ?
            """,
            values
        )

        connection.commit()
        connection.close()

    # ========================================================
    # ACTIVITY LIST
    # ========================================================

    def activities(self):

        connection = self.con()

        rows = connection.execute(
            """
            SELECT *
            FROM activity
            ORDER BY id DESC
            LIMIT 60
            """
        ).fetchall()

        connection.close()

        return [
            dict(row)
            for row in rows
        ]

    # ========================================================
    # CONNECT PLATFORM
    # ========================================================

    def connect(self, platform):

        connection = self.con()

        connection.execute(
            """
            INSERT OR REPLACE INTO connections
            (
                platform,
                account,
                status
            )
            VALUES (?, ?, ?)
            """,
            (
                platform,
                "Demo " + platform.title() + " Account",
                "connected"
            )
        )

        connection.commit()
        connection.close()

    # ========================================================
    # GET CONNECTIONS
    # ========================================================

    def connections(self):

        connection = self.con()

        rows = connection.execute(
            """
            SELECT *
            FROM connections
            """
        ).fetchall()

        connection.close()

        return [
            dict(row)
            for row in rows
        ]

    # ========================================================
    # DASHBOARD STATISTICS
    # ========================================================

    def stats(self):

        connection = self.con()

        stats = {}

        # ----------------------------------------------------
        # TOTAL
        # ----------------------------------------------------

        stats["total"] = connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM posts
            """
        ).fetchone()["n"]

        # ----------------------------------------------------
        # PENDING APPROVAL
        # ----------------------------------------------------

        stats["pending"] = connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM posts
            WHERE status = ?
            """,
            ("pending_approval",)
        ).fetchone()["n"]

        # ----------------------------------------------------
        # APPROVED
        # ----------------------------------------------------

        stats["approved"] = connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM posts
            WHERE status = ?
            """,
            ("approved",)
        ).fetchone()["n"]

        # ----------------------------------------------------
        # SCHEDULED
        # ----------------------------------------------------

        stats["scheduled"] = connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM posts
            WHERE status = ?
            """,
            ("scheduled",)
        ).fetchone()["n"]

        # ----------------------------------------------------
        # PUBLISHED
        # ----------------------------------------------------

        stats["published"] = connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM posts
            WHERE status = ?
            """,
            ("published",)
        ).fetchone()["n"]

        # ----------------------------------------------------
        # REJECTED
        # ----------------------------------------------------

        stats["rejected"] = connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM posts
            WHERE status = ?
            """,
            ("rejected",)
        ).fetchone()["n"]

        connection.close()

        return stats

    # ========================================================
    # CHAT HISTORY
    # ========================================================

    def chatadd(
        self,
        role,
        message
    ):

        connection = self.con()

        connection.execute(
            """
            INSERT INTO chat
            (
                role,
                message,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                role,
                message,
                self.now()
            )
        )

        connection.commit()
        connection.close()

    # ========================================================
    # GET CHAT HISTORY
    # ========================================================

    def chats(self):

        connection = self.con()

        rows = connection.execute(
            """
            SELECT *
            FROM chat
            ORDER BY id ASC
            """
        ).fetchall()

        connection.close()

        return [
            dict(row)
            for row in rows
        ]

