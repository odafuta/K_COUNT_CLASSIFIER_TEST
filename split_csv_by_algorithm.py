import pandas as pd
import numpy as np

def split_csv_by_algorithm(input_file='output.csv'):
    """
    CSVファイルをアルゴリズムごとに分けて3つの正規化されたCSVファイルに変換する
    
    Args:
        input_file (str): 入力CSVファイルのパス
    """
    
    # CSVファイルを読み込み
    df = pd.read_csv(input_file)
    
    # アルゴリズムのリスト
    algorithms = ['Adaptive_Sampling', 'Heuristic_Greedy', 'Simulated_Annealing']
    
    # 各アルゴリズムごとにデータを分離
    for algorithm in algorithms:
        # 該当アルゴリズムのデータを抽出
        algorithm_df = df[df['Algorithm'] == algorithm].copy()
        
        # Algorithm列を削除（各ファイルは同じアルゴリズムなので不要）
        algorithm_df = algorithm_df.drop('Algorithm', axis=1)
        
        # データを整理（n, tau, kでソート）
        algorithm_df = algorithm_df.sort_values(['n', 'tau', 'k']).reset_index(drop=True)
        
        # ファイル名を生成
        output_filename = f'{algorithm.lower().replace("_", "_")}_results.csv'
        
        # CSVファイルとして保存
        algorithm_df.to_csv(output_filename, index=False)
        
        print(f'{algorithm}のデータを {output_filename} に保存しました')
        print(f'  行数: {len(algorithm_df)}')
        print(f'  列: {list(algorithm_df.columns)}')
        print()

def create_summary_statistics():
    """
    各アルゴリズムの結果を読み込んで統計情報を表示
    """
    
    algorithms = ['Adaptive_Sampling', 'Heuristic_Greedy', 'Simulated_Annealing']
    
    for algorithm in algorithms:
        filename = f'{algorithm.lower().replace("_", "_")}_results.csv'
        
        try:
            df = pd.read_csv(filename)
            
            print(f'=== {algorithm} 統計情報 ===')
            print(f'総データ数: {len(df)}')
            
            # 有効なデータ（TIMEOUTでない）の統計
            valid_df = df[df['Time'] != 'inf']
            if len(valid_df) > 0:
                valid_df['Time'] = pd.to_numeric(valid_df['Time'], errors='coerce')
                valid_df['Array_Size'] = pd.to_numeric(valid_df['Array_Size'], errors='coerce')
                
                print(f'有効データ数: {len(valid_df)}')
                print(f'平均実行時間: {valid_df["Time"].mean():.4f}秒')
                print(f'平均配列サイズ: {valid_df["Array_Size"].mean():.2f}')
                print(f'最小実行時間: {valid_df["Time"].min():.4f}秒')
                print(f'最大実行時間: {valid_df["Time"].max():.4f}秒')
            else:
                print('有効なデータがありません')
            
            # TIMEOUTの数
            timeout_count = len(df[df['Time'] == 'inf'])
            print(f'TIMEOUT数: {timeout_count}')
            print()
            
        except FileNotFoundError:
            print(f'{filename} が見つかりません')
            print()

if __name__ == "__main__":
    # CSVファイルをアルゴリズムごとに分割
    split_csv_by_algorithm()
    
    # 統計情報を表示
    create_summary_statistics()
    
    print("処理が完了しました。以下のファイルが生成されました:")
    print("- adaptive_sampling_results.csv")
    print("- heuristic_greedy_results.csv") 
    print("- simulated_annealing_results.csv")