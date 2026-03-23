"""
カテゴリ管理モジュール
"""
import sqlite3

from auth import get_db

DB_FILE = "todo_users.db"


def init_categories_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, name)
        )
    """)
    conn.commit()
    conn.close()


def get_categories(user_id):
    """ユーザーのカテゴリ一覧を取得"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name FROM categories WHERE user_id = ? ORDER BY name",
        (user_id,),
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "name": r["name"]} for r in rows]


def get_category_names(user_id):
    """カテゴリ名のリストのみ取得（フォーム用）"""
    cats = get_categories(user_id)
    return [""] + [c["name"] for c in cats]


def add_category(user_id, name):
    """カテゴリを追加"""
    name = name.strip()
    if not name:
        return False, "カテゴリ名を入力してください"
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO categories (user_id, name) VALUES (?, ?)",
            (user_id, name),
        )
        conn.commit()
        conn.close()
        return True, None
    except sqlite3.IntegrityError:
        conn.close()
        return False, "同じ名前のカテゴリが既にあります"


def delete_category(user_id, category_id):
    """カテゴリを削除（自分のもののみ）"""
    conn = get_db()
    conn.execute(
        "DELETE FROM categories WHERE id = ? AND user_id = ?",
        (category_id, user_id),
    )
    conn.commit()
    conn.close()
