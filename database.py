import os
import sqlite3
from datetime import date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            role     TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        INSERT INTO users (username, password, role)
        SELECT 'admin', '123', 'admin'
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin')
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date   TEXT NOT NULL,
            reason     TEXT,
            leave_days INTEGER NOT NULL DEFAULT 0,
            status     TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # Migrate existing table: add columns if they don't exist yet
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN full_name TEXT NOT NULL DEFAULT ""')
    except Exception:
        pass  # Column already exists
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1')
    except Exception:
        pass  # Column already exists
    for col, definition in [('reason', 'TEXT'), ('leave_days', 'INTEGER NOT NULL DEFAULT 0')]:
        try:
            cursor.execute(f'ALTER TABLE leave_requests ADD COLUMN {col} {definition}')
        except Exception:
            pass  # Column already exists
    # Rename working_days -> leave_days if the old column still exists
    try:
        cursor.execute('ALTER TABLE leave_requests RENAME COLUMN working_days TO leave_days')
    except Exception:
        pass  # Already renamed or column doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_balance (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            year            INTEGER NOT NULL,
            total_days      INTEGER NOT NULL DEFAULT 15,
            carry_over_days INTEGER NOT NULL DEFAULT 0,
            UNIQUE(user_id, year),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # Seed existing employees with a full 15-day allocation for the current year
    current_year = date.today().year
    cursor.execute('''
        INSERT OR IGNORE INTO leave_balance (user_id, year, total_days, carry_over_days)
        SELECT id, ?, 15, 0 FROM users WHERE role = 'employee'
    ''', (current_year,))
    conn.commit()
    conn.close()
