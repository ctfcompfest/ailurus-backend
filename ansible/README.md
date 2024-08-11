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