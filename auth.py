"""
認証モジュール - Flask-Login + SQLite
"""
import os
import sqlite3
from functools import wraps

from flask import redirect, url_for, request
from flask_login import LoginManager, UserMixin, current_user
from werkzeug.security import check_password_hash, generate_password_hash

DB_FILE = "todo_users.db"


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            google_id TEXT UNIQUE,
            email TEXT,
            font_preference TEXT DEFAULT 'gothic',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    # 既存テーブルにカラム追加（マイグレーション）
    for col in ["google_id", "email", "font_preference", "theme_preference"]:
        try:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass
    conn.close()


def get_user_font(user_id):
    """ユーザーのフォント設定を取得"""
    conn = get_db()
    row = conn.execute(
        "SELECT font_preference FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return (row["font_preference"] or "gothic") if row else "gothic"


def set_user_font(user_id, font):
    """ユーザーのフォント設定を保存"""
    if font not in ("handwritten", "mincho", "gothic"):
        font = "gothic"
    conn = get_db()
    conn.execute("UPDATE users SET font_preference = ? WHERE id = ?", (font, user_id))
    conn.commit()
    conn.close()


def get_user_theme(user_id):
    """ユーザーのテーマ設定を取得"""
    conn = get_db()
    row = conn.execute(
        "SELECT theme_preference FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return (row["theme_preference"] or "paper") if row else "paper"


def set_user_theme(user_id, theme):
    """ユーザーのテーマ設定を保存"""
    valid = ("paper", "blue", "green", "lavender", "mono", "pink", "orange")
    if theme not in valid:
        theme = "paper"
    conn = get_db()
    conn.execute("UPDATE users SET theme_preference = ? WHERE id = ?", (theme, user_id))
    conn.commit()
    conn.close()


class User(UserMixin):
    def __init__(self, id_, username):
        self.id = id_
        self.username = username or ""

    @staticmethod
    def get(user_id):
        conn = get_db()
        row = conn.execute(
            "SELECT id, username, email FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        conn.close()
        if row:
            name = row["username"] or row["email"] or str(row["id"])
            return User(row["id"], name)
        return None

    @staticmethod
    def get_by_username(username):
        conn = get_db()
        row = conn.execute("SELECT id, username, email FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if row:
            name = row["username"] or row["email"] or str(row["id"])
            return User(row["id"], name)
        return None

    @staticmethod
    def get_by_google_id(google_id):
        conn = get_db()
        row = conn.execute(
            "SELECT id, username, email FROM users WHERE google_id = ?",
            (str(google_id),),
        ).fetchone()
        conn.close()
        if row:
            name = row["email"] or row["username"] or str(row["id"])
            return User(row["id"], name)
        return None

    @staticmethod
    def create(username, password):
        password_hash = generate_password_hash(password, method="pbkdf2:sha256")
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
            conn.commit()
            row = conn.execute("SELECT id, username, email FROM users WHERE username = ?", (username,)).fetchone()
            conn.close()
            return User(row["id"], row["username"] or row["email"])
        except sqlite3.IntegrityError:
            conn.close()
            return None

    @staticmethod
    def create_from_google(google_id, email, name=None):
        """Googleログインでユーザー作成または取得"""
        user = User.get_by_google_id(google_id)
        if user:
            return user
        conn = get_db()
        try:
            # usernameはemailを使用（一意性のため）
            conn.execute(
                "INSERT INTO users (google_id, email, username) VALUES (?, ?, ?)",
                (str(google_id), email or "", email or str(google_id)),
            )
            conn.commit()
            row = conn.execute(
                "SELECT id, username, email FROM users WHERE google_id = ?",
                (str(google_id),),
            ).fetchone()
            conn.close()
            return User(row["id"], row["email"] or row["username"])
        except sqlite3.IntegrityError:
            conn.close()
            return User.get_by_google_id(google_id)

    @staticmethod
    def verify(username, password):
        conn = get_db()
        row = conn.execute(
            "SELECT id, username, email, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        conn.close()
        if row and row["password_hash"] and check_password_hash(row["password_hash"], password):
            name = row["username"] or row["email"] or str(row["id"])
            return User(row["id"], name)
        return None


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function
