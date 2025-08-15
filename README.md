# K_COUNT_CLASSIFIER_TEST
機械学習マルチ分類器に対するk制約を持たせたテストケース生成

## 概要
このプロジェクトは、機械学習マルチ分類器に対するk制約（各行に含まれる1の数がk以下(厳密にはk個)）を持つテストケース生成アルゴリズムの比較実験を行います。

## 必要な環境
- Python 3.7以上
- Java Runtime Environment (JRE) または Java Development Kit (JDK) - ACTSツール実行用
- 必要なPythonパッケージ:
  - pandas
  - matplotlib
  - numpy

## インストール手順

### 1. 依存関係のインストール
```bash
pip install pandas matplotlib numpy
```

### 2. Java環境の確認
ACTSツールを使用する場合は、Javaがインストールされていることを確認してください：
```bash
java -version
```

## 実行手順

### 1. メイン実験の実行（推奨）
4つのアルゴリズム（Adaptive Sampling、Heuristic Greedy、Simulated Annealing、ACTS）を比較する実験を実行します：

#### 基本的な実行
```bash
python test_script.py
```

#### タイムアウト設定付き実行
```bash
# 全体のタイムアウトを60秒に設定
python test_script.py --timeout-seconds 60

# アルゴリズム別にタイムアウトを設定
python test_script.py --timeout-seconds 60 --timeout-as 120 --timeout-hg 60 --timeout-sa 60 --timeout-acts 60

# タイムアウトを無効化
python test_script.py --no-timeout
```

#### 出力ファイルを指定
```bash
python test_script.py --results-csv my_results.csv --checkpoint my_checkpoint.json
```

#### 特定のアルゴリズムをスキップ
**スキップオプション** - 特定のアルゴリズムを実行しないようにする方法：

```bash
# ACTSのみをスキップ
python test_script.py --skip-acts

# Adaptive SamplingとSimulated Annealingをスキップ
python test_script.py --skip-as --skip-sa

# Heuristic GreedyとACTSをスキップ
python test_script.py --skip-hg --skip-acts

# 3つのアルゴリズムのみ実行（ACTSをスキップ）
python test_script.py --skip-acts
```

### 実験スクリプトの特徴

#### レジリエント実行（中断・再開対応）
- **自動チェックポイント**: 各テストケース終了後に進捗を自動保存
- **中断・再開**: 実験が途中で中断されても、同じコマンドで再実行すると完了済みテストケースをスキップして続行
- **インクリメンタル保存**: 結果をテストケース単位でCSVに追記（ファイル破損リスク最小化）

#### タイムアウト機能
- **グローバルタイムアウト**: 全アルゴリズムに適用されるデフォルトタイムアウト
- **個別タイムアウト**: アルゴリズムごとに異なるタイムアウト設定が可能
- **タイムアウト無効化**: `--no-timeout` オプションでタイムアウトを完全に無効化

#### エラーハンドリング
- **ACTS環境エラー**: Java環境がない場合、その実行回のみスキップして他アルゴリズムは継続
- **プロセス強制終了**: タイムアウト時は子プロセスを確実に終了
- **チェックポイント保護**: 原子操作でチェックポイントファイルを保存

このスクリプトは以下を自動的に実行します：
- テストケース生成（`testcase_generator.py`を自動実行）
- 各テストケースに対して4つのアルゴリズムを実行
- 結果を `result_summary.csv` に保存
- 進捗を `results_checkpoint.json` に保存
- コンソールに結果テーブルを表示

### 2. 結果の正規化と可視化
実験結果をグラフ化します：
```bash
python plot.py
```
これにより 正規化ファイル`output.csv` と比較グラフ（PNG形式）が生成されます。

## 個別実行手順

### テストケース生成のみ
テストケースを個別に生成したい場合：
```bash
python testcase_generator.py
```
これにより `test_cases.json` ファイルが生成されます。

## 個別正規化結果csvファイル作成
```bash
# 上述手順実行により正規化ファイル`output.csv` 生成後以下実行
python split_csv_by_algorithm.py
```
これにより 各々`<アルゴリズム名>_result.json` ファイルが生成されます。

## 個別アルゴリズムの実行

### Adaptive Sampling
```bash
python adaptive_sampling.py n tau k [seed]
```

### Heuristic Greedy
```bash
python heuristic_greedy.py n tau k [seed]
```

### Simulated Annealing
```bash
python simulated_annealing.py n tau k [seed]
```

### ACTS (Advanced Combinatorial Testing System)
```bash
python acts_runner.py n tau k [seed]
```
例：
```bash
python acts_runner.py 10 2 3 42
```

**内部で実行されるコマンド：**
```bash
java -jar -Dchandler=solver -Ddoi={tau} -Doutput=csv -Dprogress=off acts_3.2.jar {input_file} {output_file}
```

**処理の流れ：**
1. **入力ファイル生成**: `acts_inputs/acts_input_n{n}_tau{tau}_k{k}.txt` を作成
   - パラメータ定義: p1(int): 0,1, p2(int): 0,1, ..., pn(int): 0,1
   - 制約条件: p1 + p2 + ... + pn = k
2. **ACTS実行**: JavaコマンドでACTSツールを実行
3. **結果解析**: `acts_inputs/acts_output_n{n}_tau{tau}_k{k}.csv` を解析
4. **制約検証**: 各行の1の数がk個であることを確認

**注意**: Java環境が必要です。`java -version` で確認してください。

## 出力ファイル

### 主要な出力ファイル
- `test_cases.json`: 生成されたテストケース
- `result_summary.csv`: 実験結果のサマリー（インクリメンタル追記）
- `results_checkpoint.json`: 実験進捗のチェックポイント（中断・再開用）
- `output.csv`: プロット用に整形された結果
- `fig/`: 比較グラフ（PNG形式）

### アルゴリズム別結果ファイル
- `adaptive_sampling_results.csv`
- `heuristic_greedy_results.csv`
- `simulated_annealing_results.csv`
- `acts_results.csv`

### 実験再開・リセット
- **実験再開**: 同じコマンドで実行すると、完了済みテストケースを自動スキップ
- **実験リセット**: `results_checkpoint.json` と `result_summary.csv` を削除するか、別ファイル名を指定
- **部分再実行**: チェックポイントファイルを手動編集して特定テストケースのみ再実行可能

## パラメータ説明

- **n**: パラメータ数（列数）
- **tau**: 強度（t-way coverage）
- **k**: 各行に含まれる1の最大数

## 制約条件

各アルゴリズムは以下の制約を満たすテストケースを生成します：
- 各行は0と1のみで構成
- 各行の1の数はk以下
- tau-wayの組み合わせをすべてカバー

## トラブルシューティング

### Javaが見つからない場合
ACTSツールを使用する際にJavaが見つからないエラーが発生した場合：
1. Javaがインストールされているか確認
2. 環境変数PATHにJavaが含まれているか確認
3. `java -version` コマンドで動作確認

### タイムアウトエラー
一部のテストケースでタイムアウトが発生する場合：
- `--timeout-seconds` パラメータを調整
- アルゴリズム別に `--timeout-as`, `--timeout-hg`, `--timeout-sa`, `--timeout-acts` で個別設定
- `--no-timeout` でタイムアウトを無効化
- より小さなテストケースから開始

### 実験中断・再開
- 実験が途中で中断された場合、同じコマンドで再実行すると自動的に続行
- チェックポイントファイルが破損した場合、削除して最初から再実行
- 特定のテストケースで問題が発生した場合、チェックポイントファイルを編集してスキップ可能

## ファイル構成

```
k_count_classifier_test/
├── test_script.py              # メイン実験スクリプト（レジリエント実行対応）
├── testcase_generator.py       # テストケース生成
├── adaptive_sampling.py        # Adaptive Sampling アルゴリズム
├── heuristic_greedy.py         # Heuristic Greedy アルゴリズム
├── simulated_annealing.py      # Simulated Annealing アルゴリズム
├── acts_runner.py              # ACTS ツール実行
├── plot.py                     # 4アルゴリズム結果可視化
├── plot_without_acts.py        # ACTS除く3つアルゴリズム結果可視化
├── split_csv_by_algorithm.py   # 個別正規化結果csvファイル作成
├── acts_3.2/                   # ACTS ライブラリ
├── acts_3.2.jar               # ACTS ライブラリのJavaプログラム本体
├── acts_inputs/                # ACTS 入力ファイル
├── fig/                        # 生成グラフ
├── result_summary.csv          # 実験結果サマリー（デフォルト）
├── results_checkpoint.json     # 実験進捗チェックポイント（デフォルト）
└── test_cases.json            # 生成されたテストケース
```

## ライセンス
このプロジェクトは研究目的で作成されています。