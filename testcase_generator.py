import json
import random

test_cases = set()

# while len(test_cases) < 50:  # 必要なケース数だけ生成
#     tau = random.randint(2, 4)
#     n = random.randint(2 * tau, 20)
#     if n - tau < tau:
#         continue  # k の範囲が成立しない場合スキップ
#     k = random.randint(tau, min(n//2 , n - tau))
#     case = (n, tau, k)
#     test_cases.add(case)  # setに追加することで重複を自動で排除

for n in range(10,40,10):
    for tau in range(2,5,1):
        for k in range(tau,tau+6,1):
            case = (n,tau,k)
            test_cases.add(case)

sorted_cases = sorted(list(test_cases), key=lambda x: (x[0], x[1], x[2]))

# 辞書にして保存
result = [{"n": n, "tau": tau, "k": k} for (n, tau, k) in sorted_cases]

with open('test_cases.json', 'w') as f:
    json.dump(result, f, indent=4)
