
check the connected USB port. The mesg shows the converter pl2303 is attached to /dev/ttyUSB0
```
BASH > `dmesg | tail`
# output mesg
# [18152.671049] pl2303 ttyUSB0: pl2303 converter now disconnected from ttyUSB0
# [18152.671057] pl2303 1-1:1.0: device disconnected
# [18179.736826] usb 1-2: new full-speed USB device number 7 using xhci_hcd
# [18179.863789] usb 1-2: New USB device found, idVendor=067b, idProduct=2303, bcdDevice= 3.00
# [18179.863791] usb 1-2: New USB device strings: Mfr=1, Product=2, SerialNumber=0
# [18179.863792] usb 1-2: Product: USB-Serial Controller
# [18179.863793] usb 1-2: Manufacturer: Prolific Technology Inc.
# [18179.865202] pl2303 1-2:1.0: pl2303 converter detected
# [18179.865887] usb 1-2: pl2303 converter now attached to ttyUSB0
```

stty -F /dev/ttyUSB0 9600 cs8 -cstopb -parenb -crtscts # set communication mode in 9600 8N1N
echo -n ':OUTPut1:STATeON' > /dev/ttyUSB0  # send command but no any response found.
cat < /dev/ttyUSB0 # ideally it received some message.
