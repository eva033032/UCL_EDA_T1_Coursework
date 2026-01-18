import subprocess
import os
import sys

# =================設定檔=================
OUTPUT_FILE = "final_results.csv"
# 這是我們從您的截圖中取得的標準標題
CSV_HEADER = "query_id,best_hit,best_evalue,best_score,score_mean,score_std,score_gmean\n"
# =======================================

def collect_data():
    print(f"🔄 開始收集數據，目標檔案: {OUTPUT_FILE} ...")
    
    # 1. 先寫入標題 (Header)
    with open(OUTPUT_FILE, "w") as f:
        f.write(CSV_HEADER)
    
    # 2. 透過 Ansible 執行指令
    # awk 'FNR==2' 的意思是：只印出每個檔案的「第 2 行」(也就是數據行，跳過標題)
    # 這行指令會一次把該機器上所有 parse.out 的數據吐出來
    remote_cmd = "awk 'FNR==2' /home/almalinux/*parse.out"
    
    cmd = [
        "ansible", 
        "-i", "inventory.ini", 
        "workers", 
        "-m", "shell", 
        "-a", remote_cmd
    ]

    print("📡 正在連線到 Workers 抓取資料 (這可能需要幾秒鐘)...")
    
    # 執行 Ansible 指令並捕獲輸出
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
    except Exception as e:
        print(f"❌ 執行 Ansible 時發生錯誤: {e}")
        sys.exit(1)

    # 3. 解析並過濾 Ansible 的輸出
    # Ansible 的輸出會包含 "worker-0 | CHANGED..." 這種系統訊息，我們要過濾掉
    total_lines = 0
    with open(OUTPUT_FILE, "a") as f:
        # 標記：是否正在讀取某台機器的數據區塊
        in_data_block = False
        
        for line in stdout.split('\n'):
            # 判斷是否為 Ansible 的機器分隔線
            if " | CHANGED | rc=0 >>" in line or " | SUCCESS | rc=0 >>" in line:
                # 看到這個代表下面開始是數據了
                in_data_block = True
                print(f"   --> 正在讀取來自 {line.split()[0]} 的數據...")
                continue
            
            # 如果是空行或不合規的行，略過
            if not line.strip():
                continue
                
            # 如果是在數據區塊內，且這一行包含逗號 (簡單驗證是否為 CSV)
            if in_data_block:
                if "," in line:
                    f.write(line + "\n")
                    total_lines += 1
                else:
                    # 如果遇到非 CSV 格式的行，可能是一個區塊結束了
                    pass

    print("-" * 30)
    print(f"✅ 成功！")
    print(f"📊 總共收集到: {total_lines} 筆資料")
    print(f"💾 檔案已儲存為: {OUTPUT_FILE}")

    # 簡單驗證
    if total_lines >= 5999:
        print("🏆 完美！數據量符合預期 (約 6000 筆)。")
    else:
        print(f"⚠️ 注意：數據量 ({total_lines}) 少於預期，請檢查是否有 Worker 連線失敗。")

if __name__ == "__main__":
    collect_data()