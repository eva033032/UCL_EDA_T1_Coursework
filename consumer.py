import pika
import json
import subprocess
import os
import time

# ==========================================
# 設定區 (請修改這裡！)
# ==========================================
HOST_IP = '10.134.12.209'  # <--- 請填入 Host 的內網 IP
QUEUE_NAME = 'task_queue'
PIPELINE_SCRIPT = '/home/almalinux/pipeline_script.py'
# ==========================================

def run_pipeline(protein_id, sequence):
    """
    將單一蛋白質寫入暫存檔，呼叫 pipeline，並將結果存檔
    """
    # 1. 建立暫存檔
    temp_filename = f"job_{protein_id}.fa"
    safe_filename = temp_filename.replace('|', '_')
    
    # 建立輸出檔名 (重要！每個 ID 要有獨立的檔案，才不會互相覆蓋)
    # 我們把 '|' 換成 '_' 以免檔名出錯
    safe_id = protein_id.replace('|', '_')
    output_filename = f"{safe_id}.out"

    with open(safe_filename, "w") as f:
        f.write(f">{protein_id}\n{sequence}\n")
    
    print(f" [Running] 處理蛋白質: {protein_id}")

    # 2. 呼叫外部指令
    cmd = ["python3", PIPELINE_SCRIPT, safe_filename]
    
    try:
        # 執行並捕捉輸出
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # ★★★ 關鍵修正：將結果寫入檔案 ★★★
        # 如果 pipeline 是印出到螢幕 (stdout)，我們就存 stdout
        if result.stdout:
            with open(output_filename, "w") as f:
                f.write(result.stdout)
                
        # 如果 pipeline 是產生固定檔名 (如 hhr_parse.out)，我們就把它改名
        # (這裡做個雙重保險)
        elif os.path.exists("hhr_parse.out"):
             os.rename("hhr_parse.out", output_filename)

        print(f" [Done] 成功產出: {output_filename}")
        
        # 3. 清理暫存檔
        if os.path.exists(safe_filename):
            os.remove(safe_filename)
            
    except subprocess.CalledProcessError as e:
        print(f" [Error] 失敗: {protein_id}")
        print(f"錯誤訊息: {e.stderr}")

def callback(ch, method, properties, body):
    """
    RabbitMQ 的回呼函數，當收到訊息時會執行這裡
    """
    data = json.loads(body)
    run_pipeline(data['id'], data['sequence'])
    
    # 關鍵：告訴 RabbitMQ "我做完了，可以把這則訊息刪掉了"
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    print(f" [*] 正在連線到 Host ({HOST_IP})...")
    
    try:
        # ★ 修改開始：加入帳號密碼認證
        credentials = pika.PlainCredentials('admin', 'admin123')
        # # 加入 heartbeat=0，告訴 Server 不要因為我算太久就踢掉我
        parameters = pika.ConnectionParameters(HOST_IP, 5672, '/', credentials, heartbeat=0)
        connection = pika.BlockingConnection(parameters)
        # ★ 修改結束
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        # 關鍵優化：負載平衡
        # prefetch_count=1 代表 "我手上這個沒做完，不要給我下一個"
        # 這保證了 Load Average 不會爆衝，且工作會自動分配給比較閒的 Worker
        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

        print(' [*] 等待任務中... 按 CTRL+C 離開')
        channel.start_consuming()
        
    except Exception as e:
        print(f"連線失敗: {e}")
        print("請檢查 Host 防火牆是否開啟 5672，以及 IP 是否正確。")

if __name__ == '__main__':
    main()