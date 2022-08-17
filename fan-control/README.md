# Control fans on H11DSi-NT v2

## Control CPU zone (FAN1-8)
`ipmitool raw 0x30 0x70 0x66 0x01 0x00 0x10`

## Control peripheral zone (FANA-B)
`ipmitool raw 0x30 0x70 0x66 0x01 0x01 0x10`

## When nothing works and the fans are crazy

`ipmitool mc reset cold`
