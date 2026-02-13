# Next Steps - 100 TIMES AI WORLD BUILDING Local Version

**プロジェクト完成！次のステップガイド**

---

## 🎉 完成状態

すべてのフェーズ（Phase 0〜6）の実装が完了しました！

- ✅ コアモジュール実装完了
- ✅ プロンプトテンプレート完成
- ✅ 設定ファイル完備
- ✅ テストコード作成済み
- ✅ ドキュメント完備
- ✅ .gitignore設定済み（開発履歴保護）

---

## 🚀 すぐに始める

### ステップ1: セットアップ確認

```bash
python setup_check.py
```

すべて✓になるまで問題を解決してください。

### ステップ2: Phase 1を試す（5〜25分）

```bash
# コマンドラインから
python example_run.py
# → 選択肢1を選択

# または、Jupyter Notebookで
jupyter notebook
# → local-v2.0.ipynb を開いて Cell 1-6を実行
```

### ステップ3: 結果を確認

```bash
# 生成されたファイルを確認
ls output/intermediate/

# YAMLファイルの内容を確認
cat output/intermediate/01_desire_list.yaml | head -20
```

---

## 📊 完全パイプライン実行（1.5〜8時間）

### オプション1: コマンドラインから

```bash
python example_run.py
# → 選択肢2を選択
```

### オプション2: Jupyter Notebookで

```python
# Cell 7のコメントアウトを解除
all_results = pipeline.run_full_pipeline(user_context)
```

### 実行中の監視

```bash
# ログをリアルタイムで表示
tail -f logs/local_v2.log

# 進捗を確認
ls -lh output/intermediate/
ls -lh output/novels/
ls -lh output/references/
```

---

## 🛠️ カスタマイズ

### モデルの変更

`config/ollama_config.yaml` を編集:

```yaml
model:
  name: "gpt-oss:20b-q4"  # より軽量なモデル
  # または
  name: "llama3:70b"      # 代替モデル
```

### 生成パラメータの調整

```yaml
phases:
  phase5_novel:
    temperature: 1.2      # より創造的（デフォルト: 1.0）
    num_predict: 8192     # より長い出力（デフォルト: 4096）
```

### プロンプトのカスタマイズ

`config/prompts/*.yaml` のプロンプトを編集してください。

---

## 🔧 トラブルシューティング

### Ollamaサーバーが起動しない

```bash
# 手動起動
ollama serve

# または、バックグラウンドで
nohup ollama serve > ollama.log 2>&1 &
```

### メモリ不足

```bash
# より軽量なモデルをダウンロード
ollama pull gpt-oss:20b-q4

# 設定を変更
# config/ollama_config.yaml:
performance:
  max_parallel_requests: 1
```

### JSON出力エラー

temperatureを下げてみてください:

```yaml
phases:
  phase1_expansion:
    temperature: 0.5
```

---

## 📚 学習リソース

### ドキュメントを読む

1. **README_LOCAL.md** - ユーザーガイド
2. **DESIGN_SPEC_LOCAL.md** - 技術仕様書
3. **IMPLEMENTATION_STATUS.md** - 実装状況

### コードを読む

1. **src/pipeline.py** - メインロジック
2. **src/ollama_client.py** - API通信
3. **config/prompts/** - プロンプト設計

---

## 🧪 テストの実行

```bash
# 全テストを実行
pytest tests/ -v

# カバレッジレポート付き
pytest tests/ --cov=src --cov-report=html

# カバレッジレポートを開く
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## 📦 バージョン管理

### 初回コミット

```bash
# 現在の状態を確認
git status

# 開発履歴は自動的に除外されます（.gitignore設定済み）
# 以下はGitで管理されません:
# - output/
# - checkpoints/
# - logs/
# - user_context*.yaml

# コミット
git add .
git commit -m "feat: Add local version v2.0 with Ollama + gpt-oss:20b

- Implement Phase 0-6 complete pipeline
- Add checkpoint management
- Add comprehensive prompts
- Configure .gitignore for development artifacts
"
```

### ブランチ戦略（推奨）

```bash
# メインブランチは安定版
git checkout main

# 実験用ブランチ
git checkout -b experiment/faster-prompts

# 機能追加用ブランチ
git checkout -b feature/web-ui
```

---

## 🌟 次の改善案

### 優先度高

1. **Phase 1の結果を確認して品質評価**
   - 願望・能力・役割リストの多様性
   - プロンプトの調整が必要か判断

2. **完全パイプラインを1回実行**
   - 全体の動作確認
   - 生成品質の評価
   - ボトルネックの特定

3. **プロンプトの改善**
   - 出力品質に基づいて調整
   - より具体的な指示を追加
   - 例示の追加

### 優先度中

4. **並列処理の最適化**
   - 独立したAPI呼び出しの並列化
   - メモリ使用量の監視

5. **エラーハンドリングの強化**
   - より詳細なエラーメッセージ
   - 自動リトライの改善

6. **進捗表示の改善**
   - リアルタイム進捗バー
   - 推定残り時間の表示

### 優先度低

7. **Web UI開発**
   - Streamlit/Gradioインターフェース
   - リアルタイムモニタリング

8. **API化**
   - FastAPIによるRESTful API
   - 外部からの利用

9. **マルチモーダル対応**
   - 画像入力の復活
   - 視覚対応モデルの統合

---

## 💡 使い方のヒント

### 短時間でテスト

```python
# Phase 1のみ実行（5-25分）
python example_run.py
# → 選択肢1

# 結果を確認して、続行するか判断
```

### チェックポイントを活用

```python
# Phase 1まで実行して保存
results = pipeline.run_phase1_expansion(user_context)

# 後で続きから再開
pipeline.resume_from_checkpoint("phase1_expansion")
```

### カスタムコンテクストの使用

```python
# あなた独自のストーリーコンテクスト
custom_context = """
context:
  theme: "あなたのテーマ"
  mood: "あなたの雰囲気"
  setting: "あなたの設定"
"""

results = pipeline.run_phase1_expansion(custom_context)
```

---

## 📞 サポート

### 問題が発生した場合

1. **setup_check.pyを実行**
   ```bash
   python setup_check.py
   ```

2. **ログを確認**
   ```bash
   tail -100 logs/local_v2.log
   ```

3. **GitHub Issuesで報告**
   - エラーメッセージ
   - 実行環境（OS, RAM, GPU等）
   - 再現手順

---

## 🎯 ゴール達成までのロードマップ

### Week 1: セットアップと検証
- [x] 環境構築
- [ ] Phase 1の動作確認
- [ ] 出力品質の評価

### Week 2: 最適化
- [ ] プロンプトの改善
- [ ] パフォーマンスチューニング
- [ ] エラーハンドリング強化

### Week 3: 完全実行
- [ ] 完全パイプラインの実行
- [ ] 生成された小説の確認
- [ ] 設定資料集の確認

### Week 4: 公開準備
- [ ] ドキュメントの最終確認
- [ ] サンプル出力の準備
- [ ] コミュニティへの共有

---

## ✅ 今すぐできること

1. **Phase 1を実行**
   ```bash
   python example_run.py
   ```

2. **生成結果を確認**
   ```bash
   cat output/intermediate/01_desire_list.yaml | head -30
   ```

3. **プロンプトを調整**
   - `config/prompts/expansion.yaml` を編集
   - 再実行して品質を比較

4. **フィードバックを記録**
   - 気づいたことをメモ
   - 改善点をIssueに登録

---

## 🌈 楽しんでください！

あなたの創造力 × AIのパワー = 無限の物語世界

Let's build amazing worlds together! 🚀

---

**Happy World Building!**
**Author**: masa-jp-art
**Date**: 2026-02-14
