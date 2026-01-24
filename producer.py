import pika
import json
import sys
from Bio import SeqIO

# ==========================================
# Configuration Section
# ==========================================
QUEUE_NAME = 'task_queue'
ID_FILE = 'experiment_ids.txt'
FASTA_FILE = 'UP000000589_10090.fasta'
# ==========================================

def main():
    # 1. Establish RabbitMQ connection (localhost)
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True) # Durable means the queue survives reboots
    except Exception as e:
        print(f"Cannot connect to RabbitMQ: {e}")
        sys.exit(1)

    # 2. Read ID list to process
    print(f"Reading {ID_FILE}...")
    target_ids = set()
    try:
        with open(ID_FILE, 'r') as f:
            for line in f:
                # Remove whitespace or newlines
                clean_id = line.strip()
                if clean_id:
                    target_ids.add(clean_id)
    except FileNotFoundError:
        print(f"Error: {ID_FILE} not found")
        sys.exit(1)
    
    print(f"Total target IDs: {len(target_ids)}")

    # 3. Scan FASTA file and send tasks
    print(f"Scanning {FASTA_FILE} and sending tasks...")
    count = 0
    
    # Read using Biopython
    for record in SeqIO.parse(FASTA_FILE, "fasta"):
        # Handle ID format 
        match = False
        if record.id in target_ids:
            match = True
        else:
            # Try splitting by pipe '|'
            parts = record.id.split('|')
            for part in parts:
                if part in target_ids:
                    match = True
                    break
        
        if match:
            # Prepare message content
            message = {
                'id': record.id,
                'sequence': str(record.seq)
            }
            
            # Send message
            channel.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                ))
            count += 1
            
            if count % 100 == 0:
                print(f"Sent {count} tasks...")

    print(f"✅ Done! Total {count} tasks sent to Queue.")
    connection.close()

if __name__ == '__main__':
    main()