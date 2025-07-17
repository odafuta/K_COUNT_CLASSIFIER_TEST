import json
import random

test_cases = []
for _ in range(10):
    tau = random.randint(2, 4)
    n = random.randint(2 * tau, 10)
    k = random.randint(tau, n - tau)
    test_cases.append({"n": n, "tau": tau, "k": k})

with open('test_cases.json', 'w') as f:
    json.dump(test_cases, f, indent=4)
