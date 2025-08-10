#!/bin/bash
# Run this script on VPN server

WIREGUARD_NAME="wg0"
ALL_MACHINE_SUBNET="10.0.32.0/24"

CLIENT_LIST=(
  "172.32.0.2,10.0.32.31"
)
# The example value of TEAM_LIST variable: 
# (
#   "<WIREGUARD_CLIENT_ADDRESSES1>,<MACHINE_IP1>"
#   "<WIREGUARD_CLIENT_ADDRESSES2>,<MACHINE_IP1>"
#   "<WIREGUARD_CLIENT_ADDRESSES3>,<MACHINE_IP2>"
#   "<WIREGUARD_CLIENT_ADDRESSES4>,<MACHINE_IP2>"
# )

for CLIENT in ${CLIENT_LIST[@]}; do 
  IFS=',' read -r VPN_CLIENT_IP TEAM_SERVER_IP <<< "${CLIENT}" 
  
  # Delete iptables to open the connection to the other machines
  iptables -D FORWARD -i ${WIREGUARD_NAME} -s ${VPN_CLIENT_IP} -d ${ALL_MACHINE_SUBNET} -j DROP
  iptables -D FORWARD -i ${WIREGUARD_NAME} -s ${TEAM_SERVER_IP} -d ${VPN_CLIENT_IP} -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  iptables -D FORWARD -i ${WIREGUARD_NAME} -s ${VPN_CLIENT_IP} -d ${TEAM_SERVER_IP} -j ACCEPT
done

