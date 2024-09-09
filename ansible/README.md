# Ailurus Ansible Playbook

## How to use
1. Make sure you have [ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) installed in your computer and python3 on each target machine.
2. Copy `config-example` to `config`, then update all the configuration files.
3. Copy `inventory-example` to `inventory`, then update it with your target machine credentials.
4. You can choose command from the available playbook.

## Available Playbook
### 1. Deploy VPN Server and Generate Client Profile
This playbook will deploy an [Wireguard VPN server](https://www.wireguard.com/) and mask all the traffic that going through the tunnel. The target machine should have public IP address. This playbook will look into all target machine under the `vpn` section inside the `inventory` and use `wireguard.yml` configuration format.

- To install the VPN server and generate a client profile, you can use the following command.
    ```bash
    ansible-playbook playbooks/vpn-setup.yml -e @config/wireguard.yml
    ```

    The client profile will be placed in the `wireguard-result` directory. The VPN server are automatically run after the installation.

- To terminate the VPN server, you can use the following command.
    ```bash
    ansible-playbook playbooks/vpn-terminate.yml -e @config/wireguard.yml
    ```

- To run the VPN server, you can use the following command.
    ```bash
    ansible-playbook playbooks/vpn-run.yml -e @config/wireguard.yml
    ```

- To generate more client profiles, you can use the following command.
    ```bash
    ansible-playbook playbooks/vpn-useradd.yml -e @config/wireguard.yml
    ```

### 2. Deploy Ailurus Backend (Webapp and Keeper)
This playbook will deploy the database, redis, rabbitmq, also ailurus webapp and keeper. This playbook will look into all target machine under the `backend` section inside the `inventory` and use `ailurus.yml` configuration format.

- To deploy all surrounding service (i.e. database, redis, rabbitmq), webapp, and keeper.
    ```bash
    ansible-playbook playbooks/backend-setup.yml -e @config/ailurus.yml
    ```

- To only run the webapp and keeper (without rebuild the image).
    ```bash
    ansible-playbook playbooks/backend-run.yml -e @config/ailurus.yml
    ```

- To terminate the webapp and keeper.
    ```bash
    ansible-playbook playbooks/backend-terminate.yml -e @config/ailurus.yml
    ```

### 3. Deploy Ailurus Backend (Worker)
This playbook will deploy ailurus frontend. This playbook will look into all target machine under the `worker` section inside the `inventory` and use `ailurus.yml` configuration format.

#### Notes
1. Make sure `host.backend` section inside the `ailurus.yml` can be accessed from the worker instance later.
2. This playbook will use the first entry from `[backend]` section inside the `inventory` to connect to the database and rabbitmq. Make sure it is accessible from the worker instance.
3. You need to modify `num_worker` attribute on each `[worker]` entry to specify number of workers inside the respective target machine.

#### Playbook

- To build the image and deploy the worker.
    ```bash
    ansible-playbook playbooks/worker-setup.yml -e @config/ailurus.yml
    ```

- To only run the worker (without rebuild the image).
    ```bash
    ansible-playbook playbooks/worker-run.yml -e @config/ailurus.yml
    ```

- To terminate the worker.
    ```bash
    ansible-playbook playbooks/worker-terminate.yml -e @config/ailurus.yml
    ```

### 4. Deploy Ailurus Frontend
This playbook will deploy ailurus frontend. This playbook will look into all target machine under the `frontend` section inside the `inventory` and use `ailurus.yml` configuration format.

> Make sure `host` section inside the yaml configuration are configured properly.

- To rebuild image and run the frontend.
    ```bash
    ansible-playbook playbooks/frontend-setup.yml -e @config/ailurus.yml
    ```

- To run the frontend (without rebuild the image).
    ```bash
    ansible-playbook playbooks/frontend-run.yml -e @config/ailurus.yml
    ```

- To terminate the frontend.
    ```bash
    ansible-playbook playbooks/frontend-terminate.yml -e @config/ailurus.yml
    ```