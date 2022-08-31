FROM docker.io/golang:1.17.9-buster
LABEL maintainer="Pierre-Luc Bertrand <bertrand.pierreluc@gmail.com>"
LABEL version="0.1"
LABEL description="Docker image to build Lotus"

# branch or tag of the lotus version to build
ARG BRANCH
ARG NETWORK

RUN echo "Building lotus from branch $BRANCH in network $NETWORK"

RUN apt-get update -y && \
    apt-get install sudo cron git mesa-opencl-icd gcc bzr jq pkg-config clang libhwloc-dev ocl-icd-opencl-dev build-essential hwloc -y && \
    apt-get clean

ENV CGO_CFLAGS="-D__BLST_PORTABLE__"
ENV RUSTFLAGS="-C target-cpu=native -g"
ENV FFI_BUILD_FROM_SOURCE=1


# ENV FIL_PROOFS_USE_MULTICORE_SDR=1
# ENV FIL_PROOFS_MULTICORE_SDR_PRODUCERS=3

# ENV FFI_USE_CUDA=1
# ENV BELLMAN_CUSTOM_GPU="NVIDIA GeForce RTX 3090 Ti:10752"
# ENV FIL_PROOFS_USE_GPU_TREE_BUILDER=1
# ENV FIL_PROOFS_USE_GPU_COLUMN_BUILDER=1 


RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN git clone https://github.com/filecoin-project/lotus.git --depth 1 --branch $BRANCH && \
    cd lotus && \
    git submodule update --init --recursive && \
    make -j 16 clean && \
    make -j 16 deps && \
    make -j 16 $NETWORK lotus lotus-worker lotus-miner lotus-bench lotus-shed lotus-gateway && \
    install -C ./lotus /usr/local/bin/lotus && \
    install -C ./lotus-worker /usr/local/bin/lotus-worker && \
    install -C ./lotus-miner /usr/local/bin/lotus-miner && \
    install -C ./lotus-bench /usr/local/bin/lotus-bench && \
    install -C ./lotus-shed /usr/local/bin/lotus-shed && \
    install -C ./lotus-gateway /usr/local/bin/lotus-gateway
