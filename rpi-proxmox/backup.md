# Backup disk image

```
proxmox-backup-client backup root.img:/dev/mmcblk0 --repository 192.168.1.74:Proxmox-Backup
```

# Backup files

```
proxmox-backup-client backup root.pxar:/ \
 --include-dev /boot/firmware \
 --include-dev /etc/pve \
 --exclude '/var/log/pve*' \
 --exclude '/var/log/ceph*' \
 --exclude '/var/log/corosync*' \
 --repository 192.168.1.74:Proxmox-Backup \
 --ns fs \
 --change-detection-mode=metadata
```

# Restore disk image

```
proxmox-backup-client restore host/rpi-2/2024-10-27T22:52:28Z root.img - --repository 192.168.1.74:Proxmox-Backup | dd of=/dev/mmcblk1 bs=256M status=progress
```

# Restore to latest files

```
proxmox-backup-client mount --ns fs host/rpi-2/2024-11-03T17:44:52Z root.ppxar /mnt --repository 192.168.1.74:Proxmox-Backup
mount /dev/sde2 /mnt2
mount /dev/sde1 /mnt2/boot/firmware
rsync -avz --info=progress2 --partial --delete /mnt/. /mnt2/.
```
