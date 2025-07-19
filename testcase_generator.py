import json
import random

test_cases = set()

while len(test_cases) < 10:  # 必要なケース数だけ生成
    tau = random.randint(2, 3)
    n = random.randint(2 * tau, 10)
    if n - tau < tau:
        continue  # k の範囲が成立しない場合スキップ
    k = random.randint(tau, n - tau)
    case = (n, tau, k)
    test_cases.add(case)  # setに追加することで重複を自動で排除

sorted_cases = sorted(list(test_cases), key=lambda x: (x[0], x[1], x[2]))

# 辞書にして保存
result = [{"n": n, "tau": tau, "k": k} for (n, tau, k) in sorted_cases]

with open('test_cases.json', 'w') as f:
    json.dump(result, f, indent=4)
