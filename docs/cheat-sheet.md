# Network Training Lab Cheat Sheet

## Topology

- `left_arm`: `172.21.0.11/24`
- `right_arm`: `172.21.0.12/24`
- `brain`: `172.20.0.11/24`
- `router`:
  - `eth0`: `172.21.0.254/24`
  - `eth1`: `172.20.0.254/24`

Subnets:

- `arm_net`: `172.21.0.0/24`
- `brain_net`: `172.20.0.0/24`

Key route logic:

- `left_arm` and `right_arm`: `172.20.0.0/24 via 172.21.0.254`
- `brain`: `172.21.0.0/24 via 172.20.0.254`

Firewall behavior:

- cross-subnet TCP to port `9000`: allowed
- cross-subnet ICMP: blocked

## Open A Shell

```bash
docker compose exec left_arm bash
docker compose exec right_arm bash
docker compose exec brain bash
docker compose exec router bash
```

## Built-In Shell Helpers

- `ifaces` -> `ip -brief addr`
- `routes` -> `ip route`
- `ports` -> `ss -lntp`
- `fw` -> `iptables -vnL`
- `dns` -> `cat /etc/resolv.conf`
- `check-self` -> hostname, interfaces, routes, listeners, DNS
- `check-router` -> gateway path + router DNS check
- `check-brain` -> DNS + route + TCP probe to `brain:9000`
- `sniff-brain` -> focused `tcpdump` capture for `brain`
- `sniff-9000` -> focused `tcpdump` capture for TCP/9000
- `demo-reset` -> zero router `FORWARD` counters on `router`
- `l2-neighbors` -> ARP cache + `arp-scan` on the local L2 segment

## Installed Tools

- `ping`
- `arping`
- `fping`
- `arp-scan`
- `ip`
- `ss`
- `iptables`
- `tcpdump`
- `nslookup`
- `nc`

## Quick Checks

### 1. Interfaces

```bash
ifaces
```

Expected:

- `left_arm` and `right_arm`: `eth0` in `172.21.0.0/24`
- `brain`: `eth0` in `172.20.0.0/24`
- `router`: `eth0` in `172.21.0.0/24`, `eth1` in `172.20.0.0/24`

### 2. Layer-2 Neighbors On `arm_net`

```bash
ip neigh show dev eth0
arping -I eth0 right_arm
arping -I eth0 172.21.0.254
arp-scan --interface=eth0 --localnet
```

Or:

```bash
l2-neighbors
```

Expected from `left_arm`:

- sees `right_arm`
- sees `router`
- sees Docker bridge endpoint `172.21.0.1`
- does not see `brain` as an L2 neighbor

### 3. Routes

```bash
routes
ip route get 172.20.0.11
```

Expected on `left_arm`:

- `172.20.0.0/24 via 172.21.0.254`

Expected on `brain`:

```bash
routes
ip route get 172.21.0.11
```

- `172.21.0.0/24 via 172.20.0.254`

### 4. DNS

```bash
dns
nslookup brain
nslookup left_arm
```

Expected:

- arm-side containers use `172.21.0.254`
- `brain` uses `172.20.0.254`

### 5. Same-Subnet Reachability

```bash
ping -c 1 right_arm
fping -c 1 left_arm right_arm
printf "hello\n" | nc right_arm 9000
```

Expected:

- all should work from `left_arm`

### 6. Cross-Subnet Reachability

```bash
ping -c 1 brain
printf "hello\n" | nc brain 9000
```

Expected:

- `ping brain`: fails
- TCP to `brain:9000`: works

## Firewall Checks

On `router`:

```bash
demo-reset
fw
iptables -S FORWARD
```

Expected:

- default `FORWARD` policy is `DROP`
- explicit TCP/9000 rules permit traffic between `eth0` and `eth1`

## Packet Capture

On `router`:

```bash
sniff-9000
```

On `left_arm`:

```bash
sniff-brain
```

Then generate traffic:

```bash
printf "hello\n" | nc brain 9000
```

## Best Demo Sequence

1. `demo-reset` on `router`
2. `check-self` on `left_arm`
3. `l2-neighbors` on `left_arm`
4. `check-router` on `left_arm`
5. `ping right_arm`
6. `ping brain`
7. `check-brain`
8. `sniff-9000` on `router`
9. repeat the TCP probe
10. `fw` on `router`

## Mental Model

- layer 2: who is on my segment?
- route: where does the packet go next?
- DNS: what IP should I try?
- transport: does the service answer?
- firewall: what traffic is actually permitted?
