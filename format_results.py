import csv
import statistics

# ================= 設定 =================
INPUT_FILE = "final_results.csv"
HITS_OUTPUT = "hits_output.csv"
PROFILE_OUTPUT = "profile_output.csv"
# =======================================

def is_valid_number(value):
    """檢查是否為有效數字 (不是 nan 也不是空字串)"""
    try:
        f = float(value)
        # 檢查是否為 nan (float('nan') != float('nan'))
        if f != f: 
            return False
        return True
    except ValueError:
        return False

def main():
    print(f"🔄 正在讀取 {INPUT_FILE} 並進行轉換...")
    
    # 準備儲存數據
    std_values = []
    gmean_values = []
    
    try:
        with open(INPUT_FILE, 'r') as f_in, \
             open(HITS_OUTPUT, 'w', newline='') as f_hits:
            
            reader = csv.DictReader(f_in)
            writer_hits = csv.writer(f_hits)
            
            # 1. 寫入 hits_output.csv 的標題
            writer_hits.writerow(['fasta_id', 'best_hit_id'])
            
            count = 0
            for row in reader:
                count += 1
                
                # --- 處理任務 A: hits_output ---
                # 抓取 query_id 和 best_hit
                # 注意：如果您的 final_results.csv 標題是 query_id,best_hit... 請確保這裡對應
                q_id = row.get('query_id', '').strip()
                b_hit = row.get('best_hit', '').strip()
                writer_hits.writerow([q_id, b_hit])
                
                # --- 處理任務 B: profile_output ---
                # 抓取 score_std 和 score_gmean
                s_std = row.get('score_std', '')
                s_gmean = row.get('score_gmean', '')
                
                if is_valid_number(s_std):
                    std_values.append(float(s_std))
                    
                if is_valid_number(s_gmean):
                    gmean_values.append(float(s_gmean))

        print(f"✅ 已生成 {HITS_OUTPUT} (共 {count} 筆)")

        # 2. 計算平均值並寫入 profile_output.csv
        # 如果沒有有效數據，設為 0
        ave_std = statistics.mean(std_values) if std_values else 0
        ave_gmean = statistics.mean(gmean_values) if gmean_values else 0
        
        with open(PROFILE_OUTPUT, 'w', newline='') as f_profile:
            writer_profile = csv.writer(f_profile)
            # 寫入標題
            writer_profile.writerow(['ave_std', 'ave_gmean'])
            # 寫入數據 (保留兩位小數)
            writer_profile.writerow([f"{ave_std:.2f}", f"{ave_gmean:.2f}"])
            
        print(f"✅ 已生成 {PROFILE_OUTPUT}")
        print(f"   - Average Std: {ave_std:.2f} (樣本數: {len(std_values)})")
        print(f"   - Average Gmean: {ave_gmean:.2f} (樣本數: {len(gmean_values)})")

    except FileNotFoundError:
        print(f"❌ 錯誤：找不到檔案 {INPUT_FILE}")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

if __name__ == "__main__":
    main()