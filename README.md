# Distributed Protein Structure Prediction Pipeline

## Overview

This repository contains a distributed data analysis system for predicting protein structures using the S4Pred and HHSearch machine learning tools. The system distributes workload across a mini-cluster of cloud machines to efficiently process a large set of proteins.

The pipeline is designed to be reproducible and fully automated.

## System Architecture

* **Host Machine:** Manages task distribution via RabbitMQ and runs the producer script.
* **Worker Machines:** Execute the pipeline scripts on assigned protein sequences, running S4Pred and HHSearch.
* **Message Queue:** RabbitMQ is used to distribute tasks from Host to Workers.
* **Data Storage:** Protein data and results are stored centrally for aggregation and reporting.

## Phase 1: Infrastructure Setup

### Prerequisites

* WSL (Ubuntu) or any Linux environment
* Terraform installed
* Access credentials for your cloud provider (Harvester)

### Steps

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

### Prerequisites

* SSH access from your local machine to the Host
* Ansible installed on the Host

### Steps

1. Copy your SSH private key to Host.
2. Test connectivity from Host to Workers:

   ```bash
   ansible -i inventory.ini workers -m ping
   ```
3. Run the Ansible playbook to install dependencies, Python, S4Pred, HH-suite, and pipeline scripts:

   ```bash
   ansible-playbook -i inventory.ini playbook.yml
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
* Run the consumer script on each Worker:

  ```bash
  python3 consumer.py
  ```

### Monitoring

* Use the following commands on Host to monitor progress:

  ```bash
  # Check running consumers
  ansible -i inventory.ini workers -m shell -a "ps -ef | grep consumer.py | grep -v grep"

  # Check RabbitMQ queue
  sudo rabbitmqctl list_queues name messages_ready messages_unacknowledged

  # Check recent logs
  ansible -i inventory.ini workers -m shell -a "tail -n 5 /home/almalinux/consumer.log"
  ```
* Optional: Use Netdata or Grafana for visual monitoring.

## Post-processing

* After all tasks complete, aggregate results using:

  ```bash
  python3 create_final_report.py
  ```
* This script generates:

  * `final_hits_output.csv`: protein IDs and best HHSearch hits
  * `final_profile_output.csv`: average STD and Geometric mean for results
  * `missing_ids.txt`: list of IDs not processed successfully

## File Structure

* `playbook.yml`: Ansible playbook for Host and Worker setup
* `producer.py`: Sends protein sequences to RabbitMQ
* `consumer.py`: Worker script to process sequences
* `pipeline_script.py`: Executes the S4Pred and HHSearch pipeline
* `results_parser.py`: Parses HHSearch output
* `create_final_report.py`: Aggregates results into CSV files
* `select_ids.py`: Utility to select a subset of protein IDs
* `.gitignore`: Prevents large datasets and temporary files from being uploaded to git

## Dependencies

### Python Packages

* biopython
* torch
* numpy
* scipy
* pika

### External Tools

* S4Pred: [https://github.com/psipred/s4pred](https://github.com/psipred/s4pred)
* HH-suite: [https://github.com/soedinglab/hh-suite](https://github.com/soedinglab/hh-suite)

### Databases

* PDB70 for HHSearch: `pdb70_from_mmcif_latest.tar.gz`
* Mouse proteome FASTA: `UP000000589_10090.fasta`
* Protein ID list: `experiment_ids.txt`

## Usage Summary

1. Provision cloud machines with Terraform.
2. Configure environment with Ansible.
3. Upload input FASTA and ID files to Host.
4. Run `producer.py` on Host.
5. Run `consumer.py` on Workers.
6. Monitor progress and queue.
7. After completion, run `create_final_report.py` to generate results.

## Notes

* Ensure RabbitMQ port (5672) is open in firewall.
* Host machine is intended for orchestration only; Workers perform the computation.
* System is scalable to additional Workers or different protein datasets by updating inventory and input files.
