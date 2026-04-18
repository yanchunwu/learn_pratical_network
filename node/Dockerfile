FROM python:3.12-alpine

RUN apk add --no-cache \
    arp-scan \
    bash \
    bash-completion \
    bind-tools \
    busybox-extras \
    fping \
    iproute2 \
    iptables \
    tcpdump

WORKDIR /app

COPY node.py /app/node.py
COPY entrypoint.sh /app/entrypoint.sh
COPY bashrc /etc/bash/network-demo.sh
COPY inputrc /root/.inputrc

RUN cp /etc/bash/network-demo.sh /etc/profile.d/network-demo.sh && \
    chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
