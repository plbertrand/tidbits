#!/bin/bash
buildah bud --pull --layers -t plbertrand/lotus-build-intel:latest -f Dockerfile.intel --build-arg BRANCH="v1.17.1" .
