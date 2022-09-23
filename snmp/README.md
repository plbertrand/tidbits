# SuperMicro IPMI BMC SNMP configuration for DataDog

## Find SNMP OID for temperatures, fans and voltages

Find first part of OID to search everything:

```
snmpwalk -v3 -l authPriv -u plb -a SHA -A "HelloHello01" -x AES -X "WorldWorld01" 192.168.2.175
```

My prefix for every output is `1.3.6.1.4.1`:
```
snmpwalk -v3 -l authPriv -u plb -a SHA -A "HelloHello01" -x AES -X "WorldWorld01" 192.168.2.175 1.3.6.1.4.1 | grep FAN0
# iso.3.6.1.4.1.21317.1.3.1.13.30 = STRING: "FAN1"
```

## DataDog configuration:

```
    metrics:
      - MIB: ATEN-IPMI-MIB
        table:
          OID: 1.3.6.1.4.1.21317.1.3
          name: smHealthMonitorTable
        symbols:
          - OID: 1.3.6.1.4.1.21317.1.3.1.2
            name: smHealthMonitorReading
        metric_tags:
          - tag: sensor
            column:
              OID: 1.3.6.1.4.1.21317.1.3.1.13
              name: smHealthMonitorIndex
```

