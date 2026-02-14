# 100 TIMES AI WORLD BUILDING — ローカルバージョン設計仕様書

**バージョン**: v2.0-local
**作成日**: 2026-02-13
**著者**: masa-jp-art
**文書ステータス**: 初版ドラフト
**対応Issue**: [#2 ローカルバージョンを作成したい](https://github.com/masa-jp-art/100-times-ai-world-building/issues/2)

---

## 目次

1. [概要と動機](#1-概要と動機)
2. [要件定義](#2-要件定義)
3. [システムアーキテクチャ](#3-システムアーキテクチャ)
4. [モデル置換設計](#4-モデル置換設計)
5. [ローカルファイルストレージ設計](#5-ローカルファイルストレージ設計)
6. [推論エフォート設定機能](#6-推論エフォート設定機能)
7. [設定管理](#7-設定管理)
8. [パイプライン改修](#8-パイプライン改修)
9. [エラーハンドリングとリカバリ](#9-エラーハンドリングとリカバリ)
10. [制作ログ機能](#10-制作ログ機能)
11. [移行ガイド](#11-移行ガイド)
12. [制約事項と前提条件](#12-制約事項と前提条件)
13. [将来の拡張性](#13-将来の拡張性)

---

## 1. 概要と動機

### 1.1 背景

現行のv1.2はGoogle Colab上で動作し、OpenAI API（o4-mini）とAnthropic API（Claude 3.7 Sonnet）に依存している。これにより以下の課題が存在する：

- **コスト**: 1回の完全実行で74回のAPI呼び出しが発生し、数千〜数万円のAPI利用料が発生する
- **外部依存**: インターネット接続とAPI提供者の可用性に依存
- **データ主権**: 生成データが外部APIサーバーを経由するため、プライバシー上の懸念がある
- **永続性の欠如**: ノートブックのカーネル状態に依存し、中間データの保存機能がない
- **柔軟性の不足**: モデルやパラメータの切り替えが容易でない

### 1.2 本バージョンの目的

ローカルバージョンでは、以下の3つの要件を実現する：

1. **推論モデルのローカル化**: `gpt-oss:20b` への置換によりオフライン実行を可能にする
2. **ローカルファイルストレージ**: プロジェクト単位のフォルダ管理と制作過程を記録するログ機能
3. **柔軟なエフォート設定**: タスクの性質に応じた推論エフォートレベルの最適化

---

## 2. 要件定義

### 2.1 機能要件

| ID | 要件 | 優先度 |
|----|------|--------|
| FR-01 | 推論部分を gpt-oss:20b に置換する | 必須 |
| FR-02 | すべての中間データ・最終出力をローカルファイルに自動保存する | 必須 |
| FR-03 | プロジェクト単位でフォルダを分離し、成果物を整理する | 必須 |
| FR-04 | 制作過程を記録する制作ログを自動生成する | 必須 |
| FR-05 | タスクごとに推論エフォートレベルを設定可能にする | 必須 |
| FR-06 | 既存のv1.2パイプライン（6フェーズ構成）の機能を維持する | 必須 |
| FR-07 | インターネット接続なしで完全実行可能にする | 推奨 |
| FR-08 | 中断した処理をチェックポイントから再開可能にする | 推奨 |

### 2.2 非機能要件

| ID | 要件 | 目標値 |
|----|------|--------|
| NFR-01 | ローカル推論の応答時間 | 1リクエストあたり5分以内（VRAM依存） |
| NFR-02 | ディスク使用量 | モデル本体を除き、1プロジェクトあたり100MB以下 |
| NFR-03 | メモリ使用量 | モデルロード後のパイプライン実行で追加8GB以下 |
| NFR-04 | Python互換性 | Python 3.10以上 |

---

## 3. システムアーキテクチャ

### 3.1 全体構成

```
┌─────────────────────────────────────────────────────────────┐
│                    ローカル実行環境                            │
│               Jupyter Notebook / Python スクリプト             │
│                                                              │
│  ┌──────────┐    ┌───────────────────────────────────────┐   │
│  │ ユーザー   │───▶│         メインパイプライン               │   │
│  │ 入力      │    │  (local_worldbuilding.py)              │   │
│  └──────────┘    └──────┬──────────────┬─────────────────┘   │
│                          │              │                     │
│           ┌──────────────▼──┐    ┌──────▼──────────────┐     │
│           │  ローカル推論    │    │  ファイルストレージ    │     │
│           │  エンジン        │    │  マネージャー         │     │
│           │                 │    │                      │     │
│           │  gpt-oss:20b   │    │  ・プロジェクト管理   │     │
│           │                 │    │  ・中間データ保存     │     │
│           │  ・構造化データ  │    │  ・制作ログ記録       │     │
│           │  ・長文生成      │    │  ・チェックポイント   │     │
│           │  ・キーワード    │    │                      │     │
│           │    抽出          │    │                      │     │
│           └────────────────┘    └──────────────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                   設定管理                              │    │
│  │   config.yaml                                         │    │
│  │   ・モデル設定                                          │    │
│  │   ・エフォートレベル設定                                 │    │
│  │   ・出力パス設定                                        │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 コンポーネント構成

```
100-times-ai-world-building/
├── local_worldbuilding.py          # メインエントリーポイント
├── config.yaml                     # プロジェクト設定ファイル
├── src/
│   ├── __init__.py
│   ├── inference.py                # 推論エンジン（gpt-oss:20b対応）
│   ├── pipeline.py                 # パイプライン制御（6フェーズ）
│   ├── storage.py                  # ファイルストレージマネージャー
│   ├── production_log.py           # 制作ログ管理
│   ├── effort_config.py            # エフォートレベル設定
│   ├── checkpoint.py               # チェックポイント管理
│   └── utils.py                    # ユーティリティ関数
├── projects/                       # プロジェクト保存ディレクトリ
│   └── {project_name}/            # 個別プロジェクト
│       ├── config.yaml            # プロジェクト固有設定
│       ├── user_context.yaml      # ユーザーコンテクスト
│       ├── intermediate/          # 中間データ
│       ├── output/                # 最終出力
│       ├── checkpoint/            # チェックポイント
│       └── production_log.md      # 制作ログ
├── 20250601-100-TIMES-AI-WORLD-BUILDING-v1.2.ipynb  # 既存ノートブック（参照用）
├── DESIGN_SPEC.md                  # 既存設計仕様書
├── LOCAL_VERSION_DESIGN_SPEC.md    # 本文書
└── README.md
```

---

## 4. モデル置換設計

### 4.1 置換方針

現行システムでは2つのモデルを使い分けているが、ローカルバージョンでは `gpt-oss:20b` に統一する。

| 現行 | ローカルバージョン | 用途 |
|------|-------------------|------|
| OpenAI o4-mini | gpt-oss:20b | 構造化データ生成（JSON/YAML） |
| Anthropic Claude 3.7 Sonnet | gpt-oss:20b | 長文小説生成・設定資料集生成 |

### 4.2 推論エンジンインターフェース

モデルの差し替えを容易にするため、推論部分を抽象化したインターフェースを設ける。

```python
# src/inference.py

from dataclasses import dataclass
from typing import Optional
from enum import Enum

class OutputFormat(Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    TEXT = "text"

class EffortLevel(Enum):
    LOW = "low"          # 高速・低品質（リスト生成、キーワード抽出等）
    MEDIUM = "medium"    # バランス（世界設定生成、プロット等）
    HIGH = "high"        # 高品質・低速（小説本文、設定資料集等）

@dataclass
class InferenceConfig:
    model_name: str = "gpt-oss:20b"
    effort_level: EffortLevel = EffortLevel.MEDIUM
    max_tokens: int = 4096
    temperature: float = 0.7
    output_format: OutputFormat = OutputFormat.TEXT
    system_prompt: str = ""

class InferenceEngine:
    """ローカル推論エンジンの抽象インターフェース"""

    def __init__(self, model_path: str, device: str = "auto"):
        """
        Args:
            model_path: gpt-oss:20b のモデルパスまたはモデル名
            device: 推論デバイス ("auto", "cuda", "cpu")
        """
        ...

    def generate(self, prompt: str, config: InferenceConfig) -> str:
        """推論を実行し結果を返す"""
        ...

    def generate_json(self, prompt: str, config: InferenceConfig) -> str:
        """JSON形式の応答を生成し、YAML文字列に変換して返す"""
        ...

    def generate_markdown(self, prompt: str, config: InferenceConfig) -> str:
        """Markdown形式の応答を生成して返す"""
        ...
```

### 4.3 gpt-oss:20b 対応の詳細

#### 4.3.1 モデルロード

```python
# gpt-oss:20b のロード方式（想定）
# OpenAI互換APIサーバー経由、またはローカル推論ライブラリ経由

# 方式A: OpenAI互換ローカルサーバー経由（推奨）
#   - vLLM, llama.cpp, Ollama等でサーバーを起動
#   - OpenAI互換エンドポイントに接続
#   - 既存のプロンプト構造をほぼそのまま利用可能

# 方式B: 直接ロード
#   - transformers / llama-cpp-python 等でモデルを直接ロード
#   - メモリ管理が必要だが、レイテンシは低い
```

#### 4.3.2 OpenAI互換サーバー方式（方式A・推奨）

既存のプロンプト構造を最大限に活用するため、OpenAI互換のローカルサーバーを推奨する。

```python
class LocalOpenAICompatEngine(InferenceEngine):
    """OpenAI互換ローカルサーバーを使用する推論エンジン"""

    def __init__(self, base_url: str = "http://localhost:8080/v1", model_name: str = "gpt-oss:20b"):
        from openai import OpenAI
        self.client = OpenAI(base_url=base_url, api_key="not-needed")
        self.model_name = model_name

    def generate(self, prompt: str, config: InferenceConfig) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )
        return response.choices[0].message.content

    def generate_json(self, prompt: str, config: InferenceConfig) -> str:
        config.system_prompt = "常に日本語で応答します。常にjson形式で応答します。"
        raw = self.generate(prompt, config)
        # JSON → YAML 変換
        data = json.loads(raw)
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)
```

### 4.4 既存関数との対応関係

| 現行関数 | 置換後の呼び出し | エフォートレベル |
|----------|-----------------|-----------------|
| `o4(prompt)` | `engine.generate_json(prompt, config)` | タスク依存（後述） |
| `o4md(prompt)` | `engine.generate_markdown(prompt, config)` | タスク依存 |
| `claude(prompt)` | `engine.generate(prompt, config)` | HIGH |

---

## 5. ローカルファイルストレージ設計

### 5.1 プロジェクト構造

各実行はプロジェクトとして独立したフォルダに保存される。

```
projects/
└── {project_name}_{timestamp}/
    ├── config.yaml                    # このプロジェクトの設定スナップショット
    ├── user_context.yaml              # 入力コンテクスト
    │
    ├── intermediate/                  # 中間データ（フェーズ別）
    │   ├── phase1_expansion/
    │   │   ├── desire_list.yaml
    │   │   ├── ability_list.yaml
    │   │   ├── role_list.yaml
    │   │   ├── plottype_list.yaml
    │   │   └── plottype.yaml
    │   │
    │   ├── phase2_characters/
    │   │   └── characters_list.yaml
    │   │
    │   ├── phase3_worldbuilding/
    │   │   ├── events.yaml
    │   │   ├── observation.yaml
    │   │   ├── interpretation.yaml
    │   │   ├── media.yaml
    │   │   ├── important_past_events.yaml
    │   │   ├── social_structure.yaml
    │   │   ├── living_environment.yaml
    │   │   ├── social_groups.yaml
    │   │   ├── people_list.yaml
    │   │   └── future_scenarios.yaml
    │   │
    │   └── phase4_plot/
    │       ├── plot.yaml
    │       ├── plot_01.yaml ～ plot_10.yaml
    │       ├── plot_keywords_01.yaml ～ plot_keywords_10.yaml
    │       └── plot_reference_01.yaml ～ plot_reference_10.yaml
    │
    ├── output/                        # 最終出力
    │   ├── novel/
    │   │   ├── chapter_01.md ～ chapter_10.md
    │   │   └── novel_complete.md      # 全章結合版
    │   │
    │   └── reference/
    │       ├── reference_characters_list.md
    │       ├── reference_plot.md
    │       ├── reference_user_context.md
    │       ├── reference_events.md
    │       ├── reference_observation.md
    │       ├── reference_interpretation.md
    │       ├── reference_media.md
    │       ├── reference_important_past_events.md
    │       ├── reference_social_structure.md
    │       ├── reference_living_environment.md
    │       ├── reference_social_groups.md
    │       ├── reference_people_list.md
    │       ├── reference_future_scenarios.md
    │       ├── reference_desire_list.md
    │       ├── reference_ability_list.md
    │       ├── reference_role_list.md
    │       └── reference_plottype_list.md
    │
    ├── checkpoint/                    # チェックポイント
    │   └── state_{phase}_{step}.json  # 復元用状態データ
    │
    └── production_log.md              # 制作ログ
```

### 5.2 ストレージマネージャー

```python
# src/storage.py

class StorageManager:
    """プロジェクトのファイル保存を管理するクラス"""

    def __init__(self, project_name: str, base_dir: str = "./projects"):
        """
        Args:
            project_name: プロジェクト名
            base_dir: プロジェクト保存ベースディレクトリ
        """
        ...

    def create_project(self) -> str:
        """プロジェクトフォルダ構造を初期化し、パスを返す"""
        ...

    def save_intermediate(self, phase: str, name: str, data: str, fmt: str = "yaml") -> str:
        """中間データを保存する

        Args:
            phase: フェーズ名 ("phase1_expansion", "phase2_characters", etc.)
            name: データ名 ("desire_list", "events", etc.)
            data: 保存するデータ文字列
            fmt: ファイル形式 ("yaml", "json", "md")
        Returns:
            保存先のファイルパス
        """
        ...

    def save_output(self, category: str, name: str, data: str) -> str:
        """最終出力を保存する

        Args:
            category: カテゴリ ("novel", "reference")
            name: ファイル名
            data: 保存するデータ文字列
        Returns:
            保存先のファイルパス
        """
        ...

    def load_intermediate(self, phase: str, name: str) -> Optional[str]:
        """保存済みの中間データを読み込む（チェックポイント復元用）"""
        ...

    def save_checkpoint(self, phase: str, step: str, state: dict) -> str:
        """チェックポイントを保存する"""
        ...

    def load_latest_checkpoint(self) -> Optional[dict]:
        """最新のチェックポイントを読み込む"""
        ...

    def combine_novel_chapters(self) -> str:
        """全章を結合した完全版小説ファイルを生成する"""
        ...
```

### 5.3 自動保存のタイミング

各API呼び出し（ローカル推論）の完了直後に、結果を自動的にファイルに保存する。

```
推論実行 → 結果取得 → ファイル保存 → 制作ログ追記 → チェックポイント更新
```

---

## 6. 推論エフォート設定機能

### 6.1 エフォートレベルの定義

タスクの性質に応じて、推論のリソース配分を3段階で制御する。

| レベル | 名称 | 用途 | max_tokens | temperature | 推論時間目安 |
|--------|------|------|------------|-------------|-------------|
| LOW | 高速モード | リスト生成、キーワード抽出、データ分割 | 2048 | 0.3 | 〜30秒 |
| MEDIUM | バランスモード | 世界設定生成、キャラクター生成、プロット | 4096 | 0.7 | 〜2分 |
| HIGH | 高品質モード | 小説本文執筆、設定資料集作成 | 8192 | 1.0 | 〜5分 |

### 6.2 タスク別デフォルトエフォート設定

```yaml
# config.yaml の effort_settings セクション

effort_settings:
  # Phase 1: 100倍拡張
  desire_list: medium
  ability_list: medium
  role_list: medium
  plottype_list: low
  plottype: low

  # Phase 2: キャラクター生成
  characters_list: medium

  # Phase 3: 世界構築
  events: medium
  observation: medium
  interpretation: medium
  media: medium
  important_past_events: medium
  social_structure: high
  living_environment: high
  social_groups: medium
  people_list: high
  future_scenarios: medium

  # Phase 4: プロット生成
  plot: high
  plot_split: low          # plot_1 ～ plot_10（分割処理）
  plot_keywords: low       # キーワード抽出
  plot_reference: low      # 参考資料検索

  # Phase 5: 小説生成
  story: high              # story_1 ～ story_10

  # Phase 6: 設定資料集生成
  reference: high          # reference_* 全17種
```

### 6.3 エフォート設定の仕組み

```python
# src/effort_config.py

class EffortConfig:
    """タスクごとのエフォートレベルを管理する"""

    # エフォートレベルから推論パラメータへのマッピング
    EFFORT_PARAMS = {
        EffortLevel.LOW: {
            "max_tokens": 2048,
            "temperature": 0.3,
        },
        EffortLevel.MEDIUM: {
            "max_tokens": 4096,
            "temperature": 0.7,
        },
        EffortLevel.HIGH: {
            "max_tokens": 8192,
            "temperature": 1.0,
        },
    }

    def __init__(self, config_path: str = "config.yaml"):
        """設定ファイルからエフォートレベルを読み込む"""
        ...

    def get_config(self, task_name: str) -> InferenceConfig:
        """タスク名に対応する推論設定を返す"""
        ...

    def override(self, task_name: str, level: EffortLevel):
        """特定タスクのエフォートレベルを実行時に上書きする"""
        ...
```

### 6.4 ユーザーによるカスタマイズ

ユーザーは以下の方法でエフォートレベルをカスタマイズできる：

1. **config.yaml の編集**: 実行前にデフォルト値を変更
2. **実行時引数**: コマンドラインやノートブックから特定タスクのレベルを上書き
3. **一括設定**: `--effort-all high` のように全タスクのレベルを一括変更

```bash
# 例: 全体をhighで実行（最高品質）
python local_worldbuilding.py --project "my_story" --effort-all high

# 例: 小説部分のみhigh、その他はlowで高速実行
python local_worldbuilding.py --project "my_story" --effort-default low --effort story=high
```

---

## 7. 設定管理

### 7.1 グローバル設定ファイル

```yaml
# config.yaml

# === モデル設定 ===
model:
  name: "gpt-oss:20b"
  # 方式A: OpenAI互換サーバー（推奨）
  backend: "openai_compatible"
  base_url: "http://localhost:8080/v1"
  # 方式B: 直接ロード（代替）
  # backend: "direct"
  # model_path: "/models/gpt-oss-20b"
  device: "auto"          # "auto", "cuda", "cuda:0", "cpu"

# === 出力設定 ===
output:
  base_dir: "./projects"
  language: "ja"           # 出力言語

# === エフォート設定 ===
effort_settings:
  # （前述のタスク別設定）
  ...

# === 制作ログ設定 ===
production_log:
  enabled: true
  detail_level: "normal"   # "minimal", "normal", "verbose"
  include_prompts: false   # プロンプト全文をログに含めるか
  include_timestamps: true

# === チェックポイント設定 ===
checkpoint:
  enabled: true
  auto_resume: true        # 前回の中断箇所から自動再開
```

### 7.2 プロジェクト固有設定

各プロジェクトフォルダ内にも `config.yaml` を保持し、そのプロジェクトで使用した設定を完全に記録する。再現性の確保に役立つ。

---

## 8. パイプライン改修

### 8.1 改修方針

既存の6フェーズパイプラインの論理構造は維持し、以下を変更する：

1. **API呼び出しの置換**: `o4()` / `o4md()` / `claude()` → `InferenceEngine` 経由
2. **データ保存の追加**: 各推論完了後にファイル自動保存
3. **エフォート適用**: タスクごとに適切なエフォートレベルを適用
4. **ログ記録**: 各ステップの実行状況を制作ログに記録
5. **チェックポイント**: フェーズ完了時にチェックポイントを保存

### 8.2 パイプライン制御

```python
# src/pipeline.py

class WorldBuildingPipeline:
    """ローカル版ワールドビルディングパイプライン"""

    def __init__(self, engine: InferenceEngine, storage: StorageManager,
                 effort: EffortConfig, logger: ProductionLogger):
        self.engine = engine
        self.storage = storage
        self.effort = effort
        self.logger = logger

    def run(self, user_context: str, resume: bool = False):
        """パイプライン全体を実行する

        Args:
            user_context: ユーザーコンテクスト（YAML文字列）
            resume: Trueの場合、前回のチェックポイントから再開
        """
        if resume:
            state = self.storage.load_latest_checkpoint()
            if state:
                self.logger.log("チェックポイントから再開", state["phase"])
                # 完了済みフェーズをスキップ
                ...

        self.logger.log_start(user_context)

        # Phase 1: 100倍拡張
        self._run_phase1_expansion(user_context)

        # Phase 2: キャラクター生成
        self._run_phase2_characters(user_context)

        # Phase 3: 世界構築
        self._run_phase3_worldbuilding()

        # Phase 4: プロット生成
        self._run_phase4_plot(user_context)

        # Phase 5: 小説生成
        self._run_phase5_novel()

        # Phase 6: 設定資料集生成
        self._run_phase6_reference()

        # 後処理
        self.storage.combine_novel_chapters()
        self.logger.log_complete()

    def _run_phase1_expansion(self, user_context: str):
        """Phase 1: 100倍拡張"""
        self.logger.log_phase_start("Phase 1: 100倍拡張")

        # 願望リスト生成
        config = self.effort.get_config("desire_list")
        desire_list = self.engine.generate_json(
            f"以下のコンテクストを抽象的に解釈して拡張し、100個の願望を生成してください。\n\n{user_context}",
            config
        )
        self.storage.save_intermediate("phase1_expansion", "desire_list", desire_list)
        self.logger.log_step("desire_list", "完了", config.effort_level)

        # ... ability_list, role_list, plottype_list, plottype も同様

        self.storage.save_checkpoint("phase1", "complete", self._get_state())
        self.logger.log_phase_end("Phase 1: 100倍拡張")
```

### 8.3 API呼び出し回数（変更なし）

パイプラインの論理構造は維持するため、API呼び出し回数は変わらない。

| フェーズ | 呼び出し回数 | エフォート |
|----------|-------------|-----------|
| Phase 1: 100倍拡張 | 5回 | LOW〜MEDIUM |
| Phase 2: キャラクター生成 | 1回 | MEDIUM |
| Phase 3: 世界構築 | 10回 | MEDIUM〜HIGH |
| Phase 4: プロット生成 | 31回 | LOW〜HIGH |
| Phase 5: 小説生成 | 10回 | HIGH |
| Phase 6: 設定資料集生成 | 17回 | HIGH |
| **合計** | **74回** | — |

---

## 9. エラーハンドリングとリカバリ

### 9.1 改善点

現行v1.2の課題であったエラーハンドリングを改善する。

| 現行の問題 | ローカルバージョンの対策 |
|-----------|----------------------|
| APIエラー時にエラー文字列が変数に代入される | 例外を発生させ、リトライ後にチェックポイントから復元 |
| カーネルリスタートでデータ消失 | 全中間データをファイルに自動保存 |
| 途中再開ができない | チェックポイント機能により任意のフェーズから再開可能 |
| JSON パースエラーの検出なし | パース結果を検証し、失敗時はリトライ |

### 9.2 リトライ機構

```python
# ローカル推論でもメモリ不足やタイムアウトが起こりうる
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒

def generate_with_retry(engine, prompt, config, max_retries=MAX_RETRIES):
    for attempt in range(max_retries):
        try:
            result = engine.generate(prompt, config)
            # JSON出力の場合はパース検証
            if config.output_format == OutputFormat.JSON:
                json.loads(result)  # 検証
            return result
        except Exception as e:
            if attempt < max_retries - 1:
                logger.log_warning(f"推論エラー（リトライ {attempt + 1}/{max_retries}）: {e}")
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(f"推論に{max_retries}回失敗しました: {e}")
```

---

## 10. 制作ログ機能

### 10.1 目的

ワールドビルディングの制作過程を記録し、以下を実現する：

- 制作過程の振り返り・分析
- 生成品質の比較・改善
- パラメータ調整の記録
- 再現性の確保

### 10.2 制作ログの形式

Markdown形式で、人間が読みやすい形で記録する。

```markdown
# 制作ログ: {project_name}

## 基本情報
- **プロジェクト名**: 幻想都市アルカディア
- **作成開始**: 2026-02-13 15:30:00
- **作成完了**: 2026-02-13 17:45:00
- **総実行時間**: 2時間15分
- **使用モデル**: gpt-oss:20b

## 設定サマリー
- **デフォルトエフォート**: medium
- **カスタムエフォート**: story=high, reference=high

---

## Phase 1: 100倍拡張
**開始**: 15:30:00 | **完了**: 15:38:00 | **所要時間**: 8分

| ステップ | エフォート | トークン数 | 所要時間 | 状態 |
|----------|-----------|-----------|---------|------|
| desire_list | medium | 3,240 | 1分32秒 | 完了 |
| ability_list | medium | 3,180 | 1分28秒 | 完了 |
| role_list | medium | 3,410 | 1分35秒 | 完了 |
| plottype_list | low | 1,820 | 0分45秒 | 完了 |
| plottype | low | 980 | 0分22秒 | 完了 |

---

## Phase 2: キャラクター生成
...

(以降、全フェーズの詳細が記録される)

---

## 完了サマリー
- **総推論回数**: 74回
- **成功**: 74回 / **リトライ**: 2回 / **失敗**: 0回
- **総生成トークン数**: 約 285,000 トークン
- **出力ファイル数**: 小説10章 + 設定資料17種 + 中間データ31種
```

### 10.3 制作ログマネージャー

```python
# src/production_log.py

class ProductionLogger:
    """制作ログを管理するクラス"""

    def __init__(self, storage: StorageManager, detail_level: str = "normal"):
        ...

    def log_start(self, user_context: str):
        """パイプライン開始をログに記録"""
        ...

    def log_phase_start(self, phase_name: str):
        """フェーズ開始をログに記録"""
        ...

    def log_step(self, step_name: str, status: str, effort: EffortLevel,
                 tokens: int = 0, duration_sec: float = 0):
        """個別ステップの結果をログに記録"""
        ...

    def log_warning(self, message: str):
        """警告をログに記録（リトライ等）"""
        ...

    def log_phase_end(self, phase_name: str):
        """フェーズ完了をログに記録"""
        ...

    def log_complete(self):
        """パイプライン完了のサマリーをログに記録"""
        ...
```

---

## 11. 移行ガイド

### 11.1 環境構築手順

```bash
# 1. リポジトリをクローン
git clone https://github.com/masa-jp-art/100-times-ai-world-building.git
cd 100-times-ai-world-building

# 2. Python仮想環境を作成
python -m venv .venv
source .venv/bin/activate

# 3. 依存パッケージをインストール
pip install -r requirements.txt

# 4. gpt-oss:20b のセットアップ（環境に応じて選択）
# 方式A: Ollamaを使用する場合
ollama pull gpt-oss:20b
ollama serve  # サーバー起動

# 方式B: vLLMを使用する場合
# vllm serve gpt-oss:20b --port 8080

# 5. 設定ファイルを編集
cp config.yaml.example config.yaml
# config.yaml をエディタで編集（base_url等を環境に合わせて設定）
```

### 11.2 実行方法

```bash
# 基本実行
python local_worldbuilding.py --project "プロジェクト名" --context user_context.yaml

# エフォートレベルを指定して実行
python local_worldbuilding.py --project "プロジェクト名" --context user_context.yaml --effort-all high

# 前回の中断から再開
python local_worldbuilding.py --project "プロジェクト名" --resume
```

### 11.3 依存パッケージ

```
# requirements.txt
openai>=1.0.0         # OpenAI互換クライアント（ローカルサーバー接続用）
pyyaml>=6.0
```

### 11.4 v1.2 との互換性

- 既存のノートブック（v1.2）はそのまま保持し、Google Colab版としても引き続き利用可能
- ローカルバージョンはノートブックとは独立したPythonスクリプトとして提供
- ユーザーコンテクストの形式（YAML）はv1.2と完全互換

---

## 12. 制約事項と前提条件

### 12.1 ハードウェア要件

| 要件 | 最小 | 推奨 |
|------|------|------|
| GPU VRAM | 24GB（量子化モデル使用時） | 48GB以上 |
| システムメモリ | 32GB | 64GB以上 |
| ストレージ | 50GB（モデル含む） | 100GB以上 |
| GPU | NVIDIA RTX 3090 / 4090 | NVIDIA A100 / RTX 4090 |

※ CPU推論も可能だが、74回の推論で数時間〜十数時間を要する可能性がある。

### 12.2 ソフトウェア要件

- Python 3.10以上
- CUDA 12.x（GPU使用時）
- gpt-oss:20b モデルファイル
- OpenAI互換サーバー（Ollama, vLLM, llama.cpp 等）

### 12.3 gpt-oss:20b に関する注意事項

- **トークン制限**: gpt-oss:20b のコンテクストウィンドウサイズに依存。v1.2では後段フェーズで累積コンテクストが非常に大きくなるため、コンテクストウィンドウが不足する場合はプロンプトの圧縮やサマリー化が必要になる可能性がある
- **JSON出力の安定性**: ローカルモデルは外部APIと比較してJSON形式の出力安定性が低い場合がある。パース失敗時のリトライやフォーマット修正の仕組みが重要
- **生成品質**: 20Bパラメータモデルは外部APIの大規模モデルと比較して生成品質に差がある可能性がある。エフォートレベルの調整やプロンプトの最適化で補う

### 12.4 既知のリスク

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| コンテクストウィンドウ超過 | 後段フェーズで入力が切り捨てられる | コンテクスト圧縮・要約機能の追加 |
| JSON出力の不安定性 | パイプラインエラー | リトライ＋JSON修復処理 |
| 長時間実行によるメモリリーク | プロセスクラッシュ | チェックポイントからの再開 |
| GPU VRAM不足 | 推論失敗 | 量子化モデルの使用、バッチサイズ調整 |

---

## 13. 将来の拡張性

### 13.1 短期的な拡張（v2.1）

- **Web UI**: Streamlit / Gradio による対話型インターフェース
- **プロジェクト一覧管理**: 過去のプロジェクトを一覧表示・比較
- **エクスポート機能**: PDF / EPUB / Google Docs 形式へのエクスポート

### 13.2 中期的な拡張（v2.x）

- **モデル切替**: 設定ファイルでの動的モデル切替（他のローカルモデルにも対応）
- **並列実行**: 独立したAPI呼び出しの並列化による高速化
- **プロンプトテンプレート**: カスタムプロンプトの外部化と編集機能
- **多言語対応**: 日本語以外の言語での世界構築

### 13.3 長期的な拡張

- **マルチモデルパイプライン**: タスクに応じて異なるローカルモデルを使い分け
- **RAG統合**: ユーザーの過去の作品や参考資料をベクトルDBに格納し、生成時に参照
- **共同制作**: 複数ユーザーによる同一世界観での共同ワールドビルディング

---

*本文書は Issue #2「ローカルバージョンを作成したい」の要件に基づき作成されたローカルバージョンの設計仕様書です。*
