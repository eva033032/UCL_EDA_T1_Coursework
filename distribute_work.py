import sys
import math
from Bio import SeqIO
import os
import subprocess
import shutil

# =================Configuration=================
ID_FILE = "experiment_ids.txt"
SOURCE_FASTA = "UP000000589_10090.fasta" 
NUM_WORKERS = 4
WORKER_INPUT_PATH = "/home/almalinux/input.fa"
# ===============================================

def split_and_distribute():
    # 1. Read target IDs
    print(f"Reading target IDs from {ID_FILE}...")
    try:
        with open(ID_FILE, 'r') as f:
            target_ids = set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        print(f"Error: {ID_FILE} not found!")
        sys.exit(1)
    
    print(f"Total IDs to process: {len(target_ids)}")

    # 2. Extract corresponding sequences from the source file
    print(f"Extracting sequences from {SOURCE_FASTA}...")
    records = []
    
    try:
        # Create an index for faster lookup (optimized for large files)
        # This is much faster than a simple loop and ensures accurate ID matching
        index = SeqIO.index(SOURCE_FASTA, "fasta")
        
        for tid in target_ids:
            # Attempt direct match
            if tid in index:
                records.append(index[tid])
            else:
                pass
                
    except FileNotFoundError:
        print(f"Error: {SOURCE_FASTA} not found! Please run wget and gunzip first.")
        sys.exit(1)

    print(f"Found {len(records)} sequences out of {len(target_ids)} requested.")
    
    if len(records) == 0:
        print("Error: No matching sequences found! The IDs in text file do not match FASTA headers.")
        sys.exit(1)

    # 3. Calculate workload per worker
    chunk_size = math.ceil(len(records) / NUM_WORKERS)
    print(f"Splitting into {NUM_WORKERS} chunks (approx {chunk_size} seqs per worker)...")

    # 4. Split and distribute
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
        
        # A. Transfer file (Copy)
        print(f"    Sending file to {worker_name}...")
        subprocess.run([
            "ansible", "-i", "inventory.ini", worker_name, 
            "-m", "copy", "-a", f"src={local_filename} dest={WORKER_INPUT_PATH}"
        ], stdout=subprocess.DEVNULL)

        # B. Start task (Shell - Background)
        print(f"    Starting analysis on {worker_name}...")
        # Use nohup to run in the background
        cmd_run = f"nohup python3 /home/almalinux/pipeline_script.py {WORKER_INPUT_PATH} > /home/almalinux/run.log 2>&1 &"
        
        subprocess.run([
            "ansible", "-i", "inventory.ini", worker_name, 
            "-m", "shell", "-a", cmd_run
        ])

    print("\n✅ All jobs dispatched! Workers are processing in background.")
    print("Check progress with: ansible -i inventory.ini workers -m shell -a 'ps aux | grep python'")

if __name__ == "__main__":
    split_and_distribute()