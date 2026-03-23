"""
Todoリスト Webアプリ - Flask + Googleスプレッドシート
"""
import os

from authlib.integrations.flask_client import OAuth
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, current_user

from auth import User, init_db, login_required, get_user_font, set_user_font, get_user_theme, set_user_theme
from categories import (
    init_categories_db,
    get_categories,
    get_category_names,
    add_category,
    delete_category,
)
from google_sheets import (
    get_sheet,
    get_all_todos,
    add_todo,
    update_todo,
    delete_todo,
    toggle_complete,
    find_todo_row,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

init_db()
init_categories_db()

# Google OAuth
oauth = OAuth(app)
oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "ログインしてください。"


@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))


@app.context_processor
def inject_user_prefs():
    """全テンプレートにフォント・テーマ設定を渡す"""
    if current_user.is_authenticated:
        return {"font_pref": get_user_font(current_user.id), "theme_pref": get_user_theme(current_user.id)}
    return {"font_pref": "gothic", "theme_pref": "paper"}


def get_worksheet():
    """ワークシートを取得（エラーハンドリング付き）"""
    try:
        return get_sheet()
    except Exception as e:
        flash(f"Googleスプレッドシートの接続に失敗しました: {e}", "error")
        return None


@app.route("/login", methods=["GET", "POST"])
def login():
    """ログイン"""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "GET":
        return render_template("login.html", google_enabled=bool(os.environ.get("GOOGLE_CLIENT_ID")))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("ユーザー名とパスワードを入力してください。", "error")
        return render_template("login.html", google_enabled=bool(os.environ.get("GOOGLE_CLIENT_ID")))

    user = User.verify(username, password)
    if user:
        login_user(user)
        next_url = request.args.get("next") or url_for("index")
        return redirect(next_url)

    flash("ユーザー名またはパスワードが正しくありません。", "error")
    return render_template("login.html", google_enabled=bool(os.environ.get("GOOGLE_CLIENT_ID")))


@app.route("/login/google")
def login_google():
    """Googleログイン開始"""
    if not os.environ.get("GOOGLE_CLIENT_ID"):
        flash("Googleログインは設定されていません。", "error")
        return redirect(url_for("login"))
    redirect_uri = url_for("auth_google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/auth/google/callback")
def auth_google_callback():
    """Googleログインコールバック"""
    try:
        token = oauth.google.authorize_access_token()
    except Exception as e:
        flash(f"Googleログインに失敗しました: {e}", "error")
        return redirect(url_for("login"))

    user_info = token.get("userinfo")
    if not user_info:
        flash("Googleからユーザー情報を取得できませんでした。", "error")
        return redirect(url_for("login"))

    user = User.create_from_google(
        google_id=user_info["sub"],
        email=user_info.get("email", ""),
        name=user_info.get("name"),
    )
    login_user(user)
    flash("Googleでログインしました。", "success")
    next_url = request.args.get("next") or url_for("index")
    return redirect(next_url)


@app.route("/register", methods=["GET", "POST"])
def register():
    """新規登録"""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")

    if not username or not password:
        flash("ユーザー名とパスワードを入力してください。", "error")
        return render_template("register.html")

    if password != password_confirm:
        flash("パスワードが一致しません。", "error")
        return render_template("register.html")

    if len(password) < 4:
        flash("パスワードは4文字以上にしてください。", "error")
        return render_template("register.html")

    user = User.create(username, password)
    if user:
        login_user(user)
        flash("登録が完了しました。", "success")
        return redirect(url_for("index"))

    flash("このユーザー名は既に使用されています。", "error")
    return render_template("register.html")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """設定（フォント・カテゴリ）"""
    if request.method == "POST":
        # フォント変更
        if request.form.get("font"):
            font = request.form.get("font", "gothic")
            set_user_font(current_user.id, font)
            flash("フォントを変更しました。", "success")
            return redirect(url_for("settings"))
        if request.form.get("theme"):
            theme = request.form.get("theme", "paper")
            set_user_theme(current_user.id, theme)
            flash("テーマを変更しました。", "success")
            return redirect(url_for("settings"))
        # カテゴリ追加
        if "category_name" in request.form:
            ok, err = add_category(current_user.id, request.form.get("category_name", ""))
            if ok:
                flash("カテゴリを追加しました。", "success")
            else:
                flash(err, "error")
            return redirect(url_for("settings"))
        # カテゴリ削除
        if "delete_category_id" in request.form:
            delete_category(current_user.id, request.form["delete_category_id"])
            flash("カテゴリを削除しました。", "success")
            return redirect(url_for("settings"))

    categories_list = get_categories(current_user.id)
    current_font = get_user_font(current_user.id)
    current_theme = get_user_theme(current_user.id)
    return render_template(
        "settings.html",
        categories=categories_list,
        font=current_font,
        theme=current_theme,
    )


@app.route("/logout")
def logout():
    """ログアウト"""
    logout_user()
    flash("ログアウトしました。", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    """一覧表示"""
    worksheet = get_worksheet()
    categories = get_category_names(current_user.id)
    if worksheet is None:
        return render_template("index.html", todos=[], categories=categories, font=get_user_font(current_user.id))

    category_filter = request.args.get("category", "")
    todos = get_all_todos(worksheet, user_id=current_user.id)
    if category_filter:
        todos = [t for t in todos if t["category"] == category_filter]

    return render_template(
        "index.html",
        todos=todos,
        categories=categories,
        category_filter=category_filter,
        font=get_user_font(current_user.id),
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """新規登録"""
    categories = get_category_names(current_user.id)
    if request.method == "GET":
        return render_template("form.html", todo=None, action="add", categories=categories, font=get_user_font(current_user.id))

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    due_date = request.form.get("due_date", "").strip()
    category = request.form.get("category", "").strip()

    if not title:
        flash("タイトルは必須です。", "error")
        return render_template(
            "form.html",
            todo={"title": title, "content": content, "due_date": due_date, "category": category},
            action="add",
            categories=categories,
            font=get_user_font(current_user.id),
        )

    worksheet = get_worksheet()
    if worksheet is None:
        return redirect(url_for("index"))

    add_todo(worksheet, title, content, due_date, category=category, user_id=current_user.id)
    flash("Todoを追加しました。", "success")
    return redirect(url_for("index"))


@app.route("/edit/<todo_id>", methods=["GET", "POST"])
@login_required
def edit(todo_id):
    """編集"""
    worksheet = get_worksheet()
    if worksheet is None:
        return redirect(url_for("index"))

    row = find_todo_row(worksheet, todo_id)
    if row is None:
        flash("該当するTodoが見つかりません。", "error")
        return redirect(url_for("index"))

    categories = get_category_names(current_user.id)
    if request.method == "GET":
        todos = get_all_todos(worksheet, user_id=current_user.id)
        todo = next((t for t in todos if t["id"] == todo_id), None)
        if todo is None:
            flash("該当するTodoが見つかりません。", "error")
            return redirect(url_for("index"))
        return render_template("form.html", todo=todo, action="edit", categories=categories, font=get_user_font(current_user.id))

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    due_date = request.form.get("due_date", "").strip()
    category = request.form.get("category", "").strip()

    if not title:
        flash("タイトルは必須です。", "error")
        return render_template(
            "form.html",
            todo={"id": todo_id, "title": title, "content": content, "due_date": due_date, "category": category},
            action="edit",
            categories=categories,
            font=get_user_font(current_user.id),
        )

    update_todo(worksheet, row, title, content, due_date, category=category)
    flash("Todoを更新しました。", "success")
    return redirect(url_for("index"))


@app.route("/toggle/<todo_id>", methods=["POST"])
@login_required
def toggle(todo_id):
    """完了状態の切り替え"""
    worksheet = get_worksheet()
    if worksheet is None:
        return redirect(url_for("index"))

    row = find_todo_row(worksheet, todo_id)
    if row is None:
        flash("該当するTodoが見つかりません。", "error")
        return redirect(url_for("index"))

    todos = get_all_todos(worksheet, user_id=current_user.id)
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if todo is None:
        flash("該当するTodoが見つかりません。", "error")
        return redirect(url_for("index"))

    toggle_complete(worksheet, row, not todo["completed"])
    flash("完了状態を更新しました。", "success")
    return redirect(url_for("index"))


@app.route("/delete/<todo_id>", methods=["POST"])
@login_required
def delete(todo_id):
    """削除"""
    worksheet = get_worksheet()
    if worksheet is None:
        return redirect(url_for("index"))

    row = find_todo_row(worksheet, todo_id)
    if row is None:
        flash("該当するTodoが見つかりません。", "error")
        return redirect(url_for("index"))

    todos = get_all_todos(worksheet, user_id=current_user.id)
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if todo is None:
        flash("該当するTodoが見つかりません。", "error")
        return redirect(url_for("index"))

    delete_todo(worksheet, row)
    flash("Todoを削除しました。", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
