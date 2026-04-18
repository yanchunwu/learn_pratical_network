#!/bin/sh
set -eu

mkdir -p /data
ip route replace "${PEER_SUBNET}" via "${ROUTER_IP}"

exec python /app/node.py
