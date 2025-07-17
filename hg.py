import itertools
import random
import time
import sys
from typing import List, Set, Tuple, Dict, Any

def generate_binary_covering_array_heuristic_greedy(
    n: int,
    tau: int,
    k: int,
    num_candidate_rows_sample: int = 5000,
    seed: int = 0,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    ヒューリスティックな貪欲法を用いてバイナリのカバレッジアレイを生成します。

    Parameters:
    n (int): パラメータ数 (列数)
    tau (int): 強度 (t-way)
    k (int): 各行に含まれる1の最大数 (1からkまで)
    num_candidate_rows_sample (int): 各ステップで評価する候補行のサンプリング数
    seed (int): 乱数シード
    verbose (bool): 詳細出力を制御

    Returns:
    dict: 結果を含む辞書 (行数, 被覆状況, 実行時間など)
    """
    start_time = time.perf_counter()
    rng = random.Random(seed)

    # すべてのτ-way組み合わせを生成
    all_combos = set()
    for indices in itertools.combinations(range(n), tau):
        for values in itertools.product([0, 1], repeat=tau):
            # 組み合わせをソートして一意性を保証
            combo = tuple(sorted((i, v) for i, v in zip(indices, values)))
            all_combos.add(combo)

    uncovered_combos = set(all_combos)
    covering_array = []
    U_size = len(all_combos)

    if verbose:
        print(f"n={n}, tau={tau}, k={k}")
        print(f"組み合わせ総数: {U_size}")
        print(f"候補行サンプリング数: {num_candidate_rows_sample}")

    # ランダムな制約付き行を生成するヘルパー関数
    def generate_random_k_constrained_row():
        ones_count = rng.randint(1, k)  # 1からkの間でランダムに1の数を選択
        ones_positions = rng.sample(range(n), ones_count)
        return [1 if i in ones_positions else 0 for i in range(n)]

    iteration = 0
    coverage_history = []
    last_coverage = 0

    while uncovered_combos:
        iteration += 1
        best_row = None
        best_covered_count = -1
        candidate_rows = []

        # 候補行を生成
        for _ in range(num_candidate_rows_sample):
            row = generate_random_k_constrained_row()
            if row:
                candidate_rows.append(row)

        if not candidate_rows:
            error_msg = (
                f"Iteration {iteration}: 有効な候補行が生成されませんでした。"
                f"パラメータ確認: n={n}, k={k}"
            )
            if verbose:
                print(error_msg)
            return {
                "n": n,
                "tau": tau,
                "k": k,
                "num_rows": len(covering_array),
                "covered": False,
                "coverage_percentage": len(all_combos - uncovered_combos) / U_size,
                "time": time.perf_counter() - start_time,
                "covering_array": covering_array,
                "error": error_msg
            }

        # 最良の行を選択
        for row in candidate_rows:
            covered_count = 0
            for combo in uncovered_combos:
                if all(row[i] == v for i, v in combo):
                    covered_count += 1
            if covered_count > best_covered_count:
                best_covered_count = covered_count
                best_row = row

        # 新しいカバレッジがない場合の処理
        if best_covered_count <= 0:
            if verbose:
                print(f"Iteration {iteration}: 新しい組み合わせをカバーできませんでした。終了します。")
            break

        # 最良の行を追加
        covering_array.append(best_row)

        # カバーされた組み合わせを削除
        to_remove = set()
        for combo in uncovered_combos:
            if all(best_row[i] == v for i, v in combo):
                to_remove.add(combo)
        uncovered_combos -= to_remove

        # 進捗記録
        current_coverage = U_size - len(uncovered_combos)
        coverage_history.append(current_coverage)

        if verbose and (current_coverage - last_coverage > 0 or iteration % 10 == 0):
            print(f"Iteration {iteration}: 行追加 - カバー: {best_covered_count} | 累計: {current_coverage}/{U_size} ({current_coverage/U_size:.2%})")
            last_coverage = current_coverage

    # 最終結果の計算
    end_time = time.perf_counter()
    total_time = end_time - start_time
    covered = len(uncovered_combos) == 0
    coverage_percentage = 1.0 if covered else (U_size - len(uncovered_combos)) / U_size

    if verbose:
        print("\n最終結果:")
        print(f"生成行数: {len(covering_array)}")
        print(f"被覆率: {coverage_percentage:.2%}")
        print(f"実行時間: {total_time:.4f}秒")

    return {
        "n": n,
        "tau": tau,
        "k": k,
        "num_rows": len(covering_array),
        "covered": covered,
        "coverage_percentage": coverage_percentage,
        "time": total_time,
        "covering_array": covering_array
    }

# コマンドライン実行用
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python greedy_algorithm.py n tau k [num_candidate_rows_sample] [seed]")
        print("Example: python greedy_algorithm.py 10 2 5 1000 42")
        sys.exit(1)

    n = int(sys.argv[1])
    tau = int(sys.argv[2])
    k = int(sys.argv[3])
    num_candidate = int(sys.argv[4]) if len(sys.argv) > 4 else 5000
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 42

    result = generate_binary_covering_array_heuristic_greedy(
        n, tau, k,
        num_candidate_rows_sample=num_candidate,
        seed=seed,
        verbose=True
    )

    # 小さいインスタンスの場合のみ配列を表示
    if n <= 20 and result["num_rows"] <= 50:
        print("\nカバーリング配列:")
        for i, row in enumerate(result["covering_array"], 1):
            print(f"{i:3}: {row}")
