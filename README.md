# Network Training Lab

This lab uses Docker Compose to demonstrate five core networking topics in one place:

- `eth0` and `eth1` interfaces
- static routes
- a dedicated routed gateway
- DNS name resolution across subnets
- firewall rules that permit only selected traffic

## Network Diagram

Rendered topology: [topology.svg](/opt/bg/network_demo/docs/topology.svg)
Slide-friendly version: [topology-slide.svg](/opt/bg/network_demo/docs/topology-slide.svg)
Presenter version with numbered callouts: [topology-speaker.svg](/opt/bg/network_demo/docs/topology-speaker.svg)
Training slide deck: [training-slides.html](/opt/bg/network_demo/docs/training-slides.html)
Print-friendly deck: [training-slides-print.html](/opt/bg/network_demo/docs/training-slides-print.html)
Attendee cheat sheet: [cheat-sheet.md](/opt/bg/network_demo/docs/cheat-sheet.md)

## Topology

- `left_arm` on `172.21.0.11/24`
- `right_arm` on `172.21.0.12/24`
- `brain` on `172.20.0.11/24`
- `router` on both networks:
  - `172.21.0.254/24`
  - `172.20.0.254/24`

The two lab subnets are:

- `arm_net`: `172.21.0.0/24`
- `brain_net`: `172.20.0.0/24`

`left_arm` and `right_arm` get a static route for `172.20.0.0/24` through `172.21.0.254`.
`brain` gets a static route for `172.21.0.0/24` through `172.20.0.254`.

The `router` container enables IPv4 forwarding and installs `iptables` rules that:

- allow established traffic
- allow new TCP traffic to port `9000` between the two subnets
- drop other forwarded traffic such as cross-subnet ICMP

DNS is also hosted on `router` by `dnsmasq`, so the lab nodes can resolve:

- `left_arm`
- `right_arm`
- `brain`

## Runtime Behavior

Each application node:

- runs a TCP echo service on port `9000`
- writes `hostname timestamp` to `/data/states.log` once per second
- stores timestamps in UTC
- keeps only the last 60 seconds of entries in the log file

## Start The Lab

```bash
docker compose up --build -d
```

## Inspect Interfaces

```bash
docker compose exec left_arm ip -brief address
docker compose exec brain ip -brief address
docker compose exec router ip -brief address
```

Expected highlights:

- `left_arm` and `right_arm` each have a single `eth0` in `172.21.0.0/24`
- `brain` has a single `eth0` in `172.20.0.0/24`
- `router` has `eth0` in `172.21.0.0/24` and `eth1` in `172.20.0.0/24`

## Inspect Routes And Gateway

```bash
docker compose exec left_arm ip route
docker compose exec brain ip route
docker compose exec left_arm ip route get 172.20.0.11
docker compose exec brain ip route get 172.21.0.11
```

Expected highlights:

- `left_arm` routes `172.20.0.0/24` via `172.21.0.254`
- `brain` routes `172.21.0.0/24` via `172.20.0.254`

## Inspect DNS

```bash
docker compose exec left_arm nslookup brain 172.21.0.254
docker compose exec brain nslookup left_arm 172.20.0.254
```

Expected highlights:

- `brain` resolves to `172.20.0.11`
- `left_arm` resolves to `172.21.0.11`

## Test TCP Connectivity

```bash
docker compose exec left_arm bash -lc 'printf "hello\n" | nc brain 9000'
docker compose exec brain bash -lc 'printf "hello\n" | nc left_arm 9000'
docker compose exec right_arm bash -lc 'printf "hello\n" | nc left_arm 9000'
```

Each command should return the peer hostname and a current UTC timestamp.

## Debugging From Inside Containers

Use `docker compose exec` to open a `bash` shell in any lab container:

```bash
docker compose exec left_arm bash
docker compose exec right_arm bash
docker compose exec brain bash
docker compose exec router bash
```

The images include `bash` and `bash-completion`, so tab completion works for common commands and paths in interactive sessions.
They also include a small `~/.inputrc` for friendlier demos:

- case-insensitive completion
- immediate completion lists for ambiguous matches
- prefix-based history search with Up and Down arrows
- Ctrl-Left and Ctrl-Right word jumps in `bash`
- `set -o vi` enabled by default for interactive Bash editing

Interactive `bash` also includes a few network-oriented aliases:

- `ifaces` -> `ip -brief addr`
- `routes` -> `ip route`
- `ports` -> `ss -lntp`
- `fw` -> `iptables -vnL`
- `dns` -> `cat /etc/resolv.conf`

Installed debugging tools available in every container:

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

It also includes a few task-oriented helpers for demos:

- `check-self` -> show hostname, interfaces, routes, listeners, and DNS
- `check-router` -> verify the lab gateway path and router-hosted DNS
- `check-brain` -> resolve `brain`, show the route, and do a TCP probe to port `9000`
- `sniff-brain` -> run `tcpdump` focused on traffic to `brain`
- `sniff-9000` -> run `tcpdump` focused on TCP port `9000`
- `demo-reset` -> on `router`, zero the `FORWARD` counters for a clean demo start; on nodes, print a local reset reminder and state summary
- `l2-neighbors` -> show ARP neighbors and run `arp-scan` on the local L2 segment; on `router`, you can pass an interface such as `l2-neighbors eth0`

For reachability demos, `fping` is also installed in every container.
For packet capture demos, `tcpdump` is also installed in every container.
For layer-2 neighbor discovery demos, `arp-scan` is also installed in every container.

### 1. Check Interface Configuration

Inside a node container:

```bash
ip addr show
ip -brief addr
```

Focus on:

- `left_arm` and `right_arm` should show `eth0` in `172.21.0.0/24`
- `brain` should show `eth0` in `172.20.0.0/24`

Inside `router`:

```bash
ip addr show
ip -brief addr
```

Focus on:

- `eth0` should be `172.21.0.254`
- `eth1` should be `172.20.0.254`

### 1b. Check Layer-2 Neighbors On arm_net

Inside `left_arm`:

```bash
ip neigh show dev eth0
arping -I eth0 right_arm
arping -I eth0 172.21.0.254
arp-scan --interface=eth0 --localnet
```

Or use the helper:

```bash
l2-neighbors
```

On `router`, you can choose the interface explicitly:

```bash
l2-neighbors eth0
l2-neighbors eth1
```

What to point out:

- `right_arm` and `router` are layer-2 neighbors on `arm_net`
- `brain` is not a layer-2 neighbor on `arm_net`
- `ip neigh` shows the kernel ARP cache
- `arp-scan` actively sweeps the local broadcast domain

### 2. Check Routing

Inside `left_arm`:

```bash
ip route
ip route get 172.20.0.11
```

Inside `brain`:

```bash
ip route
ip route get 172.21.0.11
```

Focus on:

- `left_arm` and `right_arm` should route `172.20.0.0/24` via `172.21.0.254`
- `brain` should route `172.21.0.0/24` via `172.20.0.254`
- the selected next hop proves which gateway is in use for inter-subnet traffic

### 3. Check Name Resolution

Inside `left_arm`:

```bash
cat /etc/resolv.conf
nslookup brain
nslookup right_arm
```

Inside `brain`:

```bash
cat /etc/resolv.conf
nslookup left_arm
```

Focus on:

- arm-side nodes should use `172.21.0.254` as DNS
- `brain` should use `172.20.0.254` as DNS
- successful lookups prove the router DNS is working

### 4. Check Basic Reachability With Ping

Inside `left_arm`:

```bash
ping -c 1 right_arm
ping -c 1 172.21.0.254
ping -c 1 brain
```

Interpretation:

- `ping right_arm` should work because both are on the same subnet
- `ping 172.21.0.254` should work because the router is directly connected
- `ping brain` should fail because cross-subnet ICMP is blocked by the router firewall

### 5. Check TCP Listening Sockets With ss

Inside any node:

```bash
ss -lntp
ss -tn
```

Focus on:

- each node should listen on `0.0.0.0:9000`
- after running an `nc` test, `ss -tn` may briefly show the TCP session

Inside `router`:

```bash
ss -lnup
```

Focus on:

- `dnsmasq` should be listening on UDP port `53`

### 6. Check Firewall Rules With iptables

Inside `router`:

```bash
iptables -vnL FORWARD
iptables -S FORWARD
```

Focus on:

- default FORWARD policy should be `DROP`
- there should be explicit TCP/9000 allow rules between `eth0` and `eth1`
- packet counters increase when you test cross-subnet TCP

Inside a node container:

```bash
iptables -vnL
```

Focus on:

- node containers are not acting as routers in this lab
- the key filtering logic is on `router`

### 6b. Capture Traffic With tcpdump

Inside `router`:

```bash
tcpdump -ni eth0 tcp port 9000
tcpdump -ni eth1 tcp port 9000
```

Inside `left_arm`:

```bash
tcpdump -ni eth0 host brain
```

Then, in another shell, generate traffic:

```bash
printf "hello\n" | nc brain 9000
```

This is useful for showing:

- successful TCP flows to `brain:9000`
- DNS traffic aimed at the router
- missing cross-subnet ICMP replies when the firewall drops them

### 7. Compare A Working And Failing Path

Working same-subnet path from `left_arm`:

```bash
ping -c 1 right_arm
fping -c 1 left_arm right_arm
printf "hello\n" | nc right_arm 9000
```

Working cross-subnet TCP path from `left_arm`:

```bash
printf "hello\n" | nc brain 9000
```

Failing cross-subnet ICMP path from `left_arm`:

```bash
ping -c 1 brain
```

This gives a clean troubleshooting story:

- name resolution works
- the route exists
- the gateway is reachable
- TCP works through the router
- ICMP fails because the firewall policy blocks it

### 8. Recommended Demo Flow

For a live teaching session, this sequence works well:

1. `demo-reset` on `router` for clean firewall counters
2. `check-self` on `left_arm` to show interfaces, routes, listeners, and DNS
3. `l2-neighbors` on `left_arm` to show ARP neighbors on `arm_net`
4. `check-router` on `left_arm` to prove the gateway path and router DNS
5. `ping right_arm` for a working same-subnet check
6. `ping brain` for a failing cross-subnet ICMP check
7. `check-brain` on `left_arm` for a successful cross-subnet TCP check
8. `sniff-9000` on `router` or `sniff-brain` on `left_arm` to show packet flow
9. `iptables -vnL FORWARD` on `router` to explain why TCP passes and ICMP fails

## Inspect Firewall Rules

```bash
docker compose exec router iptables -vnL FORWARD
```

This shows that the router only forwards TCP traffic to port `9000` between the two subnets.

## Demonstrate A Blocked Protocol

Same-subnet ICMP should work:

```bash
docker compose exec left_arm ping -c 1 right_arm
```

Cross-subnet ICMP should be blocked by the router firewall:

```bash
docker compose exec left_arm ping -c 1 brain
```

Cross-subnet TCP on port `9000` should still work:

```bash
docker compose exec left_arm bash -lc 'printf "still works\n" | nc brain 9000'
```

## Inspect The State Logs

```bash
docker compose exec left_arm tail -n 10 /data/states.log
docker compose exec right_arm tail -n 10 /data/states.log
docker compose exec brain tail -n 10 /data/states.log
```

The file should contain roughly the last 60 lines because each node writes one line per second.

## Stop The Lab

```bash
docker compose down -v
```

## Notes

- The Docker bridge gateway for each subnet remains Docker's own bridge IP, typically `.1`.
- The `router` container is the teaching gateway for inter-subnet traffic because the nodes install explicit routes that point to `.254`.
- If your Docker installation rejects underscores in the `hostname` field, switch `left_arm` and `right_arm` to hyphenated hostnames and keep the DNS aliases in `router/dnsmasq.conf`.
