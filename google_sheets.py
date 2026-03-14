"""
Googleスプレッドシートとの連携モジュール
"""
import json
import os

import gspread
from google.oauth2.service_account import Credentials


# スコープ設定（スプレッドシートとドライブの読み書き）
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_credentials():
    """環境変数またはファイルから認証情報を取得"""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        # Render等：環境変数にJSON文字列を設定
        info = json.loads(creds_json)
        return Credentials.from_service_account_info(info, scopes=SCOPES)

    # ローカル：credentials.json ファイルを使用
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    return Credentials.from_service_account_file(creds_path, scopes=SCOPES)


def get_sheet():
    """
    Googleスプレッドシートのワークシートを取得
    - ローカル: credentials.json または GOOGLE_CREDENTIALS_PATH
    - Render等: GOOGLE_CREDENTIALS_JSON に credentials.json の内容をそのまま設定
    """
    spreadsheet_id = os.environ.get("SPREADSHEET_ID", "")

    if not spreadsheet_id:
        raise ValueError(
            "SPREADSHEET_ID 環境変数を設定してください。"
            "スプレッドシートのURLの /d/ と /edit の間の文字列です。"
        )

    credentials = _get_credentials()
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.sheet1

    # ヘッダー行がなければ作成（A=ID, B=タイトル, C=内容, D=期日, E=カテゴリ, F=完了, G=user_id）
    if not worksheet.cell(1, 1).value:
        worksheet.update("A1:G1", [["ID", "タイトル", "内容", "期日", "カテゴリ", "完了", "user_id"]])
        worksheet.format("A1:G1", {"textFormat": {"bold": True}})

    return worksheet


def get_all_todos(worksheet, user_id=None):
    """全Todoを取得。user_id指定時はそのユーザーのTodoのみ（user_id空は従来データとして全員に表示）"""
    values = worksheet.get_all_values()
    if not values:
        return []

    first_cell = (values[0][0] if values[0] else "").strip()
    data_rows = values[1:] if first_cell == "ID" else values

    todos = []
    for row_values in data_rows:
        todo_id = (row_values[0] if len(row_values) > 0 else "").strip()
        if not todo_id or not todo_id.isdigit():
            continue
        row_user_id = row_values[6] if len(row_values) > 6 else ""
        if user_id and row_user_id and row_user_id != str(user_id):
            continue
        todos.append({
            "id": todo_id,
            "title": row_values[1] if len(row_values) > 1 else "",
            "content": row_values[2] if len(row_values) > 2 else "",
            "due_date": row_values[3] if len(row_values) > 3 else "",
            "category": row_values[4] if len(row_values) > 4 else "",
            "completed": (row_values[5] if len(row_values) > 5 else "").strip().lower() in ("1", "○", "true", "完了"),
        })
    return todos


def add_todo(worksheet, title, content, due_date, category="", user_id=""):
    """Todoを追加"""
    values = worksheet.get_all_values()
    next_id = 1
    if len(values) > 1:
        ids = []
        first_cell = (values[0][0] if values[0] else "").strip()
        data_rows = values[1:] if first_cell == "ID" else values
        for row in data_rows:
            vid = (row[0] if len(row) > 0 else "").strip()
            if vid.isdigit():
                ids.append(int(vid))
        if ids:
            next_id = max(ids) + 1

    worksheet.append_row([next_id, title, content, due_date, category, "", str(user_id)])
    return next_id


def update_todo(worksheet, row, title, content, due_date, category=""):
    """Todoを更新"""
    worksheet.update(f"B{row}:E{row}", [[title, content, due_date, category]])


def toggle_complete(worksheet, row, completed):
    """Todoの完了状態を切り替え"""
    worksheet.update(f"F{row}", [["1" if completed else ""]])


def delete_todo(worksheet, row):
    """Todoを削除（行をクリア）"""
    worksheet.update(f"A{row}:G{row}", [["", "", "", "", "", "", ""]])


def find_todo_row(worksheet, todo_id):
    """IDから行番号を取得"""
    cell = worksheet.find(str(todo_id), in_column=1)
    return cell.row if cell else None
