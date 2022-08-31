#!/bin/bash
sudo docker build -t plbertrand/lotus-build-cuda:latest -f Dockerfile.cuda --build-arg BRANCH="releases" .
