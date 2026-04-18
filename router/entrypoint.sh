#!/bin/sh
set -eu

iptables -F FORWARD
iptables -P FORWARD DROP
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -i eth0 -o eth1 -p tcp --dport 9000 -j ACCEPT
iptables -A FORWARD -i eth1 -o eth0 -p tcp --dport 9000 -j ACCEPT

exec dnsmasq --keep-in-foreground --log-facility=-
