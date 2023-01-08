#!/bin/bash
buildah bud --pull --layers -t plbertrand/lotus-build-intel:latest -f Dockerfile.intel --build-arg BRANCH="release/v1.20.0" .
