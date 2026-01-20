import pika
import json
import sys
from Bio import SeqIO

# ==========================================
# 設定區
# ==========================================
QUEUE_NAME = 'task_queue'
ID_FILE = 'experiment_ids.txt'
FASTA_FILE = 'UP000000589_10090.fasta' # 請確認檔名是否正確 (若是 .gz 需先 gunzip)
# ==========================================

def main():
    # 1. 建立 RabbitMQ 連線 (連本機)
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True) # Durable 代表重開機後 Queue 還在
    except Exception as e:
        print(f"無法連線到 RabbitMQ: {e}")
        sys.exit(1)

    # 2. 讀取要跑的 ID 清單
    print(f"正在讀取 {ID_FILE}...")
    target_ids = set()
    try:
        with open(ID_FILE, 'r') as f:
            for line in f:
                # 處理可能的空白或換行
                clean_id = line.strip()
                if clean_id:
                    target_ids.add(clean_id)
    except FileNotFoundError:
        print(f"錯誤：找不到 {ID_FILE}")
        sys.exit(1)
    
    print(f"目標 ID 總數: {len(target_ids)}")

    # 3. 掃描 FASTA 檔並發送任務
    print(f"正在掃描 {FASTA_FILE} 並發送任務...")
    count = 0
    
    # 使用 Biopython 讀取
    # 注意：如果您的 FASTA 檔還沒解壓縮，請先執行 'gunzip UP000000589_10090.fasta.gz'
    for record in SeqIO.parse(FASTA_FILE, "fasta"):
        # 處理 ID 格式 (有些是 'sp|Q9JIX|...', 我們只要中間的 ID)
        # 如果您的 experiment_ids.txt 裡面是很單純的 ID，這裡可能需要 split
        # 假設 record.id 長這樣: "tr|A0A087WPF7|A0A087WPF7_MOUSE"
        # 這裡做一個通用的檢查
        
        match = False
        if record.id in target_ids:
            match = True
        else:
            # 試試看拆解 pipe '|'
            parts = record.id.split('|')
            for part in parts:
                if part in target_ids:
                    match = True
                    break
        
        if match:
            # 準備訊息內容
            message = {
                'id': record.id,
                'sequence': str(record.seq)
            }
            
            # 發送訊息
            channel.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 讓訊息持久化 (Persistent)
                ))
            count += 1
            
            if count % 100 == 0:
                print(f"已發送 {count} 筆...")

    print(f"✅ 發送完畢！總共發送了 {count} 個任務進入 Queue。")
    connection.close()

if __name__ == '__main__':
    main()