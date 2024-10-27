#!/bin/sh

#zerotier-cli listnetworks | grep '200' | awk '!/nwid/ {print $3}'
nwid=db64858fedd65586
vmbr=vmbr1

zerotier-cli listnetworks | if grep $nwid >/dev/null
then
echo "ZT OK";
else
echo "ZT NOT OK";
systemctl start zerotier-one.service
sleep 10
fi

dev=$(zerotier-cli listnetworks | grep '200' | awk '!/dev/ {print $8}')
brctl show | if grep $dev >/dev/null
then
echo "brctl OK";
else
echo "brctl NOT OK";
brctl addif $vmbr $dev
ip link set $dev up
fi

