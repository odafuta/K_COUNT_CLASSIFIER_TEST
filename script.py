import subprocess
import sys
import os
from pathlib import Path
import re

# timeout (sec)
timeout = 3600

# スクリプトを置いているディレクトリ
p = Path("")

# 上記のディレクトリ下の .py ファイルを実行対象とする
sourcefiles = list(p.glob("**/*.py"))

# Python 実行コマンド
python_exec = sys.executable  # 今のPython環境を使用

# 各 .py ファイルを実行
for inp in sourcefiles:
    input_path = str(inp)
    output_path = input_path + ".txt"

    command = [python_exec, input_path]  # 実行コマンド（リスト形式）

    with open(output_path, "w") as outputfile:
        try:
            subprocess.run(command, stderr=outputfile, timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"Timeout: {input_path}")
            break
        except Exception as e:
            print(f"Error executing {input_path}: {e}")
            break
