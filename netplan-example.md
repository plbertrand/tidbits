# Netplan bonding on motherboard nics and matching other network cards

This is the configuration file that matches based on the driver the netword interfaces. I have 4 gig integrated gig interfaces on the motherboard and a PCI 2x10GbE card. The two uses different drivers. I'm bonding the 4 integrated cards because I don't have a 10GbE switch yet.

```
network:
  version: 2
  renderer: networkd
  ethernets:
    mb_nics:
      match:
        driver: igb
    10g_nics:
      match:
        driver: ixgbe
    #enp10s0f0:
    #  dhcp4: false
    #  dhcp6: false
    #enp10s0f1:
    #  dhcp4: false
    #  dhcp6: false
    #enp10s0f2:
    #  dhcp4: false
    #  dhcp6: false
    #enp10s0f3:
    #  dhcp4: false
    #  dhcp6: false

  bonds:
    bond0:
      dhcp4: false
      dhcp6: false
      interfaces:
        - mb_nics
        #- enp10s0f0
        #- enp10s0f1
        #- enp10s0f2
        #- enp10s0f3
      parameters:
        mode: 802.3ad
        lacp-rate: fast
        mii-monitor-interval: 100
        transmit-hash-policy: layer2+3

  bridges:
    br0:
      dhcp4: true
      interfaces:
        - bond0

```

Don't forget to run:

```
# sudo netplan generate
# sudo netplan apply
```

