"""
Todoリスト Webアプリ - Flask + Googleスプレッドシート
"""
import os

from flask import Flask, render_template, request, redirect, url_for, flash

from google_sheets import (
    get_sheet,
    get_all_todos,
    add_todo,
    update_todo,
    delete_todo,
    find_todo_row,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")


def get_worksheet():
    """ワークシートを取得（エラーハンドリング付き）"""
    try:
        return get_sheet()
    except Exception as e:
        flash(f"Googleスプレッドシートの接続に失敗しました: {e}", "error")
        return None


@app.route("/")
def index():
    """一覧表示"""
    worksheet = get_worksheet()
    if worksheet is None:
        return render_template("index.html", todos=[])

    todos = get_all_todos(worksheet)
    return render_template("index.html", todos=todos)


@app.route("/add", methods=["GET", "POST"])
def add():
    """新規登録"""
    if request.method == "GET":
        return render_template("form.html", todo=None, action="add")

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    due_date = request.form.get("due_date", "").strip()

    if not title:
        flash("タイトルは必須です。", "error")
        return render_template("form.html", todo={"title": title, "content": content, "due_date": due_date}, action="add")

    worksheet = get_worksheet()
    if worksheet is None:
        return redirect(url_for("index"))

    add_todo(worksheet, title, content, due_date)
    flash("Todoを追加しました。", "success")
    return redirect(url_for("index"))


@app.route("/edit/<todo_id>", methods=["GET", "POST"])
def edit(todo_id):
    """編集"""
    worksheet = get_worksheet()
    if worksheet is None:
        return redirect(url_for("index"))

    row = find_todo_row(worksheet, todo_id)
    if row is None:
        flash("該当するTodoが見つかりません。", "error")
        return redirect(url_for("index"))

    if request.method == "GET":
        todos = get_all_todos(worksheet)
        todo = next((t for t in todos if t["id"] == todo_id), None)
        if todo is None:
            flash("該当するTodoが見つかりません。", "error")
            return redirect(url_for("index"))
        return render_template("form.html", todo=todo, action="edit")

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    due_date = request.form.get("due_date", "").strip()

    if not title:
        flash("タイトルは必須です。", "error")
        return render_template(
            "form.html",
            todo={"id": todo_id, "title": title, "content": content, "due_date": due_date},
            action="edit",
        )

    update_todo(worksheet, row, title, content, due_date)
    flash("Todoを更新しました。", "success")
    return redirect(url_for("index"))


@app.route("/delete/<todo_id>", methods=["POST"])
def delete(todo_id):
    """削除"""
    worksheet = get_worksheet()
    if worksheet is None:
        return redirect(url_for("index"))

    row = find_todo_row(worksheet, todo_id)
    if row is None:
        flash("該当するTodoが見つかりません。", "error")
        return redirect(url_for("index"))

    delete_todo(worksheet, row)
    flash("Todoを削除しました。", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
