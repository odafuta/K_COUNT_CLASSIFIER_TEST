import re
import pandas as pd
import matplotlib.pyplot as plt
import os

def draw_figure(data_dict, field, n, tau, dir):
    """
    3つのアルゴリズムの結果を1つのグラフにプロット
    data_dict: {algorithm_name: (k_list, value_list)}
    """
    plt.figure(figsize=(10, 6))
    plt.title(f"Algorithm Comparison (n={n}, tau={tau})")
    
    # 各アルゴリズムのデータをプロット
    colors = ['blue', 'red', 'green']
    markers = ['o', 's', '^']
    
    for i, (algo_name, (k_list, value_list)) in enumerate(data_dict.items()):
        if k_list and value_list:  # データが存在する場合のみプロット
            plt.plot(k_list, value_list, 
                    linestyle='solid', 
                    marker=markers[i], 
                    color=colors[i],
                    label=algo_name,
                    linewidth=2,
                    markersize=6)
    
    plt.xlabel('k')
    if field == "array_size":
        plt.ylabel('Array Size')
    elif field == "time":
        plt.ylabel('Runtime (seconds)')
    
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # ファイル名を修正
    output_name = f"comparison_{field}_{n}_{tau}.png"
    output_path = os.path.join(dir, output_name)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()  # メモリリークを防ぐ
    print(f"{output_name}に出力しました。")

input_file = "result_summary.csv"
output_file = "output.csv"

# 結果を格納するリスト（ヘッダー行）
output_lines = []
output_lines.append("n,tau,k,Algorithm,Array_Size,Time")

# 直前の (n,tau,k) を保持する変数
prev_n = prev_tau = prev_k = None

with open(input_file, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        # ヘッダー行の処理
        if line.startswith("(n,tau,k)"):
            continue  # ヘッダーは上書きするので読み飛ばす

        # (n,tau,k)の部分を正規表現で抽出
        m = re.match(r"\((\d+),\s*(\d+),\s*(\d+)\)\s*(.*)", line)
        if m:
            # (n,tau,k) がある行
            n, tau, k = m.group(1), m.group(2), m.group(3)
            rest = m.group(4)
            prev_n, prev_tau, prev_k = n, tau, k
        else:
            # (n,tau,k)がない行は直前の値を使う
            n, tau, k = prev_n, prev_tau, prev_k
            rest = line

        # rest は空白区切りで Algorithm, Array_Size, Time があるのでそれぞれ抽出
        # 連続空白で分割
        parts = re.split(r"\s{2,}", rest)
        # parts は ['Algorithm名', 'Array_Size', 'Time']のはず
        if len(parts) < 3:
            # Timeに空白などある場合を考慮し、無理やり後ろから詰める
            parts = re.split(r"\s+", rest)
            # parts[-2], parts[-1]がArray_Size, Timeとして最低限確保
            if len(parts) >= 3:
                algo = " ".join(parts[:-2])
                array_size = parts[-2]
                time_val = parts[-1]
            else:
                # 形式崩れた行はスキップか適宜処理
                continue
        else:
            algo, array_size, time_val = parts[0], parts[1], parts[2]

        # 行として連結
        out_line = f"{n},{tau},{k},{algo},{array_size},{time_val}"
        output_lines.append(out_line)

field = ["array_size", "time"]

# ディレクトリ構造を比較用に変更
for f in field:
    make_dir_path = './fig/' + f
    
    #作成しようとしているディレクトリが存在するかどうかを判定する
    if os.path.isdir(make_dir_path):
        #既にディレクトリが存在する場合は何もしない
        pass
    else:
        #ディレクトリが存在しない場合のみ作成する
        os.makedirs(make_dir_path)

# ファイル書き込み
with open(output_file, "w", encoding="utf-8") as f_out:
    f_out.write("\n".join(output_lines))

input_csv = pd.read_csv('./output.csv')
n = input_csv[input_csv.keys()[0]]
tau = input_csv[input_csv.keys()[1]]
k = input_csv[input_csv.keys()[2]]
algo = input_csv[input_csv.keys()[3]]
array_size = input_csv[input_csv.keys()[4]]
time = input_csv[input_csv.keys()[5]]

prev_n = int(n[0])
prev_tau = int(tau[0])

# データ構造を辞書形式に変更
current_data = {
    "array_size": {
        "Adaptive_Sampling": ([], []),
        "Heuristic_Greedy": ([], []),
        "Simulated_Annealing": ([], [])
    },
    "time": {
        "Adaptive_Sampling": ([], []),
        "Heuristic_Greedy": ([], []),
        "Simulated_Annealing": ([], [])
    }
}

for i in range(0, n.size, 1):
    if (prev_n != int(n[i]) or prev_tau != int(tau[i])) or (i == n.size-1):
        # グラフを生成
        for f in field:
            dir = './fig/' + f
            draw_figure(current_data[f], f, prev_n, prev_tau, dir)
        
        # 新しいn, tauの値を設定
        if i < n.size:
            prev_n = int(n[i])
            prev_tau = int(tau[i])
        
        # データをクリア
        for f in field:
            for algo_name in current_data[f]:
                current_data[f][algo_name] = ([], [])

    # データを追加（TIMEOUTでない場合のみ）
    if array_size[i] not in ["TIMEOUT", "NOT_COVERED"]:
        algo_name = algo[i]
        if algo_name in current_data["array_size"]:
            current_data["array_size"][algo_name][0].append(int(k[i]))
            current_data["array_size"][algo_name][1].append(int(array_size[i]))
            current_data["time"][algo_name][0].append(int(k[i]))
            current_data["time"][algo_name][1].append(float(time[i]))