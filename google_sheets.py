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

    # ヘッダー行がなければ作成
    if not worksheet.cell(1, 1).value:
        worksheet.update("A1:D1", [["ID", "タイトル", "内容", "期日"]])
        worksheet.format("A1:D1", {"textFormat": {"bold": True}})

    return worksheet


def get_all_todos(worksheet):
    """全Todoを取得（列位置で固定: A=ID, B=タイトル, C=内容, D=期日）"""
    values = worksheet.get_all_values()
    if not values:
        return []

    # 1行目が「ID」ならヘッダー行としてスキップ、そうでなければデータとして扱う
    first_cell = (values[0][0] if values[0] else "").strip()
    data_rows = values[1:] if first_cell == "ID" else values

    todos = []
    for row_values in data_rows:
        todo_id = (row_values[0] if len(row_values) > 0 else "").strip()
        if todo_id and todo_id.isdigit():
            todos.append({
                "id": todo_id,
                "title": row_values[1] if len(row_values) > 1 else "",
                "content": row_values[2] if len(row_values) > 2 else "",
                "due_date": row_values[3] if len(row_values) > 3 else "",
            })
    return todos


def add_todo(worksheet, title, content, due_date):
    """Todoを追加"""
    records = worksheet.get_all_records()
    next_id = 1
    if records:
        ids = [int(r.get("ID", 0)) for r in records if r.get("ID")]
        if ids:
            next_id = max(ids) + 1

    worksheet.append_row([next_id, title, content, due_date])
    return next_id


def update_todo(worksheet, row, title, content, due_date):
    """Todoを更新"""
    worksheet.update(f"B{row}:D{row}", [[title, content, due_date]])


def delete_todo(worksheet, row):
    """Todoを削除（行をクリア）"""
    worksheet.update(f"A{row}:D{row}", [["", "", "", ""]])


def find_todo_row(worksheet, todo_id):
    """IDから行番号を取得"""
    cell = worksheet.find(str(todo_id), in_column=1)
    return cell.row if cell else None
