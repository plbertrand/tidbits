# Flash LSI SAS2308 from IR (Integrated RAID) to IT (Initiator Target)

Flashing that card was not a walk in the park. After the working solution section, my attempts are described starting with EFI Shell, followed by FreeDOS then the working solution.

## Working Solution

**I've put all the files I've used in this repository for myself but please don't trust me.**

1. Download `Shell_Full.efi` from [Tianocore](https://github.com/tianocore/edk2/tree/UDK2010.SR1/EdkShellBinPkg/FullShell/X64).
2. Download `PH20.00.07.00-IT.zip` from [Wayback Machine Supermicro](https://web.archive.org/web/20191126110710/https://www.supermicro.com/wftp/driver/SAS/LSI/2308/Firmware/IT/PH20.00.07.00-IT.zip)
4. Create a thumbdrive using Rufus. Select `UEFI:NTFS` as boot selection, `GPT` partition scheme, `UEFI` as target system, `exFAT` as file system and do set `Create extended label and icon files`.
5. Unzip all the content at the root of this newly created drive.
6. Rename `Shell_Full.efi` to `Shell.efi`.
7. Restart and enter BIOS.
8. On my Asus Z97 (MAXIMUS VII FORMULA), go to `Exit` tab and select `Launch EFI Shell from USB drives`.
9. In the shell, type `fs0:`
10. If you are going from IR to IT, you must first erase the firmware: `sas2flash.efi -o -e 6`
11. **DO NOT REBOOT**
12. Flash the new firmware and BIOS: `sas2flash.efi -o -f 2308T207.ROM -b mptsas2.rom`


## Attempt #1

1. Same as the working solution except use the latest release of Tianocore `Shell.efi`
2. Receive error: `InitShellApp: Application not started from Shell`

## Attempt #2

1. Format your thumbdrive with `FreeDOS` using Rufus.
2. Copy the DOS content from `PH20.00.07.00-IT.zip`.
3. Boot into FreeDOS
4. Run `sasflsh.exe -o -f 2308T207.ROM`
5. Receive error: `ERROR: Failed to initialize PAL. Exiting Program.`

## Credits

- [bsodmike](https://forum.level1techs.com/t/asus-uefi-friendly-efi-usb-no-luck-flashing-lsi9211-8i-hba-from-ir-to-it/126344/4) [Github](https://github.com/bsodmike/s5clouds8-lsi9211-8i-IR-to-IT-EFI-bootable-usb)
- [aronchick](https://serverfault.com/a/679176)

