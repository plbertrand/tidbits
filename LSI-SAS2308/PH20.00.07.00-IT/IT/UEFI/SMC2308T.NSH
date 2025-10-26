echo -off
sas2flash.efi -o -e 7
cls
sas2flash.efi -f 2308T207.ROM
sas2flash.efi -b mptsas2.rom
sas2flash.efi -b x64sas2.rom
cls
sas2flash.efi -o -sasaddhi 5003048