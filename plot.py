import re
import pandas as pd
import matplotlib.pyplot as plt
import os

def draw_figure(k,array_or_time,algorithm,dir):
    plt.figure()
    plt.title(f"{algorithm} n={prev_n} tau={prev_tau}")
    plt.plot(k, array_or_time, linestyle='solid', marker='o')
    plt.grid(True)
    output_name = f"{algorithm}_{prev_n}_{prev_tau}.png"
    output_path = os.path.join(dir, output_name)

    plt.savefig(output_path)
    print(output_name + "に出力しました。")
    array_or_time.clear()

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
algorithm = ["Adaptive_Sampling", "Heuristic_Greedy", "Simulated_Annealing"
             ]

for f in field:
    for a in algorithm:
        make_dir_path = './fig/' + f + '/' + a

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
as_k = []
hg_k = []
sa_k = []
as_array = []
hg_array = []
sa_array = []
as_time = []
hg_time = []
sa_time = []
result_array = [("Adaptive_Sampling",as_k,as_array), ("Heuristic_Greedy",hg_k,hg_array), ("Simulated_Annealing",sa_k,sa_array)]
result_time = [("Adaptive_Sampling",as_k,as_time), ("Heuristic_Greedy",hg_k,hg_time), ("Simulated_Annealing",sa_k,sa_time)]
for i in range(0, n.size, 1):
    if (prev_tau != int(tau[i])) or (i == n.size-1):
        for f in field:
            if f == "array_size":
                result = result_array
            elif f == "time":
                result = result_time
            for algo_r, k_r, array_or_time in result:
                dir = './fig/' + f + '/' + algo_r
                draw_figure(k_r,array_or_time,algo_r,dir)
        prev_n = int(n[i])
        prev_tau = int(tau[i])
        for algo_r, k_r, array_or_time in result_array:
            k_r.clear()

    if array_size[i] != "TIMEOUT":
        if algo[i] == "Adaptive_Sampling":
            as_k.append(int(k[i]))
            as_array.append(int(array_size[i]))
            as_time.append(float(time[i]))
        elif algo[i] == "Heuristic_Greedy":
            hg_k.append(int(k[i]))
            hg_array.append(int(array_size[i]))
            hg_time.append(float(time[i]))
        elif algo[i] == "Simulated_Annealing":
            sa_k.append(int(k[i]))
            sa_array.append(int(array_size[i]))
            sa_time.append(float(time[i]))