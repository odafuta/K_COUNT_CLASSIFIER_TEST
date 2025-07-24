# run_experiment.py

import json
import subprocess
import sys
import os
import time
# Imports added for the new run_with_timeout function
import pickle
import base64
import importlib


# --- New run_with_timeout function using subprocess ---
def run_with_timeout(timeout_seconds, func, *args, **kwargs):
    """
    Executes a function in a separate process with a timeout using subprocess.

    This method works by:
    1.  Defining a helper script as a string (`runner_script`).
    2.  Serializing the target function's module, name, and arguments using `pickle`.
    3.  Executing the helper script with `subprocess.run`, passing the serialized data
        via standard input.
    4.  The helper script deserializes the data, imports the module, runs the function,
        and prints the pickled result to its standard output.
    5.  The parent process reads the stdout and deserializes the result.
    6.  `subprocess.run`'s `timeout` argument handles killing the process if it
        exceeds the time limit.
    """
    runner_script = """
import sys
import pickle
import base64
import importlib

try:
    # Read base64-encoded pickled data from stdin
    encoded_data = sys.stdin.buffer.read()
    pickled_data = base64.b64decode(encoded_data)
    module_name, func_name, f_args, f_kwargs = pickle.loads(pickled_data)

    # Import the module and get the function
    module = importlib.import_module(module_name)
    target_func = getattr(module, func_name)

    # Run the function and get the result
    result = target_func(*f_args, **f_kwargs)

    # Pickle the result and write it to stdout as bytes
    pickled_result = pickle.dumps(result)
    sys.stdout.buffer.write(pickled_result)
    sys.stdout.flush()

except Exception as e:
    # If anything goes wrong, write the error to stderr and exit
    print(f"Subprocess error: {e}", file=sys.stderr)
    sys.exit(1)
"""

    # Serialize the function's identity and its arguments
    # func.__module__ gets the original module name (e.g., 'adaptive_sampling')
    # func.__name__ gets the function name (e.g., 'generate_LVCA_adaptive_sampling')
    data_to_pass = (func.__module__, func.__name__, args, kwargs)
    pickled_data = pickle.dumps(data_to_pass)
    encoded_data = base64.b64encode(pickled_data)

    try:
        # Execute the runner script in a new Python process
        proc = subprocess.run(
            [sys.executable, "-c", runner_script],
            input=encoded_data,
            capture_output=True,
            timeout=timeout_seconds,
        )
        proc.check_returncode() # Raise an exception if the subprocess returned an error
        
        # If successful, deserialize the result from stdout
        result = pickle.loads(proc.stdout)
        return result, False # Return result, no timeout

    except subprocess.TimeoutExpired:
        print(f"  -> タイムアウト：{timeout_seconds}秒以内に終了しませんでした。")
        return None, True # Return nothing, timeout occurred
    
    except subprocess.CalledProcessError as e:
        # The subprocess exited with an error. Print its stderr for debugging.
        print(f"  -> Subprocess failed. Error: {e.stderr.decode()}")
        return None, True # Return nothing, an error occurred

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
    timeout_seconds = 600

    print("\n--- Starting Experiment ---")

    for i, params in enumerate(test_cases):
        n, tau, k = params['n'], params['tau'], params['k']
        print(f"\n===== Test Case {i+1}/{len(test_cases)}: n={n}, tau={tau}, k={k} =====\n")

        case_results = {"params": params}

        # --- Adaptive Sampling ---
        print("Running Adaptive Sampling...")
        as_result, as_timeout = run_with_timeout(
            timeout_seconds, generate_LVCA_adaptive_sampling,
            n, tau, k, seed=common_seed, verbose=False
        )
        if as_timeout or as_result is None:
            case_results['as'] = {'rows': 'TIMEOUT', 'time': float('inf')}
        else:
            case_results['as'] = {'rows': as_result['num_rows'], 'time': as_result['time']}
            print(f"  -> Done in {as_result['time']:.4f}s, Generated {as_result['num_rows']} rows.")

        # --- Heuristic Greedy ---
        print("Running Heuristic Greedy...")
        hg_result, hg_timeout = run_with_timeout(
            timeout_seconds, generate_binary_covering_array_heuristic_greedy,
            n, tau, k, seed=common_seed, verbose=False
        )
        if hg_timeout or hg_result is None:
            case_results['hg'] = {'rows': 'TIMEOUT', 'time': float('inf')}
        else:
            case_results['hg'] = {'rows': hg_result['num_rows'], 'time': hg_result['time']}
            print(f"  -> Done in {hg_result['time']:.4f}s, Generated {hg_result['num_rows']} rows.")

        # --- Simulated Annealing ---
        print("Running Simulated Annealing...")
        sa_result, sa_timeout = run_with_timeout(
            timeout_seconds, lv_cit_sa,
            n, tau, k, seed=common_seed, verbose=False
        )
        if sa_timeout or sa_result is None:
            case_results['sa'] = {'rows': 'TIMEOUT', 'time': float('inf')}
        else:
            case_results['sa'] = {'rows': sa_result['num_rows'], 'time': sa_result['time']}
            print(f"  -> Done in {sa_result['time']:.4f}s, Generated {sa_result['num_rows']} rows.")

        all_results.append(case_results)

    # --- Step 5: Print the final summary table ---
    line = "-" * 105
    print("\n\n--- Experiment Finished: Overall Results ---")
    print(line)
    header = f"| {'Test Case (n, tau, k)':<25} | {'Algorithm':<45} | {'Array Size':>12} | {'Time (s)':>10} |"
    print(header)
    print(line)


    with open("result_summary.csv", "w") as f:

        f.write(f"{'(n,tau,k)':<10} {'Algorithm':<25} {'Array_Size':>12} {'Time(s)':>10}\n")

        for result in all_results:
            params_str = f"({result['params']['n']}, {result['params']['tau']}, {result['params']['k']})"

            #Adaptive Sampling
            as_res = result['as']
            print(f"| {params_str:<25} | {'Adaptive Sampling (adaptive_sampling.py)':<45} | {as_res['rows']:>12} | {as_res['time']:>10.4f} |")
            f.write(f"{params_str:<10} {'Adaptive_Sampling':<25} {as_res['rows']:>12} {as_res['time']:>10.4f}\n")

            # Heuristic Greedy
            hg_res = result['hg']
            print(f"| {'':<25} | {'Heuristic Greedy (heuristic_greedy.py)':<45} | {hg_res['rows']:>12} | {hg_res['time']:>10.4f} |")
            f.write(f"{' ':<10} {'Heuristic_Greedy':<25} {hg_res['rows']:>12} {hg_res['time']:>10.4f}\n")

            # Simulated Annealing
            sa_res = result['sa']
            print(f"| {'':<25} | {'Simulated Annealing (simulated_annealing.py)':<45} | {sa_res['rows']:>12} | {sa_res['time']:>10.4f} |")
            f.write(f"{' ':<10} {'Simulated_Annealing':<25} {sa_res['rows']:>12} {sa_res['time']:>10.4f}\n")

            print(line)

if __name__ == '__main__':
    main()
