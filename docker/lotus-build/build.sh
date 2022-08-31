#!/bin/bash
buildah bud --layers -t plbertrand/lotus-build:latest --build-arg BRANCH="release/v1.17.1" --build-arg NETWORK=lotus .
