import os
import sys
import math

# ================= Settings =================
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
    print(f"🚀 Starting report compilation (NaN exclusion mode)...")
    
    if not os.path.exists(ID_FILE):
        print(f"❌ Error: File not found {ID_FILE}")
        sys.exit(1)

    with open(ID_FILE, 'r') as f:
        target_ids = set(line.strip() for line in f if line.strip())
    
    # Prepare containers
    hits_data = []      
    all_stds = []       
    all_gmeans = []     
    found_ids = set()   
    
    # Count invalid data (NaN)
    nan_count = 0 
    
    files = os.listdir(RESULTS_DIR)
    print(f"📂 Scanning {len(files)} files...")

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
                            # --- Key Fix: Check for NaN ---
                            val_std = float(parts[5])
                            val_gmean = float(parts[6])

                            # If nan (invalid value), skip it; do not add to list
                            if math.isnan(val_std) or math.isnan(val_gmean):
                                nan_count += 1
                                # Even if values are bad, the ID ran. Should it count as a hit?
                                # NaN usually means calculation failure. Suggest excluding from stats.
                                continue 
                            
                            # Add only valid values
                            all_stds.append(val_std)
                            all_gmeans.append(val_gmean)
                            
                            # Add to Hits list
                            hits_data.append(f"{raw_id},{best_hit}")

                            # Record ID
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

    # 3. Output Hits CSV
    print(f"💾 Writing {OUTPUT_HITS} ({len(hits_data)} records)...")
    with open(OUTPUT_HITS, 'w') as f:
        f.write("fasta_id,best_hit_id\n") 
        for line in hits_data:
            f.write(line + "\n")

    # 4. Output Profile CSV
    print(f"💾 Calculating {OUTPUT_PROFILE} ...")
    print(f"   ℹ️  Excluded NaN data count: {nan_count}")
    print(f"   ℹ️  Valid data used for calculation: {len(all_stds)}")

    if len(all_stds) > 0:
        avg_std = sum(all_stds) / len(all_stds)
        avg_gmean = sum(all_gmeans) / len(all_gmeans)
        
        with open(OUTPUT_PROFILE, 'w') as f:
            f.write("ave_std,ave_gmean\n")
            f.write(f"{avg_std:.2f},{avg_gmean:.2f}\n")
            
        print(f"   ✅ Success! Ave STD = {avg_std:.2f}, Ave GMean = {avg_gmean:.2f}")
    else:
        print("❌ Error: All data is NaN or missing. Cannot calculate averages!")

    # 5. Missing Check
    missing_ids = target_ids - found_ids
    print("-" * 30)
    if missing_ids:
        print(f"⚠️ There are {len(missing_ids)} tasks incomplete or NaN")
        with open(MISSING_FILE, 'w') as f:
            for mid in sorted(missing_ids):
                f.write(mid + "\n")
    else:
        print(" Perfect! All tasks completed!")

if __name__ == "__main__":
    main()