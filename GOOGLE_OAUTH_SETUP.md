# Googleログインの設定手順

## 1. Google Cloud Console で OAuth 2.0 クライアントを作成

1. [Google Cloud Console](https://console.cloud.google.com/) にログイン
2. プロジェクトを選択（スプレッドシート用と同じでOK）
3. **APIとサービス** → **認証情報** → **認証情報を作成** → **OAuth クライアント ID**
4. 初回は「アプリケーションの種類」で **ウェブアプリケーション** を選択
5. **名前** を入力（例: Todoアプリ Web クライアント）
6. **承認済みのリダイレクト URI** に以下を追加：
   - ローカル: `http://127.0.0.1:5000/auth/google/callback`
   - Render: `https://あなたのサービス名.onrender.com/auth/google/callback`
7. **作成** をクリック
8. 表示された **クライアント ID** と **クライアント シークレット** を控える

---

## 2. 環境変数を設定

### ローカル（PowerShell）

```powershell
$env:GOOGLE_CLIENT_ID = "xxxxx.apps.googleusercontent.com"
$env:GOOGLE_CLIENT_SECRET = "GOCSPX-xxxxx"
```

### Render

**Environment** セクションに追加：

| Key | Value |
|-----|-------|
| `GOOGLE_CLIENT_ID` | クライアント ID |
| `GOOGLE_CLIENT_SECRET` | クライアント シークレット |

---

## 3. 動作確認

- 環境変数を設定すると、ログイン画面に「Googleでログイン」ボタンが表示されます
- 未設定の場合は従来のユーザー名/パスワードログインのみ表示されます

---

## 注意

- OAuth クライアントは**サービスアカウント**とは別物です（同じプロジェクト内で両方作成可能）
- 本番環境では「本番環境」としてアプリを申請する必要がある場合があります（テスト時は自分のGoogleアカウントのみ利用可能）
