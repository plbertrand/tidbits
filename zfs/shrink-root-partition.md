# Great post

https://aaronlauterer.com/blog/2021/proxmox-ve-migrate-to-smaller-root-disks/


# Recreate ESP partition:

```
proxmox-boot-tool format /dev/sda2
proxmox-boot-tool init /dev/sda2
proxmox-boot-tool clean
proxmox-boot-tool refresh
