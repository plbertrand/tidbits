#!/bin/bash
podman stop timemachine
podman rm timemachine
podman-compose up -d

