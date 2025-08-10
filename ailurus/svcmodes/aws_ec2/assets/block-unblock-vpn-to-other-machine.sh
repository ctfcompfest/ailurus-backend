# Run this script on VPN server
# This is sample script to allow a team connect only to their machine

ALL_MACHINE_SUBNET="10.0.32.0/24"

VPN_CLIENT_IP="172.32.0.2"
TEAM_SERVER_IP="10.0.32.31"

# Insert iptables to block the connection to other machines
iptables -I FORWARD -i wg0 -s ${VPN_CLIENT_IP} -d ${ALL_MACHINE_SUBNET} -j DROP
iptables -I FORWARD -i wg0 -s ${TEAM_SERVER_IP} -d ${VPN_CLIENT_IP} -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -I FORWARD -i wg0 -s ${VPN_CLIENT_IP} ${TEAM_SERVER_IP} -j ACCEPT

# Delete iptables to open the connection to the other machines
# iptables -D FORWARD -i wg0 -s ${VPN_CLIENT_IP} -d ${ALL_MACHINE_SUBNET} -j DROP
# iptables -D FORWARD -i wg0 -s ${TEAM_SERVER_IP} -d ${VPN_CLIENT_IP} -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
# iptables -D FORWARD -i wg0 -s ${VPN_CLIENT_IP} ${TEAM_SERVER_IP} -j ACCEPT
