# run_experiment.py

import json
import subprocess
import sys
import os
import time

# --- Step 1: Ensure all required script files are present ---
required_files = ['adaptive_sampling.py', 'heuristic_greedy.py', 'simulated_annealing.py', 'testcase_generator.py']
for f in required_files:
    if not os.path.exists(f):
        print(f"Error: Required script '{f}' not found in the current directory.")
        sys.exit(1)

# --- Step 2: Import the main functions from your scripts ---
# This is a cleaner approach than using subprocess for everything,
# as it allows us to directly get the dictionary of results.
try:
    from adaptive_sampling import generate_LVCA_adaptive_sampling
    from heuristic_greedy import generate_binary_covering_array_heuristic_greedy
    from simulated_annealing import lv_cit_sa
except ImportError as e:
    print(f"Error: Could not import a function from as.py, hg.py, or sa.py.")
    print(f"Please ensure they are in the same directory and have no syntax errors.")
    print(f"Details: {e}")
    sys.exit(1)


def run_test_case_generator():
    """Executes the testcase_generator.py script."""
    print("Running test case generator...")
    try:
        subprocess.run([sys.executable, 'testcase_generator.py'], check=True, capture_output=True, text=True)
        print("Successfully generated 'test_cases.json'.")
    except subprocess.CalledProcessError as e:
        print(f"Error running testcase_generator.py: {e}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)

def load_test_cases():
    """Loads test cases from the generated JSON file."""
    try:
        with open('test_cases.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: 'test_cases.json' not found. Run the generator first.")
        return []
    except json.JSONDecodeError:
        print("Error: Could not decode 'test_cases.json'. It might be empty or corrupt.")
        return []

def main():
    """Main function to run the experiment."""
    # Generate the test cases first
    run_test_case_generator()
    test_cases = load_test_cases()

    if not test_cases:
        print("No test cases to run. Exiting.")
        return

    # A common seed for all algorithms for a fair comparison on a given test case
    common_seed = 42
    all_results = []

    print("\n--- Starting Experiment ---")

    for i, params in enumerate(test_cases):
        n, tau, k = params['n'], params['tau'], params['k']
        print(f"\n===== Test Case {i+1}/{len(test_cases)}: n={n}, tau={tau}, k={k} =====\n")

        case_results = {"params": params}

        # --- Run Adaptive Sampling (as.py) ---
        print("Running Adaptive Sampling...")
        as_result = generate_LVCA_adaptive_sampling(n, tau, k, seed=common_seed, verbose=False)
        case_results['as'] = {'rows': as_result['num_rows'], 'time': as_result['time']}
        print(f"  -> Done in {as_result['time']:.4f}s, Generated {as_result['num_rows']} rows.")

        # --- Run Heuristic Greedy (hg.py) ---
        print("Running Heuristic Greedy...")
        hg_result = generate_binary_covering_array_heuristic_greedy(n, tau, k, seed=common_seed, verbose=False)
        case_results['hg'] = {'rows': hg_result['num_rows'], 'time': hg_result['time']}
        print(f"  -> Done in {hg_result['time']:.4f}s, Generated {hg_result['num_rows']} rows.")

        # --- Run Simulated Annealing (sa.py) ---
        print("Running Simulated Annealing...")
        sa_result = lv_cit_sa(n, tau, k, seed=common_seed, verbose=False)
        case_results['sa'] = {'rows': sa_result['num_rows'], 'time': sa_result['time']}
        print(f"  -> Done in {sa_result['time']:.4f}s, Generated {sa_result['num_rows']} rows.")

        all_results.append(case_results)

    # --- Step 5: Print the final summary table ---
    print("\n\n--- Experiment Finished: Overall Results ---")
    print("-" * 75)
    header = f"| {'Test Case (n, tau, k)':<25} | {'Algorithm':<25} | {'Array Size':>12} | {'Time (s)':>10} |"
    print(header)
    print("-" * 75)

    for result in all_results:
        params_str = f"({result['params']['n']}, {result['params']['tau']}, {result['params']['k']})"

        #Adaptive Sampling
        as_res = result['adaptive_sampling']
        print(f"| {params_str:<25} | {'Adaptive Sampling (adaptive_sampling.py)':<25} | {as_res['rows']:>12} | {as_res['time']:>10.4f} |")

        # Heuristic Greedy
        hg_res = result['hg']
        print(f"| {'':<25} | {'Heuristic Greedy (heuristic_greedy.py)':<25} | {hg_res['rows']:>12} | {hg_res['time']:>10.4f} |")

        # Simulated Annealing
        sa_res = result['sa']
        print(f"| {'':<25} | {'Simulated Annealing (simulated_annealing.py)':<25} | {sa_res['rows']:>12} | {sa_res['time']:>10.4f} |")

        print("-" * 75)

if __name__ == '__main__':
    main()
