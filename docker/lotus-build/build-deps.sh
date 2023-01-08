#!/bin/bash
sudo docker build --pull -t plbertrand/lotus-build-deps:latest -f Dockerfile.deps --build-arg BRANCH="release/v1.20.0" .
