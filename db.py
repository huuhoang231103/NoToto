import os
import sqlite3
from pathlib import Path

APP_NAME = "NoToto"

def data_dir() -> Path:
    base = os.getenv("LOCALAPPDATA")
    path = Path(base) / APP_NAME if base else Path.home() / ".nototo"
    path.mkdir(parents=True, exist_ok=True)
    return path

DB_PATH = data_dir() / "nototo.db"

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _columns(conn, table):
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}

def _add_column_if_missing(conn, table, name, ddl):
    if name not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")

def init_db():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            start_time TEXT DEFAULT '',
            end_time TEXT DEFAULT '',
            estimated_minutes INTEGER NOT NULL DEFAULT 0,
            worked_seconds INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            started_at TEXT NOT NULL,
            ended_at TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL DEFAULT 0,
            mode TEXT NOT NULL DEFAULT 'focus',
            FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
        );
        """)
        _add_column_if_missing(conn, "tasks", "priority", "TEXT NOT NULL DEFAULT 'medium'")
        _add_column_if_missing(conn, "tasks", "category", "TEXT NOT NULL DEFAULT 'Study'")

def list_tasks():
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY completed ASC, id DESC"
        ).fetchall()
        return [dict(r) for r in rows]

def get_task(task_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return dict(row) if row else None

def get_subtasks(task_id):
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM subtasks WHERE task_id=? ORDER BY sort_order ASC, id ASC",
            (task_id,),
        ).fetchall()
        return [dict(r) for r in rows]

def save_subtasks(task_id, subtasks):
    with connect() as conn:
        conn.execute("DELETE FROM subtasks WHERE task_id=?", (task_id,))
        for idx, item in enumerate(subtasks):
            conn.execute(
                "INSERT INTO subtasks(task_id,title,completed,sort_order) VALUES(?,?,?,?)",
                (task_id, item["title"], 1 if item.get("completed") else 0, idx),
            )

def toggle_subtask(subtask_id):
    with connect() as conn:
        conn.execute(
            "UPDATE subtasks SET completed = CASE WHEN completed=1 THEN 0 ELSE 1 END WHERE id=?",
            (subtask_id,),
        )

def add_task(title, start_time, end_time, estimated_minutes, worked_seconds,
             completed=False, priority="medium", category="Study", subtasks=None):
    with connect() as conn:
        cur = conn.execute("""
            INSERT INTO tasks(
                title,start_time,end_time,estimated_minutes,worked_seconds,
                completed,priority,category,completed_at
            ) VALUES(?,?,?,?,?,?,?,?,CASE WHEN ?=1 THEN CURRENT_TIMESTAMP ELSE NULL END)
        """, (
            title, start_time, end_time, int(estimated_minutes), int(worked_seconds),
            1 if completed else 0, priority, category, 1 if completed else 0
        ))
        task_id = cur.lastrowid

    if subtasks:
        save_subtasks(task_id, subtasks)
    return task_id

def update_task(task_id, title, start_time, end_time, estimated_minutes,
                worked_seconds, completed, priority, category, subtasks=None):
    with connect() as conn:
        conn.execute("""
            UPDATE tasks SET
                title=?, start_time=?, end_time=?,
                estimated_minutes=?, worked_seconds=?,
                completed=?, priority=?, category=?,
                completed_at=CASE
                    WHEN ?=1 AND completed_at IS NULL THEN CURRENT_TIMESTAMP
                    WHEN ?=0 THEN NULL
                    ELSE completed_at
                END
            WHERE id=?
        """, (
            title, start_time, end_time, int(estimated_minutes), int(worked_seconds),
            1 if completed else 0, priority, category,
            1 if completed else 0, 1 if completed else 0, task_id
        ))
    save_subtasks(task_id, subtasks or [])

def set_task_completed(task_id, completed):
    with connect() as conn:
        conn.execute("""
            UPDATE tasks
            SET completed=?,
                completed_at=CASE
                    WHEN ?=1 THEN COALESCE(completed_at,CURRENT_TIMESTAMP)
                    ELSE NULL
                END
            WHERE id=?
        """, (1 if completed else 0, 1 if completed else 0, task_id))

def delete_task(task_id):
    with connect() as conn:
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))

def add_worked_seconds(task_id, seconds):
    if not task_id or seconds <= 0:
        return
    with connect() as conn:
        conn.execute(
            "UPDATE tasks SET worked_seconds=worked_seconds+? WHERE id=?",
            (int(seconds), task_id),
        )

def add_session(task_id, started_at, ended_at, duration_seconds, mode):
    with connect() as conn:
        conn.execute("""
            INSERT INTO sessions(task_id,started_at,ended_at,duration_seconds,mode)
            VALUES(?,?,?,?,?)
        """, (task_id, started_at, ended_at, int(duration_seconds), mode))

def session_count(mode=None):
    with connect() as conn:
        if mode:
            row = conn.execute("SELECT COUNT(*) AS n FROM sessions WHERE mode=?", (mode,)).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) AS n FROM sessions").fetchone()
        return int(row["n"])

def total_worked_seconds():
    with connect() as conn:
        row = conn.execute("SELECT COALESCE(SUM(worked_seconds),0) AS n FROM tasks").fetchone()
        return int(row["n"])

def get_setting(key, default=""):
    with connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

def set_setting(key, value):
    with connect() as conn:
        conn.execute("""
            INSERT INTO settings(key,value) VALUES(?,?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """, (key, str(value)))
