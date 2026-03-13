# Todoリスト Webアプリ

Flask + Googleスプレッドシートで動作するTodoリストアプリです。  
タイトル・内容・期日を登録・編集・一覧表示できます。

## セットアップ手順

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. Google Cloud の設定

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. **APIとサービス** → **ライブラリ** で以下を有効化：
   - Google Sheets API
   - Google Drive API
3. **APIとサービス** → **認証情報** → **認証情報を作成** → **サービス アカウント**
4. サービスアカウントを作成し、**キー** タブから **鍵を追加** → **新しい鍵を作成** → **JSON**
5. ダウンロードしたJSONファイルをプロジェクトフォルダに `credentials.json` として保存

### 3. Googleスプレッドシートの準備

1. [Googleスプレッドシート](https://sheets.google.com/) で新しいスプレッドシートを作成
2. スプレッドシートのURLから **スプレッドシートID** を取得  
   （例: `https://docs.google.com/spreadsheets/d/【ここがID】/edit`）
3. スプレッドシートを **共有** し、サービスアカウントのメールアドレス（`credentials.json` の `client_email`）を **編集者** として追加

### 4. 環境変数の設定

PowerShell の場合：

```powershell
$env:SPREADSHEET_ID = "あなたのスプレッドシートID"
$env:GOOGLE_CREDENTIALS_PATH = "credentials.json"  # 省略時は credentials.json
```

または、`credentials.json` をプロジェクト直下に置き、`SPREADSHEET_ID` のみ設定してください。

### 5. アプリの起動

```bash
python app.py
```

ブラウザで http://127.0.0.1:5000 にアクセスしてください。

## 機能

- **一覧表示**: 登録済みTodoをテーブルで表示
- **新規登録**: タイトル・内容・期日を入力して追加
- **編集**: 既存Todoの内容を変更
- **削除**: Todoを削除

## ファイル構成

```
ToDoLIST WebApp/
├── app.py              # Flaskアプリ本体
├── google_sheets.py    # Googleスプレッドシート連携
├── requirements.txt
├── credentials.json    # サービスアカウント鍵（要配置）
├── README.md
└── templates/
    ├── base.html
    ├── index.html
    └── form.html
```

## 注意事項

- `credentials.json` は **絶対にGitにコミットしない** でください
- 本番環境では `app.secret_key` を適切な値に変更してください
