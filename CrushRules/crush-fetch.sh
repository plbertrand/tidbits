#!/bin/bash

ceph osd getcrushmap > crush.map.bin
crushtool -d crush.map.bin -o crush.map.txt
