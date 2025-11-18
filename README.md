# メールリスナー - OCRからKaipoke自動登録システム

## 概要

このプロジェクトは、メールに添付された画像からOCR（光学文字認識）を使用して構造化データを抽出し、自動的にKaipokeシステムに登録する自動化システムです。

### 主な機能

- 📧 **メール監視**: IMAP経由でメールボックスを監視し、画像添付ファイル付きのメールを自動検出
- 🔍 **OCR処理**: Google Cloud Vision APIまたはOpenAI Vision APIを使用して画像から日本語テキストを抽出
- 🤖 **AIデータ抽出**: OpenAI APIを使用して抽出されたテキストから構造化データ（名前、日付、時間、事業所名など）を自動抽出
- 🚀 **自動登録**: Playwrightを使用してKaipokeシステムに自動ログインし、抽出データを登録
- 🖥️ **GUI管理**: PyQt6ベースのユーザーインターフェースでサービスの開始・停止・ログ確認が可能

## システム構成

```
メール受信 → 画像抽出 → OCR処理 → AIデータ抽出 → Kaipoke自動登録
```

## 必要な環境

- Python 3.8以上
- Google Cloud Vision API または OpenAI API のアカウント
- Kaipokeシステムのアカウント
- IMAP対応のメールアカウント（Gmail推奨）

## インストール

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd emailListenner
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. Playwrightブラウザのインストール

```bash
playwright install chromium
```

### 4. 環境変数の設定

`.env.example`を参考に`.env`ファイルを作成し、以下の情報を設定してください：

```env
# Google Cloud Vision API認証情報
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# OpenAI API
OPENAI_API_KEY=sk-proj-your-openai-api-key-here

# Kaipoke認証情報
KAIPOKE_CORPORATE_CODE=your-corporate-code
KAIPOKE_USERNAME=your-username
KAIPOKE_PASSWORD=your-password

# メール認証情報
EMAIL_SERVER=imap.gmail.com
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

#### Google Cloud Vision APIの設定

1. Google Cloud Consoleでプロジェクトを作成
2. Cloud Vision APIを有効化
3. サービスアカウントを作成し、JSONキーをダウンロード
4. JSONキーの内容を`GOOGLE_SERVICE_ACCOUNT_JSON`環境変数に設定（1行のJSON文字列として）

#### Gmailアプリパスワードの取得

1. Googleアカウントのセキュリティ設定にアクセス
2. 2段階認証を有効化
3. アプリパスワードを生成
4. 生成されたパスワードを`EMAIL_PASSWORD`に設定

## 使用方法

### GUIアプリケーションの起動

```bash
python main.py
```

GUIが起動したら、以下の操作が可能です：

1. **サービス開始**: 「▶️ サービス開始」ボタンをクリックしてメール監視を開始
2. **ログ確認**: 画面下部のログパネルで処理状況を確認
3. **サービス停止**: 「⏹️ サービス停止」ボタンで監視を停止
4. **ログクリア**: 「🗑️ ログクリア」ボタンでログをクリア

### コマンドラインからの実行（開発用）

```bash
# メールリスナーのみ実行
python email_listener.py

# OCRテスト
python OCR.py
```

## 処理フロー

### 1. メール監視

- 30秒間隔でメールボックスをチェック
- 新しいメールを検出すると、画像添付ファイルを抽出

### 2. OCR処理

画像添付ファイルに対して以下の処理を実行：

- **Google Cloud Vision API**または**OpenAI Vision API**でテキスト抽出
- 抽出されたテキストから以下の情報をAIで構造化：
  - お名前（利用者名）
  - 実施日（サービス提供日）
  - 時間（開始・終了時間）
  - 事業所名
  - 障害者総合支援/身体（時間数）
  - 重度包括（時間数）
  - 重度訪問（時間数）
  - 家事（時間数）

### 3. Kaipoke自動登録

抽出されたデータをKaipokeシステムに自動登録：

1. Kaipokeにログイン
2. レシートページに遷移
3. 事業所別のAskページに遷移
4. 利用者別予実登録ページに遷移
5. サービス提供月を選択
6. 利用者を検索・選択
7. サービス登録ポップアップを開く
8. 以下の情報を入力：
   - 保険区分
   - サービス種類
   - サービス事業所
   - サービス区分
   - 開始・終了時間
   - 移動介護時間
   - 訪問先
   - 重複
   - 派遣人数
   - 予定・実績（実績を選択）
   - 提供日
9. 登録ボタンをクリック
10. エラーが発生した場合はモーダルを閉じて次のレコードを処理

### 4. 深夜サービス対応

終了時間が開始時間より早い場合（例：20:00～09:00）、自動的に2つのサービスに分割：

- 1件目: 当日の開始時間～24:00
- 2件目: 翌日の00:00～終了時間

## ファイル構成

```
emailListenner/
├── main.py                 # PyQt6 GUIアプリケーション
├── email_listener.py       # メール監視・処理ロジック
├── OCR.py                  # OCR処理・データ抽出
├── kaipoke.py              # Kaipoke自動登録スクレイパー
├── requirements.txt        # Python依存パッケージ
├── env.example            # 環境変数テンプレート
├── seen.json              # 処理済みメールID記録（自動生成）
├── images/                # テスト用画像ファイル
└── README.md              # このファイル
```

## 主要モジュール

### EmailListener (`email_listener.py`)

メールボックスの監視と画像添付ファイルの処理を担当：

- IMAP接続管理
- 新着メール検出
- 画像添付ファイル抽出
- OCR処理の呼び出し
- Kaipoke登録の呼び出し

### ImageTextExtractor (`OCR.py`)

画像からのテキスト抽出と構造化データ抽出を担当：

- Google Cloud Vision API / OpenAI Vision APIによるOCR
- OpenAI APIによる構造化データ抽出
- 日本語テキストの解析

### KaipokeScraper (`kaipoke.py`)

Kaipokeシステムへの自動登録を担当：

- Playwrightによるブラウザ自動化
- ログイン処理
- ページ遷移
- フォーム入力
- データ登録

## エラーハンドリング

### メール接続エラー

- 接続が切断された場合、自動的に再接続を試行
- 最大3回のリトライ

### OCR処理エラー

- 画像処理に失敗した場合、エラーログを出力して次の画像を処理
- 構造化データが抽出できない場合、警告を出力

### Kaipoke登録エラー

- バリデーションエラーが発生した場合、エラーメッセージを表示してモーダルを閉じる
- 登録に失敗した場合、エラーログを出力して次のレコードを処理

## トラブルシューティング

### メールサーバーに接続できない

- `.env`ファイルの`EMAIL_ADDRESS`と`EMAIL_PASSWORD`が正しく設定されているか確認
- Gmailを使用している場合、アプリパスワードが正しく設定されているか確認
- ファイアウォールやネットワーク設定を確認

### OCRが動作しない

- Google Cloud Vision APIの認証情報が正しく設定されているか確認
- OpenAI APIキーが正しく設定されているか確認
- APIの利用制限に達していないか確認

### Kaipokeにログインできない

- `.env`ファイルのKaipoke認証情報が正しく設定されているか確認
- ブラウザが正常に起動しているか確認（headlessモードを無効にして確認）

### データが正しく抽出されない

- 画像の品質を確認（解像度が低い、文字が不鮮明など）
- OCR処理のログを確認して、抽出されたテキストを確認
- 画像の形式が対応しているか確認（JPEG、PNG、GIF、BMP、TIFF、WebP）

## 注意事項

- このシステムは自動化ツールです。使用前にKaipokeの利用規約を確認してください
- 大量のメールを処理する場合、APIの利用制限に注意してください
- 本番環境で使用する前に、十分なテストを実施してください
- 認証情報は`.env`ファイルに保存し、Gitにコミットしないでください

## ライセンス

[ライセンス情報を記載]

## サポート

問題が発生した場合、以下の情報を含めて報告してください：

- エラーメッセージ
- ログファイルの内容
- 使用している環境（OS、Pythonバージョンなど）
- 再現手順

## 更新履歴

### v1.0
- 初回リリース
- メール監視機能
- OCR処理機能
- Kaipoke自動登録機能
- GUI管理画面

