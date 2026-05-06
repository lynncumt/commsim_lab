import sqlite3
import hashlib
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'users.db')


def _get_db_path():
    """Return absolute path to the SQLite database, creating parent dirs if needed."""
    base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, '..', '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'users.db')


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def init_db():
    db = _get_db_path()
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            real_name TEXT DEFAULT '',
            student_id TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            module_key TEXT NOT NULL,
            last_accessed TEXT NOT NULL,
            times_visited INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            UNIQUE(user_id, module_key),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Seed a default admin account so the software works out-of-the-box
    if not get_user('admin'):
        create_user('admin', 'admin123', real_name='管理员', student_id='0000')
    conn.commit()
    conn.close()


def create_user(username: str, password: str, real_name: str = '', student_id: str = '') -> bool:
    db = _get_db_path()
    conn = sqlite3.connect(db)
    c = conn.cursor()
    try:
        c.execute(
            'INSERT INTO users (username, password_hash, real_name, student_id, created_at) VALUES (?,?,?,?,?)',
            (username, _hash_password(password), real_name, student_id, datetime.now().isoformat())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user(username: str):
    db = _get_db_path()
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('SELECT id, username, real_name, student_id FROM users WHERE username=?', (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'username': row[1], 'real_name': row[2], 'student_id': row[3]}
    return None


def authenticate(username: str, password: str):
    db = _get_db_path()
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('SELECT id, username, real_name, student_id, password_hash FROM users WHERE username=?', (username,))
    row = c.fetchone()
    conn.close()
    if row and row[4] == _hash_password(password):
        return {'id': row[0], 'username': row[1], 'real_name': row[2], 'student_id': row[3]}
    return None


def record_progress(user_id: int, module_key: str, notes: str = ''):
    db = _get_db_path()
    conn = sqlite3.connect(db)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
        INSERT INTO progress (user_id, module_key, last_accessed, times_visited, notes)
        VALUES (?, ?, ?, 1, ?)
        ON CONFLICT(user_id, module_key) DO UPDATE SET
            last_accessed=excluded.last_accessed,
            times_visited=times_visited+1,
            notes=CASE WHEN excluded.notes!='' THEN excluded.notes ELSE notes END
    ''', (user_id, module_key, now, notes))
    conn.commit()
    conn.close()


def get_progress(user_id: int):
    db = _get_db_path()
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('SELECT module_key, last_accessed, times_visited, notes FROM progress WHERE user_id=?', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{'module': r[0], 'last_accessed': r[1], 'times_visited': r[2], 'notes': r[3]} for r in rows]


def change_password(username: str, old_password: str, new_password: str) -> bool:
    if not authenticate(username, old_password):
        return False
    db = _get_db_path()
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('UPDATE users SET password_hash=? WHERE username=?', (_hash_password(new_password), username))
    conn.commit()
    conn.close()
    return True
