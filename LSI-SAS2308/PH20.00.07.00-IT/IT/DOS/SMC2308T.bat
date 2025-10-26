@echo off
sas2flsh -o -e 7
cls
sas2flsh -f 2308T207.ROM
sas2flsh -b mptsas2.rom
sas2flsh -b x64sas2.rom
cls
sas2flsh -o -sasaddhi 5003048

