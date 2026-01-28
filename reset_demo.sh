#!/bin/bash

echo "🛑 1. Killing all old consumer processes (Precision Kill)..."
# Logic: List processes -> find consumer.py -> exclude 'grep' -> exclude 'ansible' (prevent suicide) -> get PID -> kill -9
# 'xargs -r' ensures the command doesn't fail if no process is found.
ansible -i inventory.ini workers -m shell -a "ps -ef | grep consumer.py | grep -v grep | grep -v ansible | awk '{print \$2}' | xargs -r kill -9"

echo "🧹 2. Purging RabbitMQ Queue..."
# Clear all pending tasks in RabbitMQ
sudo rabbitmqctl purge_queue task_queue

echo "🗑️  3. Deleting old data & metrics..."
# Remove old result files (.out) and Prometheus metric files (.prom)
ansible -i inventory.ini workers -m shell -a "rm -f /home/almalinux/*.out /home/almalinux/node_exporter_metrics/*.prom"

echo "⏳ 4. Waiting 2 seconds for cleanup to settle..."
sleep 2

echo "🚀 5. Starting new consumers in background..."
# Start the consumer script in background, unbuffered (-u), logging to a file
ansible -i inventory.ini workers -m shell -a "nohup python3 -u /home/almalinux/consumer.py > /home/almalinux/consumer.log 2>&1 &"

echo "---------------------------------------------------"
echo "🔍 VERIFICATION (Target: 0 or 'No such file'):"
# Double check if files are truly gone
ansible -i inventory.ini workers -m shell -a "ls /home/almalinux/*.out 2>/dev/null | wc -l"
echo "---------------------------------------------------"

echo "✅ System Reset Complete! Workers are ready."
echo "👉 Action: Switch to Grafana, then run 'python3 producer.py'"