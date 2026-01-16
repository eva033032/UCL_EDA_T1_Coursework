import sys
import math
from Bio import SeqIO
import os
import subprocess
import shutil

# =================設定區=================
ID_FILE = "experiment_ids.txt"
# ★ 修改這裡：使用官方下載解壓後的正確檔名
SOURCE_FASTA = "UP000000589_10090.fasta" 
NUM_WORKERS = 4
WORKER_INPUT_PATH = "/home/almalinux/input.fa"
# =======================================

def split_and_distribute():
    # 1. 讀取要跑的 ID
    print(f"Reading target IDs from {ID_FILE}...")
    try:
        with open(ID_FILE, 'r') as f:
            target_ids = set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        print(f"Error: {ID_FILE} not found!")
        sys.exit(1)
    
    print(f"Total IDs to process: {len(target_ids)}")

    # 2. 從原始大檔中抓出對應的序列
    print(f"Extracting sequences from {SOURCE_FASTA}...")
    records = []
    
    try:
        # 建立索引以加快搜尋 (針對大檔案優化)
        # 這會比單純 loop 快很多，也能準確抓到 ID
        index = SeqIO.index(SOURCE_FASTA, "fasta")
        
        for tid in target_ids:
            # 嘗試直接匹配
            if tid in index:
                records.append(index[tid])
            else:
                # 如果找不到，嘗試處理 UniProt ID 格式差異 (例如只取中間那段)
                # 這裡保留彈性，目前先印出警告
                # print(f"Warning: ID {tid} not found in source fasta.")
                pass
                
    except FileNotFoundError:
        print(f"Error: {SOURCE_FASTA} not found! Please run wget and gunzip first.")
        sys.exit(1)

    print(f"Found {len(records)} sequences out of {len(target_ids)} requested.")
    
    if len(records) == 0:
        print("Error: No matching sequences found! The IDs in text file do not match FASTA headers.")
        sys.exit(1)

    # 3. 計算每台機器分多少
    chunk_size = math.ceil(len(records) / NUM_WORKERS)
    print(f"Splitting into {NUM_WORKERS} chunks (approx {chunk_size} seqs per worker)...")

    # 4. 切分並分發
    for i in range(NUM_WORKERS):
        start = i * chunk_size
        end = start + chunk_size
        chunk = records[start:end]
        
        if not chunk:
            continue
            
        local_filename = f"job_{i}.fa"
        SeqIO.write(chunk, local_filename, "fasta")
        print(f"--> [Worker-{i}] Prepared {len(chunk)} sequences in {local_filename}")

        worker_name = f"worker-{i}"
        
        # A. 傳送檔案 (Copy)
        print(f"    Sending file to {worker_name}...")
        subprocess.run([
            "ansible", "-i", "inventory.ini", worker_name, 
            "-m", "copy", "-a", f"src={local_filename} dest={WORKER_INPUT_PATH}"
        ], stdout=subprocess.DEVNULL)

        # B. 啟動任務 (Shell - Background)
        print(f"    Starting analysis on {worker_name}...")
        # 使用 nohup 讓它在背景跑
        cmd_run = f"nohup python3 /home/almalinux/pipeline_script.py {WORKER_INPUT_PATH} > /home/almalinux/run.log 2>&1 &"
        
        subprocess.run([
            "ansible", "-i", "inventory.ini", worker_name, 
            "-m", "shell", "-a", cmd_run
        ])

    print("\n✅ All jobs dispatched! Workers are processing in background.")
    print("Check progress with: ansible -i inventory.ini workers -m shell -a 'ps aux | grep python'")

if __name__ == "__main__":
    split_and_distribute()