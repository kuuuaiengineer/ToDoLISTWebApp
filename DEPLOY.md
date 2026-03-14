# Render へのデプロイ手順

## 1. GitHub にプッシュ

プロジェクトをGitHubリポジトリにプッシュします。

```powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git
git push -u origin main
```

※ `credentials.json` は `.gitignore` に含まれているため、プッシュされません。

---

## 2. Render で Web サービスを作成

1. [Render](https://render.com) にログイン（GitHubアカウントで連携可能）
2. **Dashboard** → **New** → **Web Service**
3. 接続する **GitHubリポジトリ** を選択
4. 以下を設定：

| 項目 | 値 |
|------|-----|
| **Name** | 任意（例: todo-list） |
| **Region** | Singapore（日本に近い） |
| **Branch** | main |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |

---

## 3. 環境変数を設定

**Environment** セクションで以下を追加：

| Key | Value |
|-----|-------|
| `SPREADSHEET_ID` | スプレッドシートのID（URLの `/d/` と `/edit` の間） |
| `GOOGLE_CREDENTIALS_JSON` | `credentials.json` の**全文**をそのまま貼り付け |
| `SECRET_KEY` | ランダムな文字列（例: `openssl rand -hex 32` で生成） |
| `GOOGLE_CLIENT_ID` | （任意）Googleログイン用 OAuth クライアント ID |
| `GOOGLE_CLIENT_SECRET` | （任意）Googleログイン用 OAuth クライアント シークレット |

※ Googleログインの設定は `GOOGLE_OAUTH_SETUP.md` を参照

### GOOGLE_CREDENTIALS_JSON の取得方法

1. ローカルの `credentials.json` を開く
2. ファイルの内容を**すべて**コピー（`{` から `}` まで）
3. 改行やスペースを含めてそのまま貼り付け

```json
{"type":"service_account","project_id":"...", ...}
```

---

## 4. デプロイ

**Create Web Service** をクリックすると、自動でビルド・デプロイが開始されます。

完了後、`https://あなたのサービス名.onrender.com` でアクセスできます。

---

## 注意事項

- **無料プラン**: 15分間アクセスがないとスリープします。次回アクセス時に起動まで数十秒かかります。
- **ログ確認**: Render の **Logs** タブでエラーを確認できます。
- **再デプロイ**: GitHub にプッシュすると自動で再デプロイされます。
