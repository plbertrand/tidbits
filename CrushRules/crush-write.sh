#!/bin/bash

crushtool -c crush.map.txt -o crush2.map.bin
ceph osd setcrushmap -i crush2.map.bin
