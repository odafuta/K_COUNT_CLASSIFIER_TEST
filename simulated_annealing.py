import itertools
import time
import random
import math
import sys
from typing import List, Set, Tuple, Dict, Any

# ----------------- 基本ユーティリティ ---------------------------------
LabelVec = List[int]  # 0/1 ベクトル長 n
LVCombo = Tuple[Tuple[int, ...], Tuple[int, ...]]  # (列 index 群, その値 0/1 群)

def all_tau_combos(n: int, tau: int) -> Set[LVCombo]:
    universe: Set[LVCombo] = set()
    for idxs in itertools.combinations(range(n), tau):
        for vals in itertools.product((0, 1), repeat=tau):
            if any(vals):
                universe.add((idxs, vals))
    return universe

def row_covers(row: LabelVec, tau: int) -> Set[LVCombo]:
    covered: Set[LVCombo] = set()
    for idxs in itertools.combinations(range(len(row)), tau):
        vals = tuple(row[i] for i in idxs)
        if any(vals):
            covered.add((idxs, vals))
    return covered

def random_row(n: int, k: int, rng: random.Random) -> LabelVec:
    assert 1 <= k <= n, "k は 0〜n の範囲で指定してください"
    ones = rng.sample(range(n), k)
    return [1 if i in ones else 0 for i in range(n)]

def generate_unique_rows(n: int, k: int, count: int, rng: random.Random) -> List[LabelVec]:
    max_possible_rows = math.comb(n, k)
    if count > max_possible_rows:
        count = max_possible_rows
    rows_set = set()
    while len(rows_set) < count:
        new_row = tuple(random_row(n, k, rng))
        rows_set.add(new_row)
    return [list(row) for row in rows_set]

def lower_bound(n: int, tau: int, k: int) -> int:
    total_combos = math.comb(n, tau) * (2**tau - 1)
    denom = sum(math.comb(n - i, tau - 1) for i in range(1, k, 1))
    return math.ceil(total_combos / denom)

# ----------------- 焼きなまし本体 --------------------------------------
def lv_cit_sa(
    n: int,
    tau: int,
    k: int,
    T0: float = 10.0,
    cooling: float = 0.995,
    seed: int = 0,
    verbose: bool = True
) -> Dict[str, Any]:
    start_time = time.perf_counter()
    rng = random.Random(seed)
    universe = all_tau_combos(n, tau)
    U_size = len(universe)
    lower_bound_value = lower_bound(n, tau, k)
    init_rows_count = lower_bound_value * (2**(tau - 1))
    recovery_steps = k * (n - k) * init_rows_count

    if verbose:
        print(f"n={n}, tau={tau}, k={k}")
        print(f"組み合わせ総数: {U_size}")
        print(f"理論的下界: {lower_bound_value}")
        print(f"初期解の行数: {init_rows_count}\n")

    curr_rows = generate_unique_rows(n, k, init_rows_count, rng)
    best_rows = []
    final_covered = set()
    covered_status = False
    reached_lower_bound = False

    try:
        while True:
            covered_set: Set[LVCombo] = set()
            for r in curr_rows:
                covered_set.update(row_covers(r, tau))
            is_fully_covered = (len(covered_set) == U_size)

            if not is_fully_covered:
                if verbose:
                    print(f"{len(curr_rows)}行でのカバー率が100%ではありません。{recovery_steps}ステップ以内で復帰を試みます...")

                T = T0
                recovered = False
                for _ in range(recovery_steps):
                    T *= cooling
                    if T < 1e-9: T = 1e-9

                    current_rows_set = {tuple(r) for r in curr_rows}
                    new_rows = None
                    while new_rows is None:
                        candidate_rows = [row[:] for row in curr_rows]
                        row_idx = rng.randrange(len(candidate_rows))
                        target_row = candidate_rows[row_idx]
                        one_indices = [i for i, v in enumerate(target_row) if v == 1]
                        zero_indices = [i for i, v in enumerate(target_row) if v == 0]
                        idx_to_one = rng.choice(zero_indices)
                        idx_to_zero = rng.choice(one_indices)
                        candidate_rows[row_idx][idx_to_one] = 1
                        candidate_rows[row_idx][idx_to_zero] = 0

                        if tuple(candidate_rows[row_idx]) not in current_rows_set:
                            new_rows = candidate_rows

                    new_covered_set: Set[LVCombo] = set()
                    for r in new_rows:
                        new_covered_set.update(row_covers(r, tau))

                    curr_score = U_size - len(covered_set)
                    new_score = U_size - len(new_covered_set)

                    if new_score < curr_score or rng.random() < math.exp((curr_score - new_score) / T):
                        curr_rows = new_rows
                        covered_set = new_covered_set

                    if len(covered_set) == U_size:
                        recovered = True
                        break

                if recovered:
                    is_fully_covered = True
                else:
                    if verbose:
                        print(f"{recovery_steps}回の試行でも100%被覆に復帰できませんでした。")
                    break

            if is_fully_covered:
                if verbose:
                    print(f"カバー率100%達成！ (行数: {len(curr_rows)})")

                best_rows = [r[:] for r in curr_rows]
                if len(best_rows) == lower_bound_value:
                    reached_lower_bound = True
                    if verbose:
                        print("理論的下界に到達したため、探索を終了します。")
                    break

                if verbose:
                    print("1行削減して、再度100%カバーを目指します...\n")
                curr_rows.pop(rng.randrange(len(curr_rows)))

    except Exception as e:
        if verbose:
            print(f"エラーが発生しました: {str(e)}")

    end_time = time.perf_counter()
    total_time = end_time - start_time

    if best_rows:
        final_covered = set()
        for r in best_rows:
            final_covered.update(row_covers(r, tau))
        covered_status = (len(final_covered) == U_size)
    else:
        best_rows = curr_rows
        if best_rows:
            final_covered = set()
            for r in best_rows:
                final_covered.update(row_covers(r, tau))
            covered_status = (len(final_covered) == U_size)

    return {
        "n": n,
        "tau": tau,
        "k": k,
        "num_rows": len(best_rows),
        "lower_bound": lower_bound_value,
        "reached_lower_bound": reached_lower_bound,
        "covered": covered_status,
        "coverage_percentage": len(final_covered) / U_size if U_size > 0 else 0.0,
        "time": total_time,
        "covering_array": best_rows
    }

# ----------------- コマンドライン実行用 ----------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python sa_algorithm_1.py n tau k [seed]")
        sys.exit(1)

    n = int(sys.argv[1])
    tau = int(sys.argv[2])
    k = int(sys.argv[3])
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 42

    result = lv_cit_sa(n, tau, k, seed=seed, verbose=True)

    print("\n最終結果:")
    print(f"パラメータ: n={n}, tau={tau}, k={k}")
    print(f"生成行数: {result['num_rows']}")
    print(f"理論的下界: {result['lower_bound']}")
    print(f"下界到達: {'はい' if result['reached_lower_bound'] else 'いいえ'}")
    print(f"カバー率: {result['coverage_percentage']:.2%}")
    print(f"実行時間: {result['time']:.4f}秒")

    if n <= 20 and result['num_rows'] <= 50:
        print("\nカバーリング配列:")
        for i, row in enumerate(result['covering_array'], 1):
            print(f"{i:3}: {row}")
