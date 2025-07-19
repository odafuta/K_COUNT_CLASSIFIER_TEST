import copy
import random
import itertools
import time
import sys
from typing import List, Set, Tuple, Dict, Any

def generate_LVCA_adaptive_sampling(n: int, tau: int, k: int, seed: int = 0, verbose: bool = True) -> Dict[str, Any]:
    start_time = time.perf_counter()
    rng = random.Random(seed)

    def compute_coverage(rows: List[List[int]]) -> Set[Tuple[Tuple[int, int], ...]]:
        coverage = set()
        for row in rows:
            for indices in itertools.combinations(range(n), tau):
                if any(row[i] for i in indices):  # all-zeroは除外
                    coverage.add(tuple(sorted((i, row[i]) for i in indices)))
        return coverage

    all_combinations = {
        tuple(sorted((i, v) for i, v in zip(indices, values)))
        for indices in itertools.combinations(range(n), tau)
        for values in itertools.product([0, 1], repeat=tau)
        if any(values)
    }
    uncovered = set(all_combinations)
    A, A_set = [], set()
    U_size, iteration = len(all_combinations), 0

    if verbose:
        print(f"n={n}, tau={tau}, k={k}")
        print(f"組み合わせ総数: {U_size}")

    while uncovered:
        iteration += 1
        row = [0] * n
        c = rng.randint(1, k)

        label_counts = [sum(r[i] for r in A) for i in range(n)]
        labels = list(range(n))
        labels.sort(key=lambda x: label_counts[x])

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

        if row not in A:
            A.append(row)
            for indices in itertools.combinations(range(n), tau):
                values = tuple((i, row[i]) for i in indices)
                if any(v for _, v in values):  # all-zero除外
                    uncovered.discard(values)

        if verbose and (iteration % 10 == 0 or not uncovered):
            covered = U_size - len(uncovered)
            print(f"Iteration {iteration}: 累計 {len(A)}行, 被覆率: {covered / U_size:.2%}")

    # 最小化: 逆順で有効行のみ保持
    # 最小化: 不要な行を削る
    minimized_A = copy.deepcopy(A)
    for row in A:
        temp = minimized_A[:]
        temp.remove(row)
        temp_covered = set()
        for r in temp:
            for indices in itertools.combinations(range(n), tau):
                values = tuple((i, r[i]) for i in indices)
                temp_covered.add(values)
        if temp_covered >= all_combinations:
            minimized_A.remove(row)


    final_cover = compute_coverage(minimized_A)
    coverage_percentage = len(final_cover) / U_size
    total_time = time.perf_counter() - start_time

    if verbose:
        print(f"\n最終結果: 初期行数={len(A)}, 最小化後={len(minimized_A)}, 被覆率={coverage_percentage:.2%}, 時間={total_time:.4f}s")

    return {
        "n": n,
        "tau": tau,
        "k": k,
        "num_rows": len(minimized_A),
        "covered": final_cover == all_combinations,
        "coverage_percentage": coverage_percentage,
        "time": total_time,
        "covering_array": minimized_A
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
