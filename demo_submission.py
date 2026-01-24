import pika
import sys
import json
import os

# ================= 設定區 =================
RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'task_queue'
# 您的 Consumer 有設帳密，所以這裡也要設，不然會被拒絕連線
CREDENTIALS = pika.PlainCredentials('admin', 'admin123')
# =========================================

def main():
    if len(sys.argv) < 2:
        print("使用方式: python3 demo_submission.py <fasta_file>")
        sys.exit(1)

    fasta_file = sys.argv[1]
    
    if not os.path.exists(fasta_file):
        print(f"錯誤: 找不到檔案 {fasta_file}")
        sys.exit(1)

    print(f"📂 正在讀取 {fasta_file} ...")

    # --- 1. 解析 FASTA (抓取 ID 和 Sequence) ---
    target_id = None
    sequence_lines = []
    
    with open(fasta_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            if line.startswith('>'):
                # 如果已經有抓到上一筆 ID，就停止 (我們只 Demo 一筆)
                if target_id is not None:
                    break
                # 抓取 ID (去掉 >) e.g. >sp|Q8CDT5|SMI11_MOUSE
                target_id = line[1:].split()[0]
            else:
                # 這是序列部分
                if target_id is not None:
                    sequence_lines.append(line)
    
    if not target_id or not sequence_lines:
        print("❌ 錯誤: 無法解析 Fasta 格式 (需包含 > ID 和序列)")
        sys.exit(1)

    # 組合序列字串
    full_sequence = "".join(sequence_lines)
    print(f"🎯 解析成功:")
    print(f"   - ID: {target_id}")
    print(f"   - Seq 長度: {len(full_sequence)}")

    # --- 2. 準備 JSON 訊息 (配合 Consumer 格式) ---
    message = {
        'id': target_id,
        'sequence': full_sequence
    }
    json_body = json.dumps(message)

    # --- 3. 發送至 RabbitMQ ---
    try:
        # 使用與 Consumer 相同的連線參數 (含帳密)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            credentials=CREDENTIALS
        ))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json_body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # 持久化
            ))
        
        print(f"✅ [Sent] 任務已發送！")
        print("-" * 30)
        print("請等待約 1 分鐘後，執行 ./demo_check_result.sh 查看結果。")
    

        
        connection.close()
    except Exception as e:
        print(f"❌ RabbitMQ 連線失敗: {e}")

if __name__ == "__main__":
    main()