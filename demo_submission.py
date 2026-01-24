import pika
import sys
import json
import os

# ================= Settings =================
RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'task_queue'
CREDENTIALS = pika.PlainCredentials('admin', 'admin123')
# ============================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 demo_submission.py <fasta_file>")
        sys.exit(1)

    fasta_file = sys.argv[1]
    
    if not os.path.exists(fasta_file):
        print(f"Error: File not found {fasta_file}")
        sys.exit(1)

    print(f"📂 Reading {fasta_file} ...")

    # --- 1. Parse FASTA (Extract ID and Sequence) ---
    target_id = None
    sequence_lines = []
    
    with open(fasta_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            if line.startswith('>'):
                # Stop if we already found an ID (We only demo one entry)
                if target_id is not None:
                    break
                # Extract ID (remove >) e.g. >sp|Q8CDT5|SMI11_MOUSE
                target_id = line[1:].split()[0]
            else:
                # This is the sequence part
                if target_id is not None:
                    sequence_lines.append(line)
    
    if not target_id or not sequence_lines:
        print("❌ Error: Cannot parse Fasta format (Must include > ID and sequence)")
        sys.exit(1)

    # Combine sequence lines
    full_sequence = "".join(sequence_lines)
    print(f"🎯 Parse Successful:")
    print(f"   - ID: {target_id}")
    print(f"   - Seq Length: {len(full_sequence)}")

    # --- 2. Prepare JSON Message (Match Consumer Format) ---
    message = {
        'id': target_id,
        'sequence': full_sequence
    }
    json_body = json.dumps(message)

    # --- 3. Send to RabbitMQ ---
    try:
        # Use the same connection parameters as the Consumer (including credentials)
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
                delivery_mode=2,  # Persistent
            ))
        
        print(f"✅ [Sent] Task sent!")
        print("-" * 30)
        print("Please wait about 1 minute, then run ./demo_check_result.sh to check the result.")
    

        
        connection.close()
    except Exception as e:
        print(f"❌ RabbitMQ Connection Failed: {e}")

if __name__ == "__main__":
    main()