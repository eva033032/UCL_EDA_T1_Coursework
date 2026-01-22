import os
import sys
import math  # <--- 新增數學模組來抓出 nan

# ================= 設定區 =================
RESULTS_DIR = "final_data"            
ID_FILE = "experiment_ids.txt"        
OUTPUT_HITS = "final_hits_output.csv"       
OUTPUT_PROFILE = "final_profile_output.csv" 
MISSING_FILE = "missing_ids.txt"      
# =========================================

def get_clean_id(header_string):
    try:
        if "|" in header_string:
            return header_string.split("|")[1]
        return header_string
    except:
        return header_string

def main():
    print(f"🚀 開始彙整報告 (排除 NaN 壞值模式)...")
    
    if not os.path.exists(ID_FILE):
        print(f"❌ 錯誤: 找不到 {ID_FILE}")
        sys.exit(1)

    with open(ID_FILE, 'r') as f:
        target_ids = set(line.strip() for line in f if line.strip())
    
    # 準備容器
    hits_data = []      
    all_stds = []       
    all_gmeans = []     
    found_ids = set()   
    
    # 統計壞掉的數據
    nan_count = 0 
    
    files = os.listdir(RESULTS_DIR)
    print(f"📂 正在掃描 {len(files)} 個檔案...")

    for filename in files:
        if not filename.endswith(".out"):
            continue

        filepath = os.path.join(RESULTS_DIR, filename)
        
        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                
                if not content or "Traceback" in content:
                    continue

                lines = content.split('\n')
                for line in lines:
                    if "query_id" in line or "," not in line:
                        continue
                        
                    parts = line.split(',')
                    # index 0: query_id, 1: hit, 5: std, 6: gmean
                    if len(parts) >= 7:
                        raw_id = parts[0]
                        best_hit = parts[1]
                        
                        try:
                            # --- 關鍵修正：檢查 NaN ---
                            val_std = float(parts[5])
                            val_gmean = float(parts[6])

                            # 如果是 nan (無效數值)，就跳過，不要加進清單
                            if math.isnan(val_std) or math.isnan(val_gmean):
                                nan_count += 1
                                # 雖然數值壞了，但 ID 算是有跑過，還是可以加到 hits 嗎？
                                # 通常 nan 代表計算失敗，建議這裡先不加入統計
                                continue 
                            
                            # 數值正常才加入
                            all_stds.append(val_std)
                            all_gmeans.append(val_gmean)
                            
                            # 加入 Hits 清單
                            hits_data.append(f"{raw_id},{best_hit}")

                            # 記錄 ID
                            clean_id = get_clean_id(raw_id)
                            if clean_id in target_ids:
                                found_ids.add(clean_id)
                            else:
                                for tid in target_ids:
                                    if tid in raw_id:
                                        found_ids.add(tid)
                                        break

                        except ValueError:
                            continue 

        except Exception:
            pass 

    # 3. 輸出 Hits CSV
    print(f"💾 寫入 {OUTPUT_HITS} (共 {len(hits_data)} 筆)...")
    with open(OUTPUT_HITS, 'w') as f:
        f.write("fasta_id,best_hit_id\n") 
        for line in hits_data:
            f.write(line + "\n")

    # 4. 輸出 Profile CSV
    print(f"💾 計算 {OUTPUT_PROFILE} ...")
    print(f"   ℹ️  排除掉的 NaN 資料數: {nan_count} 筆")
    print(f"   ℹ️  有效納入計算的資料數: {len(all_stds)} 筆")

    if len(all_stds) > 0:
        avg_std = sum(all_stds) / len(all_stds)
        avg_gmean = sum(all_gmeans) / len(all_gmeans)
        
        with open(OUTPUT_PROFILE, 'w') as f:
            f.write("ave_std,ave_gmean\n")
            f.write(f"{avg_std:.2f},{avg_gmean:.2f}\n")
            
        print(f"   ✅ 成功！Ave STD = {avg_std:.2f}, Ave GMean = {avg_gmean:.2f}")
    else:
        print("❌ 錯誤: 所有數據都是 NaN 或沒有數據，無法計算平均值！")

    # 5. 缺漏檢查
    missing_ids = target_ids - found_ids
    print("-" * 30)
    if missing_ids:
        print(f"⚠️ 尚有 {len(missing_ids)} 個任務未完成或數值為 NaN")
        with open(MISSING_FILE, 'w') as f:
            for mid in sorted(missing_ids):
                f.write(mid + "\n")
    else:
        print("🎉 完美！所有任務已完成！")

if __name__ == "__main__":
    main()