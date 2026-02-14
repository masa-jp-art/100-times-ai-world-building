# 実装計画: 推論エフォートレベル設定機能

## 概要

既存のノートブック `20250601-100-TIMES-AI-WORLD-BUILDING-v1.2.ipynb` に、タスクごとに推論エフォートレベル（LOW / MEDIUM / HIGH）を設定できる機能を追加する。

## 現状分析

### 現在の関数シグネチャ

```python
# Cell 2 で定義されている3つの推論関数（モデルは gpt-oss:20b に変更済み）
def o4(prompt)        # gpt-oss:20b, JSON出力, パラメータ固定
def o4md(prompt)      # gpt-oss:20b, Markdown出力, パラメータ固定
def claude(prompt)    # gpt-oss:20b, max_tokens=16000, temperature=1 固定
```

### 問題点

- `max_tokens` と `temperature` がハードコードされている
- 全74回の推論がすべて同一パラメータで実行される
- リスト分割のような軽いタスクと小説執筆のような重いタスクに差がない

## 実装ステップ

### Step 1: エフォートレベル定義を Cell 2 に追加

Cell 2（関数定義セル）に、エフォートレベルの定義と設定辞書を追加する。

**追加するコード:**

```python
# === エフォートレベル設定 ===

EFFORT_LEVELS = {
    "low": {
        "max_tokens": 2048,
        "temperature": 0.3,
    },
    "medium": {
        "max_tokens": 4096,
        "temperature": 0.7,
    },
    "high": {
        "max_tokens": 16000,
        "temperature": 1.0,
    },
}

# タスク別デフォルトエフォート設定
TASK_EFFORT = {
    # Phase 1: 100倍拡張
    "desire_list":    "medium",
    "ability_list":   "medium",
    "role_list":      "medium",
    "plottype_list":  "low",
    "plottype":       "low",
    # Phase 2: キャラクター生成
    "characters_list": "medium",
    # Phase 3: 世界構築
    "events":                "medium",
    "observation":           "medium",
    "interpretation":        "medium",
    "media":                 "medium",
    "important_past_events": "medium",
    "social_structure":      "high",
    "living_environment":    "high",
    "social_groups":         "medium",
    "people_list":           "high",
    "future_scenarios":      "medium",
    # Phase 4: プロット生成
    "plot":            "high",
    "plot_split":      "low",       # plot_1〜plot_10（分割処理）
    "plot_keywords":   "low",       # キーワード抽出
    "plot_reference":  "low",       # 参考資料検索
    # Phase 5: 小説生成
    "story":           "high",      # story_1〜story_10
    # Phase 6: 設定資料集生成
    "reference":       "high",      # reference_* 全17種
}

def get_effort(task_name):
    """タスク名からエフォートパラメータを取得する"""
    level = TASK_EFFORT.get(task_name, "medium")
    return EFFORT_LEVELS[level]
```

**変更箇所:** Cell 2 の関数定義の直前（`client = OpenAI(...)` の前）に挿入

### Step 2: 推論関数にエフォートレベル引数を追加

3つの推論関数すべてに `task_name` 引数を追加し、エフォートレベルに応じて `max_tokens` と `temperature` を変える。

#### `o4(prompt)` → `o4(prompt, task_name="default")`

```python
def o4(prompt, task_name="default"):
    try:
        effort = get_effort(task_name)
        response = client.chat.completions.create(
            model="gpt-oss:20b",
            max_tokens=effort["max_tokens"],
            temperature=effort["temperature"],
            messages=[
                {"role": "system", "content": "常に日本語で応答します。常にjson形式で応答します。"},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return yaml.safe_dump(data, allow_unicode=True)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"
```

#### `o4md(prompt)` → `o4md(prompt, task_name="default")`

```python
def o4md(prompt, task_name="default"):
    try:
        effort = get_effort(task_name)
        response = client.responses.create(
            model="gpt-oss:20b",
            max_tokens=effort["max_tokens"],
            temperature=effort["temperature"],
            input=[
                {"role": "system", "content": "常に日本語で応答します。常にMarkdown形式で応答します。"},
                {"role": "user", "content": prompt},
            ],
        )
        return response.output_text
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"
```

#### `claude(prompt)` → `claude(prompt, task_name="default")`

```python
def claude(prompt, task_name="default"):
    try:
        effort = get_effort(task_name)
        message = client.chat.completions.create(
            model="gpt-oss:20b",
            max_tokens=effort["max_tokens"],
            temperature=effort["temperature"],
            messages=[
                {"role": "system", "content": "常に表現力豊かな日本語で出力します。"},
                {"role": "user", "content": prompt},
            ],
        )
        return message.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"
```

**変更箇所:** Cell 2 の既存の3関数を上記で置換

### Step 3: Cell 6 の全呼び出しに task_name を付与

Cell 6 には Phase 1〜4 の推論呼び出しが含まれる。各 `o4(...)` 呼び出しに `task_name` を追加。

**変更一覧（Phase 1: 100倍拡張）:**

| 変更前 | 変更後 |
|--------|--------|
| `desire_list = o4(f"...")` | `desire_list = o4(f"...", task_name="desire_list")` |
| `ability_list = o4(f"...")` | `ability_list = o4(f"...", task_name="ability_list")` |
| `role_list = o4(f"...")` | `role_list = o4(f"...", task_name="role_list")` |
| `plottype_list = o4(f"...")` | `plottype_list = o4(f"...", task_name="plottype_list")` |
| `plottype = o4(f"...")` | `plottype = o4(f"...", task_name="plottype")` |

**変更一覧（Phase 2: キャラクター生成）:**

| 変更前 | 変更後 |
|--------|--------|
| `characters_list = o4(f"...")` | `characters_list = o4(f"...", task_name="characters_list")` |

**変更一覧（Phase 3: 世界構築）:**

| 変更前 | 変更後 |
|--------|--------|
| `events = o4(f"...")` | `events = o4(f"...", task_name="events")` |
| `observation = o4(f"...")` | `observation = o4(f"...", task_name="observation")` |
| `interpretation = o4(f"...")` | `interpretation = o4(f"...", task_name="interpretation")` |
| `media = o4(f"...")` | `media = o4(f"...", task_name="media")` |
| `important_past_events = o4(f"...")` | `important_past_events = o4(f"...", task_name="important_past_events")` |
| `social_structure = o4(f"...")` | `social_structure = o4(f"...", task_name="social_structure")` |
| `living_environment = o4(f"...")` | `living_environment = o4(f"...", task_name="living_environment")` |
| `social_groups = o4(f"...")` | `social_groups = o4(f"...", task_name="social_groups")` |
| `people_list = o4(f"...")` | `people_list = o4(f"...", task_name="people_list")` |
| `future_scenarios = o4(f"...")` | `future_scenarios = o4(f"...", task_name="future_scenarios")` |

**変更一覧（Phase 4: プロット生成）:**

| 変更前 | 変更後 |
|--------|--------|
| `plot = o4(f"...")` | `plot = o4(f"...", task_name="plot")` |
| ループ内 `plot_n = o4(f"...")` | `plot_n = o4(f"...", task_name="plot_split")` |
| ループ内 `keywords = o4(f"...")` | `keywords = o4(f"...", task_name="plot_keywords")` |
| ループ内 `reference = o4(f"...")`※o4mdの可能性あり | `reference = o4md(f"...", task_name="plot_reference")` |

### Step 4: Cell 9 の全呼び出しに task_name を付与

Cell 9 には Phase 5（小説生成）と Phase 6（設定資料集生成）が含まれる。

**変更一覧（Phase 5: 小説生成）:**

| 変更前 | 変更後 |
|--------|--------|
| `story_n = claude(f"...")` | `story_n = claude(f"...", task_name="story")` |

**変更一覧（Phase 6: 設定資料集生成 — 全17箇所）:**

全 `claude(reference_prompt + f"...")` を `claude(reference_prompt + f"...", task_name="reference")` に変更。

対象:
- `reference_characters_list`
- `reference_plot`
- `reference_user_context`
- `reference_events`
- `reference_observation`
- `reference_interpretation`
- `reference_media`
- `reference_important_past_events`
- `reference_social_structure`
- `reference_living_environment`
- `reference_social_groups`
- `reference_people_list`
- `reference_future_scenarios`
- `reference_desire_list`
- `reference_ability_list`
- `reference_role_list`
- `reference_plottype_list`

## 変更サマリー

| セル | 変更内容 | 変更量 |
|------|---------|--------|
| Cell 2 | エフォートレベル定義＋設定辞書を追加、3関数を改修 | 約50行追加、3関数修正 |
| Cell 6 | 全 `o4()` 呼び出しに `task_name` 引数を追加 | 約47箇所の引数追加 |
| Cell 9 | 全 `claude()` 呼び出しに `task_name` 引数を追加 | 約27箇所の引数追加 |

## ユーザー操作

ユーザーは Cell 2 の `TASK_EFFORT` 辞書を編集することで、各タスクのエフォートレベルをカスタマイズできる。

```python
# 例: 全体的に高速化したい場合
TASK_EFFORT["story"] = "medium"  # 小説生成を medium に下げる

# 例: 特定のタスクだけ高品質にしたい場合
TASK_EFFORT["characters_list"] = "high"
```
