import itertools
import time
import random
import math
import sys
from typing import List, Set, Tuple, Dict, Any
from collections import Counter  # ★変更: カバー多重度を差分管理するためにCounterを導入

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

# ★変更: tau の列組を事前計算して使い回す（高速化）
def row_covers_precomp(row: LabelVec, tau_index_combos: List[Tuple[int, ...]]) -> Set[LVCombo]:
    covered: Set[LVCombo] = set()
    for idxs in tau_index_combos:
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
    if tau > k:
        raise ValueError("tau は k 以下でなければなりません")
    return math.ceil(math.comb(n, tau) / math.comb(k, tau))

# ★変更: rows 全体の被覆を「キャッシュ＋Counter」で構築するヘルパ
def _compute_cache_and_counter(rows: List[LabelVec], tau_index_combos: List[Tuple[int, ...]]):
    row_cov_cache: List[Set[LVCombo]] = []
    cover_counter: Counter = Counter()
    for r in rows:
        rc = row_covers_precomp(r, tau_index_combos)
        row_cov_cache.append(rc)
        cover_counter.update(rc)
    return row_cov_cache, cover_counter

# ----------------- 焼きなまし本体（純粋SA） --------------------------------------
def lv_cit_sa(
    n: int,
    tau: int,
    k: int,
    T0: float = 10.0,
    cooling: float = 0.995,
    seed: int = 0,
    verbose: bool = True
) -> Dict[str, Any]:
    # ★変更: LVCA の制約チェック
    if not (tau <= k <= n-tau+1):
        raise ValueError(f"L の制約を満たしません: tau={tau} <= k={k} <= n-tau+1={n-tau+1}")
    

    start_time = time.perf_counter()
    rng = random.Random(seed)

    universe = all_tau_combos(n, tau)
    U_size = len(universe)

    lower_bound_value = lower_bound(n, tau, k)

    # ★変更: 初期解が小さすぎるときは厚めに生成する
    init_rows_count = max(int(lower_bound_value * 1.2), lower_bound_value + 100)
    
    max_possible_rows = math.comb(n, k)
    if init_rows_count > max_possible_rows:
        if verbose:
            print(f"警告: 初期解の行数({init_rows_count})が最大可能行数({max_possible_rows})を超えています。")
            print(f"最大可能行数({max_possible_rows})に調整します。")
        init_rows_count = max_possible_rows
    
    # ★変更: 試行回数は上限付きで十分大きく確保（速度と復帰力のバランス）
    recovery_steps = min(
        max(20000, 100 * init_rows_count),
        120_000
    )

    # ★変更: tau列組の事前計算（各行の被覆計算を高速化）
    tau_index_combos: List[Tuple[int, ...]] = list(itertools.combinations(range(n), tau))

    if verbose:
        print(f"n={n}, tau={tau}, k={k}")
        print(f"組み合わせ総数: {U_size}")
        print(f"理論的下界: {lower_bound_value}")
        print(f"初期解の行数: {init_rows_count}\n")

    curr_rows = generate_unique_rows(n, k, init_rows_count, rng)
    best_rows: List[LabelVec] = []
    final_covered: Set[LVCombo] = set()
    covered_status = False
    reached_lower_bound = False

    try:
        while True:
            # ★変更: 被覆は差分更新可能な構造で保持（rowごとの被覆キャッシュ＋多重度Counter）
            row_cov_cache, cover_counter = _compute_cache_and_counter(curr_rows, tau_index_combos)
            covered_size = len(cover_counter)
            is_fully_covered = (covered_size == U_size)

            if not is_fully_covered:
                if verbose:
                    print(f"{len(curr_rows)}行でのカバー率が100%ではありません。{recovery_steps}ステップ以内で復帰を試みます...")

                T = T0
                recovered = False

                # ★変更: 現在の行集合（重複防止）を一度作って受理時のみ更新
                current_rows_set = {tuple(r) for r in curr_rows}

                for step in range(1, recovery_steps + 1):
                    if step % 1000 == 0 and verbose:  # ★変更: 進捗ログ
                        print(step)
                        print(f"covered_size: {covered_size}")
                        print(f"U_size: {U_size}")

                    T *= cooling
                    if T < 1e-5:  # ★変更: 完全凍結を避ける温度下限
                        T = 1e-5

                    # 1 行だけ 1↔0 を入れ替えて候補を作る（k 本の1は維持）
                    row_idx = rng.randrange(len(curr_rows))
                    target_row = curr_rows[row_idx]
                    one_indices = [i for i, v in enumerate(target_row) if v == 1]
                    zero_indices = [i for i, v in enumerate(target_row) if v == 0]
                    if not one_indices or not zero_indices:
                        continue

                    idx_to_one = rng.choice(zero_indices)
                    idx_to_zero = rng.choice(one_indices)
                    candidate_row = target_row[:]
                    candidate_row[idx_to_one] = 1
                    candidate_row[idx_to_zero] = 0

                    if tuple(candidate_row) in current_rows_set:
                        continue

                    # ★変更: 差分評価（この1行が置き換わることによる lost/gained）
                    old_cov = row_cov_cache[row_idx]
                    candidate_cov = row_covers_precomp(candidate_row, tau_index_combos)

                    curr_score = U_size - covered_size

                    lost = 0
                    for combo in old_cov:
                        if cover_counter[combo] == 1 and combo not in candidate_cov:
                            lost += 1

                    gained = 0
                    for combo in candidate_cov:
                        if cover_counter.get(combo, 0) == 0 and combo not in old_cov:
                            gained += 1

                    new_covered_size = covered_size - lost + gained
                    new_score = U_size - new_covered_size

                    # 受理判定（純粋SA）
                    if new_score < curr_score or rng.random() < math.exp((curr_score - new_score) / T):
                        # ★変更: 受理時のみ本体を更新（集合・カウンタ・キャッシュを差分更新）
                        current_rows_set.remove(tuple(target_row))
                        current_rows_set.add(tuple(candidate_row))
                        curr_rows[row_idx] = candidate_row

                        for combo in old_cov:
                            cover_counter[combo] -= 1
                            if cover_counter[combo] == 0:
                                del cover_counter[combo]
                        for combo in candidate_cov:
                            cover_counter[combo] += 1

                        row_cov_cache[row_idx] = candidate_cov
                        covered_size = new_covered_size

                        if covered_size == U_size:
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
                # ★変更: 改善前と同じくランダムに1行削除（貪欲法は導入しない）
                curr_rows.pop(rng.randrange(len(curr_rows)))

    except Exception as e:
        if verbose:
            print(f"エラーが発生しました: {str(e)}")

    end_time = time.perf_counter()
    total_time = end_time - start_time

    # 結果の最終確認
    try:
        if best_rows:
            final_covered = set()
            for r in best_rows:
                final_covered.update(row_covers_precomp(r, tau_index_combos))
            covered_status = (len(final_covered) == U_size)
        else:
            final_covered = set()
            for r in curr_rows:
                final_covered.update(row_covers_precomp(r, tau_index_combos))
            covered_status = (len(final_covered) == U_size)
            if covered_status:
                best_rows = [r[:] for r in curr_rows]
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

    print(f"len(final_covered): {len(final_covered)}")
    print(f"U_size: {U_size}")
    
    return {
        "n": n,
        "tau": tau,
        "k": k,
        "num_rows": len(best_rows) if covered_status else None,
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
    
    if result['num_rows'] is not None and result['num_rows'] < 1000:
        print("\nカバーリング配列:")
        for i, row in enumerate(result['covering_array'], 1):
            print(f"{i:3}: {row}")
