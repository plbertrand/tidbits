#!/bin/bash
buildah bud --pull --layers -t plbertrand/lotus-build-deps:latest -f Dockerfile.deps --build-arg BRANCH="release/v1.20.0" .
