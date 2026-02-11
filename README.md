# 100 TIMES AI WORLD BUILDING

このプロジェクトは、拙著「100 TIMES AI WORLD BUILDING」で紹介したAIを活用した世界観構築ワークフローを実際に体験できるJupyter Notebookです。

## 概要

AIを使って、ユーザーの持つコンテクストから物語世界を拡張し、重厚な小説と詳細な設定資料集を生成するワークフローを提供します。

## 主な機能

### 1. ユーザーコンテクストの抽出
- ランダムな質問を通じてユーザーの持つコンテクストを明らかにします
- ChatGPTが質問を投げかけ、回答を解釈してコンテクストをまとめます
- 画像からもコンテクストを抽出可能です

### 2. コンテクストの拡張
- ユーザーコンテクストを抽象的に解釈し、拡張します
- **100個の願望（desire）リスト**：物語の登場人物が秘めている願望
- **100個の能力（ability）リスト**：登場人物が持つ特別な能力または得意分野

### 3. 物語と設定資料集の生成
- 拡張されたコンテクストから重厚長大な長編小説を生成
- 複数章に渡る物語構造
- 詳細な設定資料集の作成

## 使用しているAI

- **OpenAI API**（GPT-4など）
- **Anthropic Claude API**

## セットアップ

### 1. 必要なライブラリのインストール

```python
pip install openai
pip install anthropic
```

### 2. APIキーの設定

```python
# OpenAI API キーの設定
OPENAI_API_KEY = "your-openai-api-key"

# Anthropic APIキーの設定
anthropic = anthropic.Anthropic(api_key="your-anthropic-api-key")
```

### 3. Google Colabでの使用

1. ファイル > ドライブにコピーを保存
2. ご自身のGoogle Driveにコピーを保存
3. APIキーを設定して実行

## 使い方

### Step 1: ユーザーコンテクストの設定

専用のChatGPTを使用してコンテクストを抽出します：
https://chatgpt.com/g/g-68280b3861008191b250b17b7fe76d88

抽出したコンテクストを変数に代入：

```python
user_context = """
# ここに抽出したコンテクストを入力
"""
```

### Step 2: コンテクストの拡張

- 100個の願望リストを生成
- 100個の能力リストを生成

### Step 3: 物語の生成

拡張されたコンテクストを基に、章ごとに重厚な小説を生成します。

## プロジェクト構成

```
.
├── 20250601-100-TIMES-AI-WORLD-BUILDING-v1_2.ipynb  # メインノートブック
└── README.md                                          # このファイル
```

## 特徴

- **100倍の拡張**：ユーザーの持つコンテクストを100個の要素に拡張
- **多層的な世界構築**：願望、能力、プロットなど多角的に世界を構築
- **重厚な物語生成**：最大トークン数を活用した長編小説の生成
- **詳細な設定資料**：物語を支える詳細な世界設定の自動生成

## 参考リンク

- [100 TIMES AI WORLD BUILDING - note版]([https://note.com/msfmnkns/n/n26ddda02e0d2])

## 必要要件

- Python 3.x
- OpenAI API キー
- Anthropic API キー
- Google Colab（推奨）またはJupyter環境

## ライセンス

このプロジェクトの使用条件については、書籍「100 TIMES AI WORLD BUILDING」をご参照ください。

## 注意事項

- APIの使用には料金が発生する場合があります
- 生成される小説の長さによっては、相応のAPIコストがかかります
- APIキーは絶対に公開しないでください

## サポート

質問や問題がある場合は、書籍のサポートページまたはnoteをご確認ください。

---

**Author**: masa-jp-art  
**Version**: v1.2  
**Last Updated**: 2025-06-01
