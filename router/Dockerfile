FROM alpine:3.20

RUN apk add --no-cache \
    arp-scan \
    bash \
    bash-completion \
    bind-tools \
    busybox-extras \
    dnsmasq \
    fping \
    iproute2 \
    iptables \
    tcpdump

COPY dnsmasq.conf /etc/dnsmasq.conf
COPY entrypoint.sh /router/entrypoint.sh
COPY bashrc /etc/bash/network-demo.sh
COPY inputrc /root/.inputrc

RUN cp /etc/bash/network-demo.sh /etc/profile.d/network-demo.sh && \
    chmod +x /router/entrypoint.sh

CMD ["/router/entrypoint.sh"]
