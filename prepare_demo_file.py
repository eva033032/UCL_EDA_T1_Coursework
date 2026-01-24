import os

# File Settings
SOURCE_FILE = 'UP000000589_10090.fasta'  # Source file
OUTPUT_FILE = 'demo_test.fa'             # Output file
TARGET_ID = 'sp|A0A0B4J1F4|ARRD4_MOUSE'  # Target ID to extract

def main():
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ Error: Source file {SOURCE_FILE} not found.")
        print("If you only have the .gz file, please run first: gunzip UP000000589_10090.fasta.gz")
        return

    print(f"🔍 Searching for {TARGET_ID} in {SOURCE_FILE} ...")
    
    found = False
    with open(SOURCE_FILE, 'r') as infile, open(OUTPUT_FILE, 'w') as outfile:
        for line in infile:
            # Check header line
            if line.startswith('>'):
                if TARGET_ID in line:
                    found = True
                    outfile.write(line)
                    print(f"✅ Found! Writing...")
                elif found:
                    # If already found and the next '>' is met, this protein entry ends
                    break
            # If inside the target block, write sequence data
            elif found:
                outfile.write(line)

    if found:
        print(f"Success, Saved {TARGET_ID} sequence to {OUTPUT_FILE}")
        print("-" * 30)
        print(f"You can run the demo now:")
        print(f"python3 demo_submission.py {OUTPUT_FILE}")
    else:
        print(f"❌ Error: ID {TARGET_ID} not found in the file.")

if __name__ == "__main__":
    main()