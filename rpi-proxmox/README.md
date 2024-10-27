
sudo su -

echo 'rpi-2' > /etc/hostname

Modify /etc/hosts to have ip -> hostname

curl -L https://mirrors.apqa.cn/proxmox/debian/pveport.gpg -o /etc/apt/trusted.gpg.d/pveport.gpg 

echo 'deb [arch=arm64] https://mirrors.apqa.cn/proxmox/debian/pve bookworm port'>/etc/apt/sources.list.d/pveport.list


apt update && apt full-upgrade

reboot

apt install ifupdown2

reboot

apt install proxmox-ve postfix open-iscsi chrony

reboot

echo 'deb [arch=arm64] https://mirrors.apqa.cn/proxmox/debian/pve bookworm ceph-reef' >> /etc/apt/sources.list.d/pveport.list



## Configure ZeroTier

curl -s https://install.zerotier.com | sudo bash

zerotier-cli join ####

Add node to https://my.zerotier.com and assign IP address

zerotier-cli listnetworks | tail -1 | awk '{ print $3"=enp1z0" }' > /var/lib/zerotier-one/devicemap
systemctl restart zerotier-one

cat << EOF >> /etc/network/interfaces

auto vmbr1
iface vmbr1 inet static
        address $(ip -f inet addr show enp1z0  | awk '/inet / {print $2}')
        bridge-ports none
        bridge-stp off
        bridge-fd 0
#zt-br
EOF

reboot

wget https://raw.githubusercontent.com/plbertrand/tidbits/refs/heads/main/rpi-proxmox/zt-vmbr.sh --directory-prefix=/root
wget https://raw.githubusercontent.com/plbertrand/tidbits/refs/heads/main/rpi-proxmox/zt-vmbr.service --directory-prefix=/usr/lib/systemd/system/
wget https://raw.githubusercontent.com/plbertrand/tidbits/refs/heads/main/rpi-proxmox/zt-vmbr.timer --directory-prefix=/usr/lib/systemd/system/

systemctl daemon-reload systemctl enable zt-vmbr.timer

reboot


## Notes

pvecm add IP-ADDRESS-CLUSTER -link0 $(ip -f inet addr show vmbr0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -link1 $(ip -f inet addr show vmbr1 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p')
