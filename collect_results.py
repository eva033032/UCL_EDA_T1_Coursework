import subprocess
import os
import sys

# =================Settings=================
OUTPUT_FILE = "final_results.csv"
CSV_HEADER = "query_id,best_hit,best_evalue,best_score,score_mean,score_std,score_gmean\n"
# =======================================

def collect_data():
    print(f"🔄 Starting data collection. Target file: {OUTPUT_FILE} ...")
    
    # 1. Write the header first
    with open(OUTPUT_FILE, "w") as f:
        f.write(CSV_HEADER)
    
    # 2. Execute command via Ansible
    # awk 'FNR==2' means: print only the "2nd line" of each file (the data line, skipping the header)
    # This command retrieves data from all parse.out files on the machine at once
    remote_cmd = "awk 'FNR==2' /home/almalinux/*parse.out"
    
    cmd = [
        "ansible", 
        "-i", "inventory.ini", 
        "workers", 
        "-m", "shell", 
        "-a", remote_cmd
    ]

    print("📡 Connecting to Workers to fetch data (this may take a few seconds)...")
    
    # Execute Ansible command and capture output
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
    except Exception as e:
        print(f"❌ Error executing Ansible: {e}")
        sys.exit(1)

    # 3. Parse and filter Ansible output
    # Ansible output includes system messages like "worker-0 | CHANGED..."; we need to filter these out
    total_lines = 0
    with open(OUTPUT_FILE, "a") as f:
        # Flag: Check if we are currently reading a data block from a machine
        in_data_block = False
        
        for line in stdout.split('\n'):
            # Check if it is an Ansible machine separator line
            if " | CHANGED | rc=0 >>" in line or " | SUCCESS | rc=0 >>" in line:
                # This indicates that the data follows immediately below
                in_data_block = True
                print(f"   --> Reading data from {line.split()[0]}...")
                continue
            
            # Skip empty or invalid lines
            if not line.strip():
                continue
                
            # If inside a data block and the line contains a comma (simple CSV validation)
            if in_data_block:
                if "," in line:
                    f.write(line + "\n")
                    total_lines += 1
                else:
                    # If a non-CSV line is encountered, the block might have ended
                    pass

    print("-" * 30)
    print(f"✅ Success!")
    print(f"📊 Total collected: {total_lines} records")
    print(f"💾 File saved as: {OUTPUT_FILE}")

    # Simple verification
    if total_lines >= 5999:
        print("Perfect! Data volume meets expectations (approx. 6000 records).")
    else:
        print(f"Warning: Data volume ({total_lines}) is less than expected. Please check if any Worker connection failed.")

if __name__ == "__main__":
    collect_data()