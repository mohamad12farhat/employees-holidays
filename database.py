import sqlite3


def init_db():
    conn = sqlite3.connect('database.db')
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
    conn.commit()
    conn.close()
