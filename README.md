# Introduction
This repository contains all necessary automation to create a VM-based lab setup to host the [Kafka-enabled version](https://github.com/nksegos/unipi-ais) of the [UniPi AIS Stream Visualization application](https://www.datastories.org/univ-piraeus-ais-stream-visualization/) along with a complete backend consisting, by default, 
of single Kafka broker, a PostgreSQL database, a data production node and a Redis database for caching.

It additionally provides automation for the creation of a synthetic dataset(based on the [Piraeus AIS Dataset for Large-scale Maritime Data Analytics](https://zenodo.org/records/6323416#.YnDqkC8RrAA) for real-time traffic simulation along with latency benchmarking for record transmission via Kafka vs Database.

# Prerequisites
The entirety of the automation is supposed to work with Debian-based hosts, both for the controller node and for the target VMs. As such it is required that it is run on Debian-based systems.

The VMs created by the `vm-lifecycle` role depend on a pre-existing KVM virsh network(by default [it's set to the 'default' one](roles/vm-lifecycle/vars/main.yml#L10). Ideally the network should be based on network bridge, but should support other configuarations as well. This needs to be done in advance by the user.

Additionally, if you plan on using the VM provisioning functionality, you should update the `vm_image_store` variable in [roles/vm-lifecycle/vars/main.yml](roles/vm-lifecycle/vars/main.yml#L8) to a valid path.

Prior using the roles and playbooks, it is needed to uncomment, edit and rename the vaulted stub files [roles/vm-lifecycle/vars/main-vault.stub.yml](roles/vm-lifecycle/vars/main-vault.stub.yml) and [roles/database/vars/database-access-vault.stub.yml](roles/database/vars/database-access-vault.stub.yml) to set your 
secrets and ideally use `ansible-vault` on them to protect said secrets. If using Ansible vault, make sure to update [ansible.cfg](ansible.cfg) with your vault password file location for easy execution.

# Quickstart

By following the commands below, you'll be able to set up from a scratch 4 virtual machines with 1 vCPU, 2G of RAM and 20G of disk space each and deploy on them the updated application along with its Redis-based cache stack, a kafka broker with Kafka Connect configured, a PostgreSQL database node and a data production node.
if you don't modify the naming convention for the VMs, nothing needs changing. Additionally, in playbooks lacking a `--limit` directive, host targeting is done via the dynamically generated and assigned role system on the inventory.

```bash
# Create 4 VMs
ansible-playbook playbooks/create-vms.yml -e vm_disk='20G' -e vm_count=4 --ask-become-pass 
# These retrieve the Piraeus AIS Dataset and build a synthetic one by blending kinematic and static data,
# but take a lot of time and storage space, you can skip them as 3 sample enriched datasets are already present in the repo
ansible-playbook playbooks/retrieve-dataset.yml 
ansible-playbook playbooks/prepare-dataset.yml
# Create the PostgreSQL database and seed the utility table, optionally include the benchmarking schema
ansible-playbook playbooks/deploy-database.yml (-e include_benchmark_ddl=true) --limit t3
# Create the Kafka broker and configure Kafka Connect, optionally with support for the benchmarking schema
ansible-playbook playbooks/deploy-kafka-broker.yml --limit t2
ansible-playbook playbooks/deploy-kafka-connect.yml (-e include_benchmark_connectors=true) --limit t2
# Deploy data production node
ansible-playbook playbooks/deploy-producer.yml --limit t1
# Deploy the visualization application along with its cache stack
ansible-playbook playbooks/deploy-consumer.yml --limit t4
# Start the application, should be live in http:// t4 : 6969/unipi-ais/unipi-ais
ansible-playbook playbooks/start-consumer-application.yml --limit t4
# Start simulating live AIS traffic, the visualizer should pick this up immediately
ansible-playbook playbooks/start-kafka-producer.yml 
```

For further control over the data flow processes, the following playbooks can be used:
```bash
# When executed in this order, they will result in a complete reset of the data flow, allowing to restart data production afterwards
# with no conflicts. NOTE: A refresh on visualization page is necessary to re-subsribe to Kafka after the recycling of the topics
ansible-playbook playbooks/stop-kafka-producer.yml 
ansible-playbook playbooks/flush-topics.yml 
ansible-playbook playbooks/flush-database.yml 
ansible-playbook playbooks/flush-application-cache.yml 
```
