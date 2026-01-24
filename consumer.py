import pika
import json
import subprocess
import os
import time

# ==========================================
# Configuration
# ==========================================
HOST_IP = '10.134.12.209'
QUEUE_NAME = 'task_queue'
PIPELINE_SCRIPT = '/home/almalinux/pipeline_script.py'
# ==========================================

def run_pipeline(protein_id, sequence):
    """
    Write a single protein to a temp file, call the pipeline, and save the results.
    """
    # 1. Create temporary file
    temp_filename = f"job_{protein_id}.fa"
    safe_filename = temp_filename.replace('|', '_')
    
    # Create output filename (Important! Each ID needs a unique file to avoid overwriting)
    # We replace '|' with '_' to avoid filename errors
    safe_id = protein_id.replace('|', '_')
    output_filename = f"{safe_id}.out"

    with open(safe_filename, "w") as f:
        f.write(f">{protein_id}\n{sequence}\n")
    
    print(f" [Running] Processing protein: {protein_id}")

    # 2. Call external command
    cmd = ["python3", PIPELINE_SCRIPT, safe_filename]
    
    try:
        # Execute and capture output
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # If the pipeline prints to screen (stdout), save stdout
        if result.stdout:
            with open(output_filename, "w") as f:
                f.write(result.stdout)
                
        # If the pipeline produces a fixed filename (e.g., hhr_parse.out), rename it
        # (Double insurance here)
        elif os.path.exists("hhr_parse.out"):
             os.rename("hhr_parse.out", output_filename)

        print(f" [Done] Successfully generated: {output_filename}")
        
        # 3. Clean up temporary file
        if os.path.exists(safe_filename):
            os.remove(safe_filename)
            
    except subprocess.CalledProcessError as e:
        print(f" [Error] Failed: {protein_id}")
        print(f"Error message: {e.stderr}")

def callback(ch, method, properties, body):
    """
    RabbitMQ callback function, executed when a message is received.
    """
    data = json.loads(body)
    run_pipeline(data['id'], data['sequence'])
    
    # Key: Tell RabbitMQ "I'm done, you can delete this message now"
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    print(f" [*] Connecting to Host ({HOST_IP})...")
    
    try:
        # Add username/password authentication
        credentials = pika.PlainCredentials('admin', 'admin123')
        # Add heartbeat=0 to tell Server not to kick me out for taking too long
        parameters = pika.ConnectionParameters(HOST_IP, 5672, '/', credentials, heartbeat=0)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        # Key optimization: Load balancing
        # prefetch_count=1 means "Don't give me the next one until I finish this one"
        # This ensures Load Average doesn't spike, and work is distributed to idle Workers
        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

        print(' [*] Waiting for tasks... Press CTRL+C to exit')
        channel.start_consuming()
        
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Please check if Host firewall port 5672 is open, and if the IP is correct.")

if __name__ == '__main__':
    main()