# Distributed Protein Sequence Analysis System (RabbitMQ Version)

This project implements a scalable distributed system for protein sequence analysis. It utilizes **RabbitMQ** for dynamic task orchestration (load balancing) and **Ansible** for automated cluster deployment.

---

## 1. Installation & Deployment

### Step 1: Configure Inventory

Ensure `inventory.ini` contains the correct IP addresses.

* **[Host]**: Configured as `localhost` (since Ansible runs on the node).
* **[Workers]**: The nodes that will execute the pipeline

### Step 2: Deploy the Cluster

Run the playbook to install RabbitMQ, Python dependencies, and HHSuite on all nodes.

```
ansible-playbook -i inventory.ini playbook.yml
```

*(Optional) Install Netdata monitoring:*

```
ansible-playbook -i inventory.ini install_netdata.yml
```
---
## 2. Demo

Use these scripts to verify the pipeline functionality with a single sequence (`demo_test.fa`) before running the full experiment.

### Step 0: Pre-Demo Preparation (Prove Idempotency)
Before starting, we remove any existing result files for the demo protein (`ARRD4_MOUSE`) from all workers.
```
ansible -i inventory.ini workers -m shell -a "rm /home/almalinux/*ARRD4_MOUSE*"
```

### Step 1: Submit the Demo Task

Reads `demo_test.fa` and pushes it to the RabbitMQ queue.

```
python3 demo_submission.py demo_test.fa
```

### Step 2: Processing

Workers will pick up the task. Check the RabbitMQ Management UI or wait approximately **45–60 seconds**.
```
# Check who is currently running the job (Look for [Running] status)
ansible -i inventory.ini workers -m shell -a "grep 'ARRD4_MOUSE' /home/almalinux/consumer.log | tail -n 1"
```

### Step 3: Verify Results

Query the workers to confirm task completion and view the result.

```
./demo_check_result.sh
```

We can also check whether the output file exists on workers.
```
ansible -i inventory.ini workers -m shell -a "ls -l /home/almalinux/*ARRD4_MOUSE*"
```

---

## 3. Running the Full Experiment

To process the full dataset (`UP000000589_10090.fasta`):

### Phase 1: Produce Tasks

Run the producer to read the dataset and publish tasks to the queue.

```
python3 producer.py
```

### Phase 2: Monitor

Monitor progress via the **RabbitMQ Management Interface (Port 15672 - [http://localhost:15672/#/](http://localhost:15672/#/))**.

In addition to the web UI, the following CLI-based monitoring checks are used to verify system health and runtime progress:
```
# Check whether consumer.py processes are running on workers
ansible -i inventory.ini workers -m shell -a "ps -ef | grep consumer.py | grep -v grep"


# Check RabbitMQ queue status (ready & unacknowledged messages)
sudo rabbitmqctl list_queues name messages_ready messages_unacknowledged


# Inspect the last 5 lines of consumer logs to confirm activity
ansible -i inventory.ini workers -m shell -a "tail -n 5 /home/almalinux/consumer.log"


# Search logs for runtime errors or exceptions
ansible -i inventory.ini workers -m shell -a "grep -i 'Error' /home/almalinux/consumer.log | tail -n 5"


# Verify successful output generation (CSV-formatted lines)
ansible -i inventory.ini workers -m shell -a "grep ',' /home/almalinux/*.out | head -n 3"
```

### Phase 3: Batch Collection & Reporting

Once the queue is empty, collect the results using Ansible (batch strategy) and generate the report.

#### 1. Archive & Fetch Results (via Ansible)

Compress output files on all workers and fetch them to `collected_results/` on the manager node.

```
ansible -i inventory.ini workers -m shell -a "tar -czf /home/almalinux/results.tar.gz /home/almalinux/*.out"

ansible -i inventory.ini workers -m fetch -a "src=/home/almalinux/results.tar.gz dest=./collected_results/"
```

#### 2. Generate Final Report

Unzip the data and calculate statistics (filtering out NaN values).

```
mkdir -p final_data

for file in collected_results/*/home/almalinux/results.tar.gz; do tar -xzf "$file" -C final_data/; done

mv final_data/home/almalinux/*.out final_data/ 2>/dev/null

python3 create_final_report.py
```

*Outputs:*

* `final_hits_output.csv`
* `final_profile_output.csv`
* `missing_ids.txt`

---

## 4. File Structure Overview

### Active System Logic (RabbitMQ Core)

* `producer.py`: Reads FASTA files and publishes tasks to the queue.
* `consumer.py`: Runs on workers; listens to the queue and executes the pipeline.
* `pipeline_script.py`: Wrapper script that orchestrates HHSearch and S4Pred.
* `results_parser.py`: Helper library to parse HHSearch raw text output into CSV format.
* `select_ids.py`: Helper script to filter specific protein IDs from the large dataset.

### Data Processing & Reporting

* `UP000000589_10090.fasta`: The main input dataset.
* `experiment_ids.txt`: List of target IDs used to verify completeness.
* `create_final_report.py`: The main reporting script. Aggregates results, filters NaNs, and generates CSVs.
* `final_hits_output.csv`: Final consolidated results (ID & Best Hit).
* `final_profile_output.csv`: Final statistical profile (Average Std / GMean).
* `missing_ids.txt`: Generated by the report script; logs any tasks that failed or are missing.

### Infrastructure & Automation

* `playbook.yml`: Main Ansible playbook for system deployment (RabbitMQ, Python, HHSuite).
* `inventory.ini`: Ansible hosts file defining Manager and Worker nodes.

### Live Demo Files

* `prepare_demo_file.py`: Script used to generate `demo_test.fa` from the main dataset.
* `demo_submission.py`: Submits a single job for the Viva demonstration.
* `demo_check_result.sh`: Shell script to check results on workers via Ansible.
* `demo_test.fa`: A small FASTA file used specifically for the demo.

### Runtime Directories

* `final_data/`: Directory where all `.out` files are extracted for analysis.
* `collected_results/`: Directory where Ansible stores the fetched `.tar.gz` files from workers.

### Other
* `install_netdata.yml`: Playbook for installing Netdata monitoring agent.
* `test-authorized-keys.sh`: Script to verify SSH connectivity across the cluster.
* `lecturer_key.pub`: Public key for lecturer access.
