# Distributed Protein Structure Prediction Pipeline

## Overview

This repository contains a distributed data analysis system for predicting protein structures using the S4Pred and HHSearch machine learning tools. The system distributes workload across a mini-cluster of cloud machines to efficiently process a large set of proteins.

The pipeline is designed to be reproducible, fully automated, and features real-time monitoring.

## System Architecture

* **Host Machine:**

  * Manages task distribution via RabbitMQ.
  * Hosts the Prometheus & Grafana monitoring stack.
  * Runs a Web Result Server for convenient data retrieval.
* **Worker Machines:**

  * Execute the pipeline scripts on assigned protein sequences.
  * Run Node Exporter to report performance and task metrics.
* **Message Queue:** RabbitMQ is used to distribute tasks from Host to Workers.
* **Data Storage:** Protein data and results are stored centrally for aggregation and reporting.

## Phase 1: Infrastructure Setup

1. Initialize Terraform:

```bash
terraform init
```

2. Apply Terraform to create machines:

```bash
terraform apply
```

3. After completion, generate `inventory.ini` using `generate_inventory.py` to populate IPs of Host and Workers.

## Phase 2: Environment Configuration (Ansible)

1. Copy SSH private key to Host.
2. Test connectivity from Host to Workers:

```bash
ansible -i inventory.ini workers -m ping
```

3. Run the Ansible playbook. This will install dependencies, Python, S4Pred, HH-suite, setup the Monitoring Stack (Prometheus/Grafana), and deploy the Web Server:

```bash
ansible -i inventory.ini playbook.yml
```

4. Verify that S4Pred weights and HH-suite database have been downloaded and compiled.

## Phase 3: Distributed Execution

### Producer (Host)

* Sends protein sequences to RabbitMQ queue.
* Run the producer script on Host:

```bash
python3 producer.py
```

* Input files:
* `experiment_ids.txt` (list of protein IDs)
* `UP000000589_10090.fasta` (protein sequences)

### Consumer (Workers)

* Pull tasks from RabbitMQ and run pipeline on each sequence.
* Run the consumer script on each Worker (supports real-time metric updates):

```bash
python3 consumer.py
```

### Monitoring & Visualization

The system provides a real-time dashboard to track cluster health and progress.

* **Grafana Dashboard:**

  * **Access:** `http://localhost:3000`
  * **Setup:** To view the custom dashboard, login to Grafana and **import the `Grafana.json` file** included in this repository.
  * **Credentials:** Default login is `admin` / `admin`.
    * *To reset the password, run the following command on the Host terminal:*
      ```bash
      sudo grafana-cli admin reset-admin-password admin
      ```
  * **Metrics:**
    * **Worker CPU Usage:** Visualizes load distribution across the cluster.
    * **Analysis Progress:** Tracks the number of completed protein sequences.
    * **Cluster Health:** Status indicators for all worker nodes.
    * **Total Mission Status:** A counter showing "Completed" vs. "Remaining" tasks, calculated dynamically using PromQL.

* **Command Line Monitoring:**

```bash
# Check running consumers
ansible -i inventory.ini workers -m shell -a "ps -ef | grep consumer.py | grep -v grep"

# Check RabbitMQ queue
sudo rabbitmqctl list_queues name messages_ready messages_unacknowledged

# Check real-time logs
ansible -i inventory.ini workers -m shell -a "tail -n 5 /home/almalinux/consumer.log"
```

## Phase 4: Post-processing & Results

### Aggregation

* After all tasks complete, aggregate results using:

```bash
python3 create_final_report.py
```

* This script generates:

  * `final_hits_output.csv`: protein IDs and best HHSearch hits
  * `final_profile_output.csv`: average STD and Geometric mean for results
  * `missing_ids.txt`: list of IDs not processed successfully

### Web Server (Download)

* A lightweight web server runs on the Host to allow direct CSV download via browser.
* **Access:** `http://localhost:5000`
* **Note:** Ensure Port 5000 is forwarded if working remotely.

## File List

* `playbook.yml`: Ansible playbook for full stack setup
* `producer.py`: Sends protein sequences to RabbitMQ
* `consumer.py`: Worker script to process sequences with custom metrics logic
* `pipeline_script.py`: Executes the S4Pred and HHSearch pipeline
* `results_parser.py`: Parses HHSearch output
* `create_final_report.py`: Aggregates results into CSV files
* `select_ids.py`: Utility to select a subset of protein IDs
* `.gitignore`: Prevents large datasets and temporary files from being uploaded to git
* `result_server.py`: Flask application for serving results via HTTP
* `Grafana.json`: Exported Grafana dashboard configuration for reproducibility


## Usage Summary

1. Provision cloud machines with Terraform.
2. Configure environment with Ansible.
3. Upload input FASTA and ID files to Host.
4. Run `producer.py` on Host.
5. Run `consumer.py` on Workers.
6. Monitor progress via Grafana Dashboard (Port 3000).
7. After completion, run `create_final_report.py`.
8. Download results via Web Server (Port 5000).

