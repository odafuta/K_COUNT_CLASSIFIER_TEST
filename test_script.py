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
import argparse
import platform
import signal


# --- New run_with_timeout function using subprocess ---
def run_with_timeout(run_timeout_seconds, func, *args, **kwargs):
    """
    Executes a function in a separate process with a timeout using subprocess.

    This method works by:
    1.  Defining a helper script as a string (`runner_script`).
    2.  Serializing the target function's module, name, and arguments using `pickle`.
    3.  Executing the helper script with a child Python process.
    4.  The helper script deserializes the data, imports the module, runs the function,
        and prints the pickled result to its standard output.
    5.  The parent process reads the stdout and deserializes the result.
    6.  If `run_timeout_seconds` is set (> 0), the parent enforces it and kills the child
        (and its descendants where possible) on timeout.
    If `run_timeout_seconds` is None or <= 0, no timeout is enforced.
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
        # Start the runner script in a new Python process
        proc = subprocess.Popen(
            [sys.executable, "-c", runner_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True  # New process group on POSIX
        )

        # Communicate with optional timeout
        if run_timeout_seconds and run_timeout_seconds > 0:
            stdout_data, stderr_data = proc.communicate(input=encoded_data, timeout=run_timeout_seconds)
        else:
            stdout_data, stderr_data = proc.communicate(input=encoded_data)

        # Raise if the subprocess returned an error
        if proc.returncode != 0:
            # Bubble up child error text
            err_text = stderr_data.decode(errors='ignore') if stderr_data else ''
            raise subprocess.CalledProcessError(proc.returncode, proc.args, output=stdout_data, stderr=err_text.encode())

        # If successful, deserialize the result from stdout
        result = pickle.loads(stdout_data)
        return result, False  # Return result, no timeout

    except subprocess.TimeoutExpired:
        # Kill the entire process tree if possible
        try:
            if platform.system().lower().startswith('win'):
                # Use taskkill to terminate the process tree on Windows
                subprocess.run(f"taskkill /PID {proc.pid} /T /F", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # POSIX: kill the whole process group created by start_new_session
                try:
                    pgid = os.getpgid(proc.pid)
                    os.killpg(pgid, signal.SIGKILL)
                except Exception:
                    proc.kill()
        except Exception:
            pass
        print(f"  -> タイムアウト：{run_timeout_seconds}秒以内に終了しませんでした。")
        return None, True  # Return nothing, timeout occurred
    
    except subprocess.CalledProcessError as e:
        # The subprocess exited with an error. Print its stderr for debugging.
        err_msg = e.stderr.decode() if isinstance(e.stderr, (bytes, bytearray)) else str(e.stderr)
        print(f"  -> Subprocess failed. Error: {err_msg}")
        return None, True  # Return nothing, an error occurred

# --- Step 1: Ensure all required script files are present ---
required_files = ['adaptive_sampling.py', 'heuristic_greedy.py', 'simulated_annealing.py', 'acts_runner.py', 'testcase_generator.py']
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
    from acts_runner import run_acts_covering_array
except ImportError as e:
    print(f"Error: Could not import a function from the required modules.")
    print(f"Please ensure they are in the same directory and have no syntax errors.")
    print(f"Details: {e}")
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Run covering array experiments with timeouts.")
    parser.add_argument("--timeout-seconds", type=int, default=600, help="Global timeout in seconds (default: 600). Use 0 or negative to disable.")
    parser.add_argument("--timeout-as", type=int, default=None, help="Adaptive Sampling timeout in seconds (overrides global). 0 or negative to disable.")
    parser.add_argument("--timeout-hg", type=int, default=None, help="Heuristic Greedy timeout in seconds (overrides global). 0 or negative to disable.")
    parser.add_argument("--timeout-sa", type=int, default=None, help="Simulated Annealing timeout in seconds (overrides global). 0 or negative to disable.")
    parser.add_argument("--timeout-acts", type=int, default=None, help="ACTS timeout in seconds (overrides global). 0 or negative to disable.")
    parser.add_argument("--no-timeout", action="store_true", help="Disable timeout for all algorithms (overrides all timeout options).")
    parser.add_argument("--results-csv", default="result_summary.csv", help="Path to results CSV (appended per test case).")
    parser.add_argument("--checkpoint", default="results_checkpoint.json", help="Path to checkpoint JSON (saved after each test case).")
    parser.add_argument("--skip-as", action="store_true", help="Skip Adaptive Sampling algorithm.")
    parser.add_argument("--skip-hg", action="store_true", help="Skip Heuristic Greedy algorithm.")
    parser.add_argument("--skip-sa", action="store_true", help="Skip Simulated Annealing algorithm.")
    parser.add_argument("--skip-acts", action="store_true", help="Skip ACTS algorithm.")
    return parser.parse_args()


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


def load_checkpoint(checkpoint_path):
    """Load previously saved results from a checkpoint JSON file."""
    if os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"Warning: Could not load checkpoint '{checkpoint_path}': {e}. Starting fresh.")
    return []


def save_checkpoint(checkpoint_path, all_results):
    """Atomically save results to a checkpoint JSON file."""
    tmp_path = checkpoint_path + ".tmp"
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, checkpoint_path)
    except Exception as e:
        print(f"Warning: Failed to save checkpoint '{checkpoint_path}': {e}")


def completed_param_set(all_results):
    """Return a set of (n, tau, k) tuples that have already been completed."""
    done = set()
    for r in all_results:
        try:
            params = r.get('params', {})
            done.add((params['n'], params['tau'], params['k']))
        except Exception:
            continue
    return done


def append_case_to_csv(csv_path, case_results):
    """Append a single test case result to the CSV, writing a header if the file doesn't exist."""
    file_exists = os.path.exists(csv_path)
    params_str = f"({case_results['params']['n']}, {case_results['params']['tau']}, {case_results['params']['k']})"
    with open(csv_path, 'a', encoding='utf-8') as f:
        if not file_exists:
            f.write(f"{('(n,tau,k)'):<10} {'Algorithm':<25} {'Array_Size':>12} {'Time(s)':>10}\n")
        as_res = case_results['as']
        time_str = f"{as_res['time']:>10.4f}" if as_res['time'] is not None else "      N/A"
        f.write(f"{params_str:<10} {'Adaptive_Sampling':<25} {as_res['rows']:>12} {time_str}\n")
        hg_res = case_results['hg']
        time_str = f"{hg_res['time']:>10.4f}" if hg_res['time'] is not None else "      N/A"
        f.write(f"{' ':<10} {'Heuristic_Greedy':<25} {hg_res['rows']:>12} {time_str}\n")
        sa_res = case_results['sa']
        time_str = f"{sa_res['time']:>10.4f}" if sa_res['time'] is not None else "      N/A"
        f.write(f"{' ':<10} {'Simulated_Annealing':<25} {sa_res['rows']:>12} {time_str}\n")
        acts_res = case_results['acts']
        time_str = f"{acts_res['time']:>10.4f}" if acts_res['time'] is not None else "      N/A"
        f.write(f"{' ':<10} {'ACTS':<25} {acts_res['rows']:>12} {time_str}\n")


def main():
    """Main function to run the experiment."""
    args = parse_args()

    # Resolve effective timeouts per algorithm
    if args.no_timeout:
        timeout_global = 0
        timeout_as = 0
        timeout_hg = 0
        timeout_sa = 0
        timeout_acts = 0
    else:
        timeout_global = args.timeout_seconds
        timeout_as = args.timeout_as if args.timeout_as is not None else timeout_global
        timeout_hg = args.timeout_hg if args.timeout_hg is not None else timeout_global
        timeout_sa = args.timeout_sa if args.timeout_sa is not None else timeout_global
        timeout_acts = args.timeout_acts if args.timeout_acts is not None else timeout_global

    # Generate the test cases first
    run_test_case_generator()
    test_cases = load_test_cases()

    if not test_cases:
        print("No test cases to run. Exiting.")
        return

    # A common seed for all algorithms for a fair comparison on a given test case
    common_seed = 42
    # Load previous progress if any
    all_results = load_checkpoint(args.checkpoint)
    already_done = completed_param_set(all_results)
    if already_done:
        print(f"Resuming: {len(already_done)} test case(s) already completed and will be skipped.")

    acts_failed_globally = False

    print("\n--- Starting Experiment ---")

    # Display which algorithms are being skipped
    skipped_algorithms = []
    if args.skip_as:
        skipped_algorithms.append("Adaptive Sampling")
    if args.skip_hg:
        skipped_algorithms.append("Heuristic Greedy")
    if args.skip_sa:
        skipped_algorithms.append("Simulated Annealing")
    if args.skip_acts:
        skipped_algorithms.append("ACTS")
    
    if skipped_algorithms:
        print(f"Skipping algorithms: {', '.join(skipped_algorithms)}")
    else:
        print("Running all algorithms.")

    for i, params in enumerate(test_cases):
        n, tau, k = params['n'], params['tau'], params['k']
        if (n, tau, k) in already_done:
            print(f"\n===== Test Case {i+1}/{len(test_cases)}: n={n}, tau={tau}, k={k} =====")
            print("Skipping (already completed).")
            continue

        print(f"\n===== Test Case {i+1}/{len(test_cases)}: n={n}, tau={tau}, k={k} =====\n")

        case_results = {"params": params}

        # --- Adaptive Sampling ---
        if not args.skip_as:
            print("Running Adaptive Sampling...")
            as_result, as_timeout = run_with_timeout(
                timeout_as, generate_LVCA_adaptive_sampling,
                n, tau, k, seed=common_seed, verbose=False
            )
            if as_timeout or as_result is None:
                case_results['as'] = {'rows': 'TIMEOUT', 'time': float('inf')}
            else:
                case_results['as'] = {'rows': as_result['num_rows'], 'time': as_result['time']}
                print(f"  -> Done in {as_result['time']:.4f}s, Generated {as_result['num_rows']} rows.")
        else:
            case_results['as'] = {'rows': 'SKIPPED', 'time': None}
            print("  -> Adaptive Sampling skipped.")

        # --- Heuristic Greedy ---
        if not args.skip_hg:
            print("Running Heuristic Greedy...")
            hg_result, hg_timeout = run_with_timeout(
                timeout_hg, generate_binary_covering_array_heuristic_greedy,
                n, tau, k, seed=common_seed, verbose=False
            )
            if hg_timeout or hg_result is None:
                case_results['hg'] = {'rows': 'TIMEOUT', 'time': float('inf')}
            else:
                case_results['hg'] = {'rows': hg_result['num_rows'], 'time': hg_result['time']}
                print(f"  -> Done in {hg_result['time']:.4f}s, Generated {hg_result['num_rows']} rows.")
        else:
            case_results['hg'] = {'rows': 'SKIPPED', 'time': None}
            print("  -> Heuristic Greedy skipped.")

        # --- Simulated Annealing ---
        if not args.skip_sa:
            print("Running Simulated Annealing...")
            sa_result, sa_timeout = run_with_timeout(
                timeout_sa, lv_cit_sa,
                n, tau, k, seed=common_seed, verbose=False
            )
            if sa_timeout or sa_result is None:
                case_results['sa'] = {'rows': 'TIMEOUT', 'time': float('inf')}
            else:
                if sa_result.get('covered', False):
                    case_results['sa'] = {'rows': sa_result['num_rows'], 'time': sa_result['time']}
                else:
                    case_results['sa'] = {'rows': 'NOT_COVERED', 'time': sa_result['time']}
                print(f"  -> Done in {sa_result['time']:.4f}s, Generated {sa_result['num_rows']} rows.")
        else:
            case_results['sa'] = {'rows': 'SKIPPED', 'time': None}
            print("  -> Simulated Annealing skipped.")

        # --- ACTS ---
        if not args.skip_acts:
            print("Running ACTS...")
            if acts_failed_globally:
                case_results['acts'] = {'rows': 'ERROR', 'time': float('inf')}
                print("  -> ACTS Error: Skipped due to previous error in this run.")
            else:
                acts_result, acts_timeout = run_with_timeout(
                    timeout_acts, run_acts_covering_array,
                    n, tau, k, seed=common_seed, verbose=False, timeout_seconds=(None if timeout_acts and timeout_acts <= 0 else timeout_acts)
                )
                if acts_timeout or acts_result is None:
                    case_results['acts'] = {'rows': 'TIMEOUT', 'time': float('inf')}
                else:
                    if acts_result.get('error'):
                        # ACTS failed with an error (e.g., Java not available)
                        acts_failed_globally = True
                        case_results['acts'] = {'rows': 'ERROR', 'time': acts_result['time']}
                        print(f"  -> ACTS Error: {acts_result['error']}")
                        print("  -> ACTS will be skipped for remaining test cases in this run.")
                    elif acts_result.get('covered', False):
                        case_results['acts'] = {'rows': acts_result['num_rows'], 'time': acts_result['time']}
                        print(f"  -> Done in {acts_result['time']:.4f}s, Generated {acts_result['num_rows']} rows.")
                    else:
                        case_results['acts'] = {'rows': 'NOT_COVERED', 'time': acts_result['time']}
                        print(f"  -> Done in {acts_result['time']:.4f}s, Generated {acts_result['num_rows']} rows.")
        else:
            case_results['acts'] = {'rows': 'SKIPPED', 'time': None}
            print("  -> ACTS skipped.")

        # Save progress incrementally
        all_results.append(case_results)
        save_checkpoint(args.checkpoint, all_results)
        append_case_to_csv(args.results_csv, case_results)

    # --- Final: Print the final summary table (console only) ---
    line = "-" * 120
    print("\n\n--- Experiment Finished: Overall Results ---")
    print(line)
    header = f"| {'Test Case (n, tau, k)':<25} | {'Algorithm':<45} | {'Array Size':>12} | {'Time (s)':>10} |"
    print(header)
    print(line)


    for result in all_results:
        params_str = f"({result['params']['n']}, {result['params']['tau']}, {result['params']['k']})"
        as_res = result['as']
        time_str = f"{as_res['time']:>10.4f}" if as_res['time'] is not None else "      N/A"
        print(f"| {params_str:<25} | {'Adaptive Sampling (adaptive_sampling.py)':<45} | {as_res['rows']:>12} | {time_str} |")
        hg_res = result['hg']
        time_str = f"{hg_res['time']:>10.4f}" if hg_res['time'] is not None else "      N/A"
        print(f"| {'':<25} | {'Heuristic Greedy (heuristic_greedy.py)':<45} | {hg_res['rows']:>12} | {time_str} |")
        sa_res = result['sa']
        time_str = f"{sa_res['time']:>10.4f}" if sa_res['time'] is not None else "      N/A"
        print(f"| {'':<25} | {'Simulated Annealing (simulated_annealing.py)':<45} | {sa_res['rows']:>12} | {time_str} |")
        acts_res = result['acts']
        time_str = f"{acts_res['time']:>10.4f}" if acts_res['time'] is not None else "      N/A"
        print(f"| {'':<25} | {'ACTS (acts_runner.py)':<45} | {acts_res['rows']:>12} | {time_str} |")
        print(line)

if __name__ == '__main__':
    main()
