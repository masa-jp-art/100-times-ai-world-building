# 100 TIMES AI WORLD BUILDING - Local Version

**完全ローカル実行版 v2.0 - Ollama + gpt-oss:20b**

このプロジェクトは、AIを活用した世界観構築ワークフローを完全にローカル環境で実行するバージョンです。

## 特徴

- ✅ **完全なプライバシー保護**: データが外部サーバーに送信されない
- ✅ **ゼロコスト運用**: API利用料金が発生しない
- ✅ **オフライン動作**: インターネット接続不要（初回モデルダウンロード後）
- ✅ **カスタマイズ性**: モデルパラメータの細かい調整が可能
- ✅ **チェックポイント機能**: 長時間実行でも中断・再開が可能

## システム要件

### 最小要件
- **OS**: Linux / macOS / Windows (WSL2推奨)
- **CPU**: 4コア以上
- **RAM**: 16GB以上
- **ストレージ**: 50GB以上の空き容量
- **Python**: 3.10以上

### 推奨要件
- **CPU**: 8コア以上
- **RAM**: 32GB以上
- **GPU**: NVIDIA RTX 3060 (12GB VRAM) 以上
- **ストレージ**: 100GB以上のSSD

## セットアップ

### 1. Ollamaのインストール

#### macOS / Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### Windows
PowerShellで実行:
```powershell
winget install Ollama.Ollama
```

### 2. Ollamaサーバーの起動

```bash
ollama serve
```

別のターミナルウィンドウで実行してください。サーバーはバックグラウンドで動作します。

### 3. gpt-oss:20bモデルのダウンロード

```bash
# フル精度版（推奨: 十分なVRAMがある場合）
ollama pull gpt-oss:20b

# または、4-bit量子化版（推奨: VRAMが限られている場合）
ollama pull gpt-oss:20b-q4
```

ダウンロードには数GBのデータ転送があるため、時間がかかる場合があります。

### 4. Python環境のセットアップ

```bash
# プロジェクトディレクトリに移動
cd 100-times-ai-world-building

# 仮想環境の作成（推奨）
python -m venv venv

# 仮想環境のアクティベート
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements-local.txt
```

### 5. Jupyter Notebookの起動

```bash
jupyter notebook
```

ブラウザが自動的に開き、Jupyter環境が表示されます。

### 6. ノートブックを開く

`local-v2.0.ipynb` を開いて、セルを順番に実行してください。

## 使い方

### 基本的な流れ

1. **ノートブックを開く**: `local-v2.0.ipynb`
2. **セルを順番に実行**: Cell 1から順に実行
3. **ユーザーコンテクストを入力**: Cell 3でコンテクストを編集
4. **Phase 1を実行**: 100倍拡張を実行（5〜25分）
5. **結果を確認**: 生成されたリストを確認
6. **完全パイプライン実行（オプション）**: Phase 2以降を実行（1.5〜8時間）

### ディレクトリ構成

```
100-times-ai-world-building/
├── local-v2.0.ipynb          # メインノートブック
├── README_LOCAL.md           # このファイル
├── DESIGN_SPEC_LOCAL.md      # 設計仕様書
├── requirements-local.txt    # Python依存関係
├── config/
│   ├── ollama_config.yaml   # Ollama設定
│   └── prompts/             # プロンプトテンプレート
├── src/
│   ├── ollama_client.py     # Ollama APIクライアント
│   ├── checkpoint_manager.py # チェックポイント管理
│   ├── utils.py             # ユーティリティ関数
│   └── pipeline.py          # パイプライン制御
├── output/                   # 生成結果（Gitで管理されない）
│   ├── intermediate/        # 中間データ
│   ├── checkpoints/         # チェックポイント
│   ├── novels/              # 生成された小説
│   └── references/          # 設定資料集
└── tests/                    # テストファイル
```

## 設定のカスタマイズ

### モデルの変更

`config/ollama_config.yaml`を編集:

```yaml
model:
  name: "gpt-oss:20b-q4"  # 軽量版に変更
```

### 生成パラメータの調整

```yaml
phases:
  phase5_novel:
    temperature: 1.2  # より創造的な出力（デフォルト: 1.0）
    num_predict: 8192  # より長い出力（デフォルト: 4096）
```

## トラブルシューティング

### Ollamaサーバーに接続できない

**エラー**: `Connection refused`

**解決策**:
```bash
# サーバーを起動
ollama serve

# または、バックグラウンドで起動
nohup ollama serve &
```

### メモリ不足エラー

**エラー**: `CUDA out of memory` または システムフリーズ

**解決策**:
1. 量子化モデルに切り替え:
```bash
ollama pull gpt-oss:20b-q4
```

2. `config/ollama_config.yaml`を編集:
```yaml
model:
  name: "gpt-oss:20b-q4"

performance:
  max_parallel_requests: 1  # 並列実行を無効化
```

### JSON出力が不正

**エラー**: `JSONDecodeError`

**解決策**:
- 自動的にリトライされます（最大3回）
- それでも失敗する場合は、temperatureを下げてください:

```yaml
phases:
  phase1_expansion:
    temperature: 0.5  # より決定論的な出力
```

### 実行が遅い

**対策**:
1. GPUを使用していることを確認:
```bash
ollama list  # モデル情報を表示
```

2. 並列処理を有効化:
```yaml
performance:
  max_parallel_requests: 3  # 複数リクエストを並列実行
```

3. より軽量なモデルを使用:
```bash
ollama pull mistral:latest  # 代替モデル
```

## パフォーマンス目安

### GPU環境（RTX 3090）
- Phase 1（100倍拡張）: 5〜10分
- Phase 2〜6（完全実行）: 1.5〜3時間

### CPU環境
- Phase 1（100倍拡張）: 15〜25分
- Phase 2〜6（完全実行）: 4〜8時間

## 高度な使い方

### コマンドラインからの実行

```python
# Python スクリプトとして実行
from src import Pipeline

pipeline = Pipeline()
pipeline.check_prerequisites()

user_context = """
context:
  theme: "未来都市"
"""

results = pipeline.run_full_pipeline(user_context)
```

### チェックポイントからの再開

```python
# チェックポイントのリスト表示
pipeline.checkpoint_manager.list_checkpoints()

# 特定のフェーズから再開
pipeline.resume_from_checkpoint("phase1_expansion")
```

### カスタムプロンプトの使用

`config/prompts/`ディレクトリに新しいYAMLファイルを追加:

```yaml
# config/prompts/custom.yaml
my_custom_prompt:
  system: "カスタムシステムプロンプト"
  user: "カスタムユーザープロンプト: {variable}"
```

## テスト

```bash
# すべてのテストを実行
pytest tests/ -v

# カバレッジレポート付き
pytest tests/ --cov=src --cov-report=html
```

## よくある質問（FAQ）

### Q1: v1.2（クラウド版）との違いは？

**A**: 主な違いは以下の通りです:
- API: OpenAI/Claude → Ollama
- コスト: 従量課金 → ゼロ
- プライバシー: データ外部送信あり → 完全ローカル
- 品質: GPT-4/Claude水準 → gpt-oss:20b水準（やや劣る）
- 実行時間: ネットワーク遅延あり → ローカル計算負荷

### Q2: 生成品質を向上させるには？

**A**: 以下の方法を試してください:
1. フル精度モデル（gpt-oss:20b）を使用
2. temperatureを調整（創造性 vs 一貫性）
3. プロンプトを詳細化
4. より高性能なハードウェアを使用

### Q3: 他のモデルを使用できますか？

**A**: はい。Ollamaがサポートする任意のモデルを使用できます:
```yaml
model:
  name: "llama3:70b"  # または他のモデル
```

利用可能なモデル一覧:
```bash
ollama list
```

### Q4: 商用利用は可能ですか？

**A**: gpt-ossモデルのライセンスに従ってください。詳細はOllamaの公式ドキュメントを参照してください。

## 貢献

バグ報告や機能リクエストは、GitHubのIssuesで受け付けています。

## ライセンス

このプロジェクトの使用条件については、書籍「100 TIMES AI WORLD BUILDING」をご参照ください。

## サポート

- [GitHub Issues](https://github.com/masa-jp-art/100-times-ai-world-building/issues)
- [設計仕様書](DESIGN_SPEC_LOCAL.md)
- [note記事](https://note.com/msfmnkns/n/n26ddda02e0d2)

## 更新履歴

### v2.0-local (2026-02-14)
- 初回リリース
- Ollama + gpt-oss:20b対応
- 完全ローカル実行環境の構築
- チェックポイント機能の追加
- .gitignore設定による開発履歴の保護

---

**Author**: masa-jp-art
**Version**: v2.0-local
**Last Updated**: 2026-02-14
