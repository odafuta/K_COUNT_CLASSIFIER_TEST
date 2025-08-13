import os
import subprocess
import tempfile
import time
import sys
from typing import Dict, Any, List

def check_java_availability():
    """
    Check if Java is available on the system
    
    Returns:
    bool: True if Java is available, False otherwise
    """
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def generate_acts_input_file(n: int, tau: int, k: int) -> str:
    """
    Generate ACTS input file content for given parameters
    
    Parameters:
    n: number of parameters
    tau: strength (t-way coverage)
    k: maximum number of 1s in each row
    
    Returns:
    String content for ACTS input file
    """
    content = "[System]\n"
    content += "Name: TestSystem\n\n"
    
    content += "[Parameter]\n"
    for i in range(1, n + 1):
        content += f"p{i}(int): 0,1\n"
    content += "\n"
    
    content += "[Constraint]\n"
    # Constraint: sum of all parameters = k
    param_sum = " + ".join([f"p{i}" for i in range(1, n + 1)])
    content += f"{param_sum} = {k}\n"
    
    return content

def parse_acts_output(output_file: str) -> List[List[int]]:
    """
    Parse ACTS output file and extract the covering array
    
    Parameters:
    output_file: path to ACTS output file
    
    Returns:
    List of rows representing the covering array
    """
    covering_array = []
    
    if not os.path.exists(output_file):
        return covering_array
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find the start of test cases (CSV format)
        found_header = False
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Look for the CSV header line (parameter names)
            if line.startswith('p1,p2') or (line.count(',') > 0 and 'p' in line):
                found_header = True
                continue
            
            # Parse CSV data rows after header
            if found_header and line:
                # Split by comma and convert to integers
                values = []
                parts = line.split(',')
                try:
                    for part in parts:
                        part = part.strip()
                        if part.isdigit():
                            values.append(int(part))
                    
                    if len(values) > 0:
                        covering_array.append(values)
                except ValueError:
                    # Skip non-numeric lines
                    continue
                    
    except Exception as e:
        print(f"Error parsing ACTS output file: {e}")
    
    return covering_array

def run_acts_covering_array(
    n: int,
    tau: int, 
    k: int,
    seed: int = 0,
    verbose: bool = True,
    timeout_seconds: int = 600
) -> Dict[str, Any]:
    """
    Run ACTS tool to generate covering array for given parameters
    
    Parameters:
    n: number of parameters
    tau: strength (t-way coverage)
    k: maximum number of 1s in each row
    seed: random seed (not directly used by ACTS but for consistency)
    verbose: whether to print progress information
    
    Returns:
    Dictionary containing results
    """
    start_time = time.perf_counter()
    
    if verbose:
        print(f"Running ACTS with n={n}, tau={tau}, k={k}")
    
    # Check Java availability first
    if not check_java_availability():
        error_msg = (
            "Java is not installed or not found in system PATH. "
            "ACTS requires Java to run. Please install Java JRE/JDK and ensure it's in your PATH."
        )
        if verbose:
            print(f"Error: {error_msg}")
        return {
            "n": n,
            "tau": tau,
            "k": k,
            "num_rows": None,
            "covered": False,
            "coverage_percentage": 0.0,
            "time": time.perf_counter() - start_time,
            "covering_array": [],
            "error": error_msg
        }
    
    # Generate input file content
    input_content = generate_acts_input_file(n, tau, k)
    
    # Create acts_inputs directory if it doesn't exist
    input_dir = "acts_inputs"
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    
    # Create input and output file paths
    input_filename = f"acts_input_n{n}_tau{tau}_k{k}.txt"
    output_filename = f"acts_output_n{n}_tau{tau}_k{k}.csv"
    input_file_path = os.path.join(input_dir, input_filename)
    output_file_path = os.path.join(input_dir, output_filename)
    
    # Write input file
    with open(input_file_path, 'w', encoding='utf-8') as f:
        f.write(input_content)
    
    try:
        # Construct ACTS command with proper JVM options
        acts_jar_path = os.path.join(os.getcwd(), 'acts_3.2.jar')
        if not os.path.exists(acts_jar_path):
            raise FileNotFoundError(f"ACTS jar file not found at {acts_jar_path}")
        
        cmd = [
            'java',
            '-jar',
            f'-Dchandler=solver',
            f'-Ddoi={tau}',
            f'-Doutput=csv',
            f'-Dprogress=off',
            acts_jar_path,
            input_file_path,
            output_file_path
        ]
        
        if verbose:
            print(f"Executing: {' '.join(cmd)}")
        
        # Run ACTS
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        if result.returncode != 0:
            error_msg = f"ACTS execution failed with return code {result.returncode}"
            if result.stderr:
                error_msg += f"\nStderr: {result.stderr}"
            if verbose:
                print(error_msg)
            return {
                "n": n,
                "tau": tau,
                "k": k,
                "num_rows": None,
                "covered": False,
                "coverage_percentage": 0.0,
                "time": time.perf_counter() - start_time,
                "covering_array": [],
                "error": error_msg
            }
        
        # Parse output
        covering_array = parse_acts_output(output_file_path)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        if verbose:
            print(f"ACTS completed in {total_time:.4f}s, generated {len(covering_array)} rows")
        
        # Validate that all constraints are satisfied
        valid_array = True
        for row in covering_array:
            if sum(row) != k:
                valid_array = False
                if verbose:
                    print(f"Warning: Row {row} violates k-constraint (sum={sum(row)} != k={k})")
                break
        
        covered = len(covering_array) > 0 and valid_array
        
        return {
            "n": n,
            "tau": tau,
            "k": k,
            "num_rows": len(covering_array),
            "covered": covered,
            "coverage_percentage": 1.0 if covered else 0.0,
            "time": total_time,
            "covering_array": covering_array
        }
        
    except subprocess.TimeoutExpired:
        error_msg = "ACTS execution timed out"
        if verbose:
            print(error_msg)
        return {
            "n": n,
            "tau": tau,
            "k": k,
            "num_rows": None,
            "covered": False,
            "coverage_percentage": 0.0,
            "time": time.perf_counter() - start_time,
            "covering_array": [],
            "error": error_msg
        }
    
    except Exception as e:
        error_msg = f"Error running ACTS: {str(e)}"
        if verbose:
            print(error_msg)
        return {
            "n": n,
            "tau": tau,
            "k": k,
            "num_rows": None,
            "covered": False,
            "coverage_percentage": 0.0,
            "time": time.perf_counter() - start_time,
            "covering_array": [],
            "error": error_msg
        }
    
    finally:
        # Keep files for inspection - no cleanup
        if verbose:
            print(f"Input file saved: {input_file_path}")
            print(f"Output file saved: {output_file_path}")

# Test function for command line usage
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python acts_runner.py n tau k [seed]")
        sys.exit(1)
    
    n = int(sys.argv[1])
    tau = int(sys.argv[2])
    k = int(sys.argv[3])
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 42
    
    result = run_acts_covering_array(n, tau, k, seed=seed, verbose=True, timeout_seconds=600)
    
    print("\n最終結果:")
    print(f"パラメータ: n={n}, tau={tau}, k={k}")
    print(f"生成行数: {result['num_rows']}")
    print(f"カバー率: {result['coverage_percentage']:.2%}")
    print(f"実行時間: {result['time']:.4f}秒")
    
    if result.get('error'):
        print(f"エラー: {result['error']}")
    
    if result['num_rows'] and result['num_rows'] < 50:
        print("\nカバーリング配列:")
        for i, row in enumerate(result['covering_array'], 1):
            print(f"{i:3}: {row}") 