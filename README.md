# agent-study

## セットアップ

仮想環境を作成：

```bash
python -m venv .venv
```

仮想環境を有効化：

```bash
.venv\Scripts\activate
```

依存関係をインストール：

```bash
pip install -r requirements-dev.txt
```

npm 依存関係をインストール（serverless フレームワーク用）：

```bash
npm install
```

AWS プロファイルを設定：

```bash
aws configure --profile pk
```

.env ファイルを設定：

```bash
cp .env.example .env
```

※ .env ファイルを自分の値で編集してください

## ローカルでテスト

```bash
npx sls invoke local -f chat -d '{"body": "{\"message\": \"お元気ですか？\"}"}'
```

## デプロイ

```bash
npx sls deploy --verbose --aws-profile pk
```

## デプロイ済みをテスト

```bash
curl -X POST <URL> -H "Content-Type: application/json" -d '{"message": "お元気ですか？"}'
```

※ <URL> はデプロイした際に表示される URL です。

## requirements を更新

requirements-base.txt を更新したら、以下のコマンドで requirements.txt を更新してください。

```bash
docker run --rm -v "$(pwd)":/app -w /app public.ecr.aws/sam/build-python3.12:latest-x86_64 /bin/sh -c "python3.12 -m pip install -r requirements-base.txt && python3.12 -m pip freeze > requirements.txt"
```
