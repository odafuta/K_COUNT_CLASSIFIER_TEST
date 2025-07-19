import json
import random

test_cases = []
for _ in range(2):
    tau = random.randint(2, 3)
    n = random.randint(2 * tau, 8)
    k = random.randint(tau, n - tau)
    test_cases.append({"n": n, "tau": tau, "k": k})

with open('test_cases.json', 'w') as f:
    json.dump(test_cases, f, indent=4)
