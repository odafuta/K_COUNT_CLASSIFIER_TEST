import copy
import random
import itertools
import time
import sys
from typing import List, Set, Tuple, Dict, Any
from collections import Counter

# === 差分管理プルーニングユーティリティ ===
# covers(row, combo) と all_combinations は generate_LVCA_adaptive_sampling 内で定義される

def prune_rows_diff(A: List[List[int]], row_to_combos: List[List[Tuple[int, int]]]) -> List[List[int]]:
    """
    差分管理による高速プルーニング
    A: List of rows
    row_to_combos: 各行がカバーする tau-組み合わせのリスト
    """
    combo_counts = Counter()
    for combos in row_to_combos:
        combo_counts.update(combos)

    minimized: List[List[int]] = []
    for row, combos in zip(A, row_to_combos):
        # 削除可能か判定
        removable = all(combo_counts[c] > 1 for c in combos)
        if removable:
            # 削除するときはカウントをデクリメント
            for c in combos:
                combo_counts[c] -= 1
        else:
            minimized.append(row)
    return minimized


def generate_LVCA_adaptive_sampling(n: int, tau: int, k: int, seed: int = 0, verbose: bool = True) -> Dict[str, Any]:
    start_time = time.perf_counter()
    rng = random.Random(seed)

    # τ-way 組み合わせの全パターン生成
    all_combinations: Set[Tuple[Tuple[int, int], ...]] = {
        tuple(sorted((i, v) for i, v in zip(indices, values)))
        for indices in itertools.combinations(range(n), tau)
        for values in itertools.product([0, 1], repeat=tau)
        if any(values)
    }
    uncovered = set(all_combinations)

    # covers 関数定義
    def covers(row: List[int], combo: Tuple[Tuple[int, int], ...]) -> bool:
        return all(row[i] == v for i, v in combo)

    # 各行がカバーする τ-組み合わせを列挙する関数
    def enumerate_combinations(row: List[int]) -> List[Tuple[Tuple[int, int], ...]]:
        return [combo for combo in all_combinations if covers(row, combo)]

    A: List[List[int]] = []
    U_size = len(all_combinations)
    iteration = 0

    if verbose:
        print(f"n={n}, tau={tau}, k={k}")
        print(f"組み合わせ総数: {U_size}")

    # サンプリングループ
    while uncovered:
        iteration += 1
        row = [0] * n
        c =  k

        # ラベルのソート
        label_counts = [sum(r[i] for r in A) for i in range(n)]
        labels = list(range(n))
        labels.sort(key=lambda x: label_counts[x])

        m = rng.randint(1, (n + 1) // 2)
        leastm, others = labels[:m], labels[m:]
        c1 = min(m, (c + 1) // 2)
        c2 = c - c1
        selected = rng.sample(leastm, c1) + (rng.sample(others, c2) if len(others) >= c2 else [])
        for i in selected:
            row[i] = 1

        if row not in A:
            A.append(row)
            for combo in enumerate_combinations(row):
                uncovered.discard(combo)

        if verbose and (iteration % 10 == 0 or not uncovered):
            covered = U_size - len(uncovered)
            print(f"Iteration {iteration}: 累計 {len(A)}行, 被覆率: {covered/U_size:.2%}")

    # プルーニング: 差分管理版
    row_to_combos = [enumerate_combinations(r) for r in A]
    A_pruned = prune_rows_diff(A, row_to_combos)

    # 結果計算
    def compute_coverage(rows: List[List[int]]) -> Set[Tuple[Tuple[int, int], ...]]:
        cov = set()
        for row in rows:
            for indices in itertools.combinations(range(n), tau):
                vals = tuple((i, row[i]) for i in indices)
                if any(v for _, v in vals):
                    cov.add(vals)
        return cov

    final_cover = compute_coverage(A_pruned)
    coverage_percentage = len(final_cover) / U_size
    total_time = time.perf_counter() - start_time

    if verbose:
        print(f"\n最終結果: 初期行数={len(A)}, 最小化後={len(A_pruned)}, 被覆率={coverage_percentage:.2%}, 時間={total_time:.4f}s")

    return {
        "n": n,
        "tau": tau,
        "k": k,
        "num_rows": len(A_pruned),
        "covered": final_cover == all_combinations,
        "coverage_percentage": coverage_percentage,
        "time": total_time,
        "covering_array": A_pruned
    }


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python adaptive_sampling.py n tau k [seed]")
        sys.exit(1)

    n, tau, k = map(int, sys.argv[1:4])
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 42
    result = generate_LVCA_adaptive_sampling(n, tau, k, seed)

    if n <= 20 and result["num_rows"] <= 50:
        print("\nカバーリング配列:")
        for i, row in enumerate(result["covering_array"], 1):
            print(f"{i:3}: {row}")

