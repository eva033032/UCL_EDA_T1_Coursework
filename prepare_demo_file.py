import os

# 設定檔案名稱
SOURCE_FILE = 'UP000000589_10090.fasta'  # 來源大檔
OUTPUT_FILE = 'demo_test.fa'             # 目標檔案
TARGET_ID = 'sp|A0A0B4J1F4|ARRD4_MOUSE'  # 我們要抓的冠軍 ID

def main():
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ 錯誤: 找不到來源檔案 {SOURCE_FILE}")
        print("如果您只有 .gz 檔，請先執行: gunzip UP000000589_10090.fasta.gz")
        return

    print(f"🔍 正在從 {SOURCE_FILE} 搜尋 {TARGET_ID} ...")
    
    found = False
    with open(SOURCE_FILE, 'r') as infile, open(OUTPUT_FILE, 'w') as outfile:
        for line in infile:
            # 檢查標題行
            if line.startswith('>'):
                if TARGET_ID in line:
                    found = True
                    outfile.write(line)
                    print(f"✅ 找到了！正在寫入...")
                elif found:
                    # 如果已經找到過，又遇到下一個 '>'，代表這個蛋白質結束了
                    break
            # 如果在目標區塊內，就寫入序列資料
            elif found:
                outfile.write(line)

    if found:
        print(f"🎉 成功！已將 {TARGET_ID} 的序列存入 {OUTPUT_FILE}")
        print("-" * 30)
        print(f"現在您可以執行 Demo 了：")
        print(f"python3 demo_submission.py {OUTPUT_FILE}")
    else:
        print(f"❌ 錯誤: 在檔案中找不到 ID {TARGET_ID}")

if __name__ == "__main__":
    main()