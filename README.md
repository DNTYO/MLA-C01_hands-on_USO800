# MLA-C01 ハンズオン環境 CDK

このCDKプロジェクトは、AWS Machine Learning Specialty (MLA-C01) 認定試験のハンズオン学習環境を構築します。知らんけど。

## 構築されるリソース

### データ取得・保存層
- **S3 Buckets**: Raw Data, Processed Data, Model Artifacts
- **DynamoDB**: 推論結果キャッシュ用テーブル
- **RDS Aurora**: 構造化データ用MySQL クラスター

### 機械学習開発層
- **SageMaker Domain**: Studio環境
- **SageMaker User Profile**: 開発用ユーザー

### データ処理層
- **AWS Glue Database**: データカタログ
- **Lambda Function**: 軽量データ処理
- **API Gateway**: Lambda用REST API

### ネットワーク
- **VPC**: セキュアなネットワーク環境

## デプロイ手順

1. 依存関係のインストール:
```bash
pip install -r requirements.txt
```

2. CDK Bootstrap (初回のみ):
```bash
cdk bootstrap
```

3. デプロイ:
```bash
cdk deploy
```

## 削除

```bash
cdk destroy
```

## 注意事項

- RDS Auroraクラスターは最小構成（t3.small）で作成されます
- 全リソースは`RemovalPolicy.DESTROY`が設定されており、スタック削除時に完全に削除されます
- S3バケット名にはアカウントIDとリージョンが含まれ、グローバルで一意になります
