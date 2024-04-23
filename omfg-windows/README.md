# OMFG Windows

This is notes for myself to fix Windows 10 when moving from AHCI to Intel RST Raid.

## Make a backup of the disk

dd ...

Using rclone was quite neat to copy the disk to GDrive.

## Create the RAID disk

CTRL-I you know the drill.

## (Optional) Set safeboot in msconfig.exe to have the right Storage Controller drivers

This is optional but much nicer than having to boot into Windows repair disk and issuing these commands (thanks to https://blog.workinghardinit.work/2018/11/28/moving-from-ahci-to-raid/)

```
bcdedit /set {default} safeboot minimal

# reboot

bcdedit /deletevalue {default} safeboot
```

## Rebuilding bcdboot

Rebuild the whole efi partition (generally first partition and 100MB). Thanks to https://www.reddit.com/r/WindowsHelp/comments/wjtyhf/bootrec_rebuildbcd_the_requested_system_device/

Steps in DiskPart:
```
select disk 1
sel part 3
assign letter c
select part 4
del part override
sel part 1
format fs=fat32 quick label=Boot
assign letter s
exit
```

Edit BCD:
```
bcdboot c:\windows /s S: /f UEFI
```

### If you like the hard way

You can build the whole efi partition manually:
```
mkdir G:\EFI\Microsoft\Boot

xcopy /s C:\Windows\Boot\EFI\*.* G:\EFI\Microsoft\Boot
```

Rebuild the Boot Configuration Data (BCD) entry in Window Boot Manager:
```
g:
cd EFI\Microsoft\Boot
bcdedit /createstore BCD
bcdedit /store BCD /create {bootmgr} /d “Windows Boot Manager”
bcdedit /store BCD /create /d “My Windows 10” /application osloader
```

The command returns the GUID of the created BCD entry. Use this GUID instead of {your_guid} in the following command:
```
bcdedit /store BCD /set {bootmgr} default {your_guid}
bcdedit /store BCD /set {bootmgr} path \EFI\Microsoft\Boot\bootmgfw.efi
bcdedit /store BCD /set {bootmgr} displayorder {default}
```

The following bcdedit commands are run in the {default} context:
```
bcdedit /store BCD /set {default} device partition=c:
bcdedit /store BCD /set {default} osdevice partition=c:
bcdedit /store BCD /set {default} path \Windows\System32\winload.efi
bcdedit /store BCD /set {default} systemroot \Windows
```
