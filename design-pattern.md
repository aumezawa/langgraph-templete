# AI Agent Disign Pattern

[Sample Codes](https://github.com/GenerativeAgents/agent-book)

## 目標設定と計画生成

### 1. Passive Goal Creator
- ユーザの入力から目標を抽出する

```mermaid
graph LR
  U[ユーザ]-- プロンプト --> I[会話インタフェース]

  subgraph エージェント
    I --> A[Passive Goal Creater]
    A -- コンテキスト取得 --> M[メモリ]
    A -- 明確化された目標 --> G[プラン生成]
  end
```

### 2. Proactive Goal Creator
- 環境や状況から能動的に目標を生成する

```mermaid
graph LR
  U[ユーザ]-- プロンプト --> I[会話インタフェース]

  subgraph E[環境]
    U
  end

  subgraph エージェント
    I --> A[Proactive Goal Creator]
    A -- コンテキスト取得 --> S[センサー]
    A -- コンテキスト取得 --> M[メモリ]
    A -- 明確化された目標 --> G[プラン生成]
  end

  S -- コンテキスト取得 --> E
```

### 3. Prompt/Response Optimizer
- プロンプトの応答を最適化する

```mermaid
graph LR
  U[ユーザ]-- プロンプト --> I

  subgraph A[エージェント]
    I[コンテキストエンジニアリング] --> A1
    A1[Prompt Optimizer] -- 最適化されたプロンプト --> C
    C[その他のコンポーネント] -- 処理結果 --> A2
    A2[Response Optimizer]
  end

  A2 -- 最適化されたレスポンス --> U
```

### 4. Single-Path Plan Generator
- 単一パスの実行計画を生成する

```mermaid
graph LR
  U[ユーザ]-- プロンプト --> A

  subgraph A[調整役エージェント]
    I[コンテキストエンジニアリング] -- ゴール --> A1
    A1[Single-Path Plan Generator] -- プラン --> I
  end

  A --> P

  subgraph P[シングルパスプラン]
    s1[ステップ1] --> s2
    s2[ステップ2] --> s3
    s3[ステップ3]
  end

  subgraph T[作業者エージェント]
    a1[エージェント1]
    a2[エージェント2]
    t1[ツール1]
    t2[ツール2]
  end

  P -- アサイン --> a1
  P --> a2
  P --> t1
  P --> t2
```

### 5 Multi-Path Plan Generator
- 複数パスの実行計画を生成する

```mermaid
graph LR
  U[ユーザ]-- プロンプト --> A
  U[ユーザ]-- 中間ステップの指示 --> A

  subgraph A[調整役エージェント]
    I[コンテキストエンジニアリング] -- ゴール --> A1
    A1[Single-Path Plan Generator] -- プラン --> I
  end

  A --> P

  subgraph P[マルチパスプラン]
    s11[ステップ1] --> s21
    s11 --> s22
    s21[ステップ2-1]
    s22[ステップ2-2] --> s31
    s22 --> s32
    s31[ステップ3-1]
    s32[ステップ3-2]
    s31 --> s4
    s4[ステップ4]
  end

  subgraph T[作業者エージェント]
    a1[エージェント1]
    a2[エージェント2]
    t1[ツール1]
    t2[ツール2]
  end

  P -- アサイン --> a1
  P --> a2
  P --> t1
  P --> t2
```

### 6. One-Shot Model Querying
- 単一のクエリでプラン生成を進める

```mermaid
graph RL
  U[ユーザ] -- プロンプト --> A

  subgraph A[エージェント]
    G[プラン生成] -- クエリ --> B
    B[基盤モデル] -- 実行結果 --> G
  end

  A -- レスポンス --> U
```

### 7. Incremental Model Querying
- 複数回のクエリで段階的にプラン生成を進める

```mermaid
graph RL
  U[ユーザ] -- プロンプト --> A

  subgraph A[エージェント]
    G[プラン生成] -- クエリ --> B
    B[基盤モデル] -- 実行結果 --> G
    G --> B
    B --> G
    G --> B
    B --> G
  end

  A -- レスポンス --> U
  U -- フィードバック --> A
```

## 推論の確実性向上

### 8. Retrieval-Augmented Generation: RAG
- 外部情報を活用して生成を行う

```mermaid
graph LR
  U[ユーザ]-- プロンプト --> A

  subgraph A[エージェント]
    P[プラン生成] -- タスク --> T
    T[タスク実行] -- 実行結果 --> P
  end

  A -- 拡張されたレスポンス --> U

  D[データストア]
  T -- 情報取得 --> D
  D -- 検索結果 --> T
```

### 9. Self-Reflection
- 自身の出力を評価し改善する

```mermaid
graph LR
  U[ユーザ] -- プロンプト --> I

  subgraph A[エージェント]
    direction LR
    I[コンテキストエンジニアリング] -- ゴール --> G
    G[プラン生成] -- 最終プラン --> I
    G -- プラン --> R
    R[Self-Reflection] -- フィードバック --> G
    R <-- 継続学習 --> M[メモリ]
    R -- フィードバック --> R
  end
```

### 10. Cross-Reflection
- 他のモデル、エージェントによる評価を行う

```mermaid
graph LR
  U[ユーザ] -- プロンプト --> I

  subgraph A[エージェント]
    direction LR
    I[コンテキストエンジニアリング] -- ゴール --> G
    G[プラン生成] -- 最終プラン --> I
    G -- プラン --> R
    R[Cross-Reflection] -- フィードバック --> G
    R <-- 継続学習 --> M[メモリ]
  end

  RA[レフレクションエージェント] <-- フィードバック --> R
```

### 11. Human Relfection
- 人間からのフィードバックを取り入れる

```mermaid
graph LR
  U[ユーザ] -- プロンプト --> I

  subgraph A[エージェント]
    direction LR
    I[コンテキストエンジニアリング] -- ゴール --> G
    G[プラン生成] -- 最終プラン --> I
    G -- プラン --> R
    R[Human-Reflection] -- フィードバック --> G
    R <-- 継続学習 --> M[メモリ]
  end

  U <-- フィードバック --> R
  E[エキスパートユーザ] <-- フィードバック --> R
```

### 12. Agent Evaluator
- エージェントの性能を評価する

```mermaid
graph LR
  C[コンテキスト] --> E
  E[エージェント評価機] -- 事前準備 --> E

  subgraph A[エージェント]
    direction TB
    CE[コンテキストエンジニアリング]
    PO[プロンプト/レスポンス最適化]
    PG[プラン生成]
    MG[マルチモーダルガードレール]
  end

  E <-- テストと結果 --> CE
  E <--> PO
  E <--> PG
  E <--> MG
```

## エージェント間の協調

### 13. Voting-Based Cooperation
- 投票によって意思決定を行う

```mermaid
graph LR
  U[ユーザ] -- プロンプト --> A
  A[調整役エージェント] -- 呼び出し --> As

  subgraph As[エージェントチーム]
    V[投票]
    As1[エージェント1] --> V
    As2[エージェント2] --> V
    As3[エージェント3] --> V
  end

  As -- 結果 --> A
```

### 14. Role-Based Cooperation
- 役割に基づいて協力する

```mermaid
graph LR
  U[ユーザ] -- プロンプト --> As

  subgraph As[エージェントチーム]
    direction LR
    P[プランナーエージェント] -- プラン --> A
    A[アサイナーエージェント] -- タスク --> W[作業者エージェント]
    A -- タスク --> G[エージェント生成]
    G --> O[他エージェント]
  end
```

### 15. Debated-Based Cooperation
- 議論を通じて合意形成を行う

```mermaid
graph RL
  U[ユーザ] -- プロンプト --> As

  subgraph As[エージェントチーム]
    direction LR
    A[エージェントA] <--> B
    B[エージェントB] <--> C
    C[エージェントC] <--> A
  end

  As -- レスポンス --> U
```

## 入出力制御

### 16. Multimodal Guardrails
- 多様な形式の入出力を制御する

```mermaid
graph LR
  subgraph E[環境]
    U[ユーザ]
  end

  U -- プロンプト --> I

  subgraph A[エージェント]
    I[コンテキストエンジニアリング]
    O[プロンプト/レスポンス最適化]

    subgraph Gs[マルチモーダルガードレール]
      direction LR
      OG[出力ガードレール]
      RG[RAGガードレール]
      EG[外部実行ガードレール]
    end

    I <--> OG
    O <--> OG

    D[データストア] --> RG
    T[ツール] --> EG

    Gs <--> B[基盤モデル]
  end

  I -- コンテキストの取得 --> E
```

### 17.Tool/Agent Registry
- ツールやサブエージェントを活用する

```mermaid
graph LR
  U[ユーザ] -- プロンプト --> A
  A[調整役エージェント] -- クエリ --> TA

  subgraph TA[ツール/エージェント]
    direction LR
    R[レジストリ]
    R --> W[作業者エージェント]
    R --> T[ツール]
    R --> S[AI/非AIシステム]
  end
```

### 18. Agent Adapter
- 外部ツールとのインターフェースを提供する

```mermaid
graph LR
  U[ユーザ]-- プロンプト --> A

  subgraph A[エージェント]
    P[プラン生成] -- タスク --> E
    E[タスク実行] -- 実行結果 --> P
    E <--> AA[エージェントアダプタ]
  end

  AA <-- 情報取得 --> D[データストア]
  AA <-- タスク --> T[ツール]
```
