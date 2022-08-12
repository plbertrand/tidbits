#!/bin/bash

echo "build lotus"
cd /lotus
git checkout releases

export RUST_LOG=debug
export RUSTFLAGS="-C target-cpu=native -g"
export FFI_BUILD_FROM_SOURCE=1
export FFI_USE_MULTICORE_SDR=1

export CGO_CFLAGS_ALLOW="-D__BLST_PORTABLE__"
export CGO_CFLAGS="-D__BLST_PORTABLE__"

# export FFI_USE_CUDA=1
export FFI_USE_CUDA=0
# export BELLMAN_CUSTOM_GPU="NVIDIA GeForce GTX 680:1536"
# export BELLMAN_CUSTOM_GPU="GeForce GTX 680:1536"
# export BELLMAN_CUSTOM_GPU="NVIDIA GeForce RTX 3090 Ti:10752"

export FIL_PROOFS_USE_MULTICORE_SDR=1
export FIL_PROOFS_MULTICORE_SDR_PRODUCERS=3
# export FIL_PROOFS_USE_GPU_TREE_BUILDER=1
# export FIL_PROOFS_USE_GPU_COLUMN_BUILDER=1 

make -j 16 deps
make -j 16 calibnet lotus-bench
make install

mkdir /snapshot
cd /snapshot
curl -sI https://fil-chain-snapshots-fallback.s3.amazonaws.com/mainnet/minimal_finality_stateroots_latest.car | perl -ne '/x-amz-website-redirect-location:\s(.+)\.car/ && print "$1.sha256sum\n$1.car"' | xargs wget

echo "Done!"
