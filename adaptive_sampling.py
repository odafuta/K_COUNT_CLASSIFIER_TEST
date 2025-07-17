import random
import itertools
import time
import sys
from typing import List, Set, Tuple, Dict, Any

def generate_LVCA_adaptive_sampling(
    n: int,
    tau: int,
    k: int,
    seed: int = 0,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Adaptive Sampling を使用してバイナリのカバーリング配列を生成します。

    Parameters:
    n (int): パラメータ数 (列数)
    tau (int): 強度 (t-way)
    k (int): 各行に含まれる1の最大数
    seed (int): 乱数シード
    verbose (bool): 詳細出力を制御

    Returns:
    dict: 結果を含む辞書 (行数, 被覆状況, 実行時間など)
    """
    start_time = time.perf_counter()
    rng = random.Random(seed)

    # すべてのτ-way組み合わせを生成 (all-zero除外)
    all_combinations = set()
    for indices in itertools.combinations(range(n), tau):
        for values in itertools.product([0, 1], repeat=tau):
            if any(values):  # all-zeroを除外
                combo = tuple(sorted((i, v) for i, v in zip(indices, values)))
                all_combinations.add(combo)

    U_size = len(all_combinations)
    uncovered = set(all_combinations)
    A = []  # カバーリング配列
    A_set = set()  # 重複チェック用のセット
    iteration = 0

    if verbose:
        print(f"n={n}, tau={tau}, k={k}")
        print(f"組み合わせ総数: {U_size}")

    # ヘルパー関数: 行がカバーする組み合わせを計算
    def compute_row_coverage(row: List[int]) -> Set[Tuple[Tuple[int, int], ...]]:
        coverage = set()
        for indices in itertools.combinations(range(n), tau):
            if any(row[i] for i in indices):  # all-zeroを除外
                combo = tuple(sorted((i, row[i]) for i in indices))
                coverage.add(combo)
        return coverage

    # メインループ: 未カバー組み合わせがなくなるまで
    while uncovered:
        iteration += 1
        row = [0] * n
        c = rng.randint(1, k)  # 1の数をランダム選択 (1〜k)

        # ラベル頻度に基づいた適応的サンプリング
        if A:
            label_counts = [0] * n
            for r in A:
                for i in range(n):
                    if r[i] == 1:
                        label_counts[i] += 1
            labels = list(range(n))
            labels.sort(key=lambda x: label_counts[x])
            m = rng.randint(1, (n + 1) // 2)
            leastm = labels[:m]
            others = labels[m:]
        else:
            labels = list(range(n))
            rng.shuffle(labels)
            m = rng.randint(1, (n + 1) // 2)
            leastm = labels[:m]
            others = labels[m:]

        c1 = min(m, (c + 1) // 2)
        c2 = c - c1

        selected = rng.sample(leastm, c1)
        if len(others) >= c2:
            selected += rng.sample(others, c2)

        for i in selected:
            row[i] = 1

        # 重複チェック
        row_tuple = tuple(row)
        if row_tuple in A_set:
            if verbose and iteration % 10 == 0:
                print(f"Iteration {iteration}: 重複行をスキップ")
            continue

        # カバレッジ計算と更新
        row_coverage = compute_row_coverage(row)
        new_cover = row_coverage & uncovered
        new_cover_count = len(new_cover)

        if not new_cover_count:
            if verbose and iteration % 10 == 0:
                print(f"Iteration {iteration}: 新規カバレッジなし")
            continue

        # 行を追加
        A.append(row)
        A_set.add(row_tuple)
        uncovered -= new_cover

        if verbose and (iteration % 10 == 0 or not uncovered):
            coverage_percent = (U_size - len(uncovered)) / U_size
            print(f"Iteration {iteration}: 追加行 - カバー: {new_cover_count} | 累計: {len(A)}行 | 被覆率: {coverage_percent:.2%}")

    # 最小化フェーズ: 冗長な行を削除
    minimized_A = []
    total_cover = set()

    # 逆順で行を追加 (よりカバレッジに貢献する行を後で追加)
    for row in reversed(A):
        temp_array = minimized_A.copy()
        temp_array.append(row)

        # 一時カバレッジ計算
        temp_cover = total_cover.copy()
        row_coverage = compute_row_coverage(row)
        temp_cover |= row_coverage

        # カバレッジが完全か確認
        if temp_cover >= all_combinations:
            total_cover = temp_cover
        else:
            minimized_A.append(row)

    # 結果の検証
    final_cover = set()
    for row in minimized_A:
        final_cover |= compute_row_coverage(row)

    covered = (final_cover == all_combinations)
    coverage_percentage = len(final_cover) / U_size if U_size > 0 else 1.0
    end_time = time.perf_counter()
    total_time = end_time - start_time

    if verbose:
        print(f"\n最終結果:")
        print(f"初期行数: {len(A)}")
        print(f"最小化後行数: {len(minimized_A)}")
        print(f"被覆率: {coverage_percentage:.2%}")
        print(f"実行時間: {total_time:.4f}秒")

    return {
        "n": n,
        "tau": tau,
        "k": k,
        "num_rows": len(minimized_A),
        "covered": covered,
        "coverage_percentage": coverage_percentage,
        "time": total_time,
        "covering_array": minimized_A
    }

# コマンドライン実行用
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python adaptive_sampling.py n tau k [seed]")
        print("Example: python adaptive_sampling.py 10 2 5 42")
        sys.exit(1)

    n = int(sys.argv[1])
    tau = int(sys.argv[2])
    k = int(sys.argv[3])
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 42

    result = generate_LVCA_adaptive_sampling(
        n, tau, k,
        seed=seed,
        verbose=True
    )

    # 小さいインスタンスの場合のみ配列を表示
    if n <= 20 and result["num_rows"] <= 50:
        print("\nカバーリング配列:")
        for i, row in enumerate(result["covering_array"], 1):
            print(f"{i:3}: {row}")
