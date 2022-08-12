FROM ubuntu:20.04
LABEL maintainer="bertrand.pierreluc@gmail.com"
LABEL version="0.1"
LABEL description="Docker image for Lotus miner"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update

RUN apt install -y git curl vim net-tools gpg ca-certificates wget inetutils-*

RUN curl -s 'https://install.zerotier.com' | bash
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | bash -s -- -y
RUN wget --progress=bar:force:noscroll -c https://golang.org/dl/go1.17.9.linux-amd64.tar.gz -O - | tar -xz -C /usr/local

RUN ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime
RUN apt install -y mesa-opencl-icd ocl-icd-opencl-dev gcc git bzr jq pkg-config curl clang build-essential hwloc libhwloc-dev wget
RUN dpkg-reconfigure --frontend noninteractive tzdata

RUN apt upgrade -y
RUN apt clean

RUN git clone https://github.com/filecoin-project/lotus.git /lotus

VOLUME ["/var/lib/zerotier-one/networks.d", "/snapshot"]

ENV PATH="${PATH}:/usr/local/go/bin:/root/.cargo/bin"
COPY start.sh /start.sh
CMD ["/start.sh"]

