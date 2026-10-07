"""Read-only client for the analyzed Lenovo ABL oemowninfo get handler."""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'dependencies'))
import usb.core
import usb.util
import libusb_package

FIELDS = ('sn', 'psn', 'skuid', 'fingerprint', 'countrycode', 'btmac',
          'wifimac', 'usbdebugflag', 'vibcalil', 'vibcalir', 'displayid')

def exchange(write, read, command):
    payload = command.encode('ascii') if isinstance(command, str) else command
    if write(payload) != len(payload):
        raise RuntimeError('Incomplete USB command write')
    deadline = time.monotonic() + 30
    infos = []
    while time.monotonic() < deadline:
        packet = bytes(read())
        if not packet:
            continue
        status, value = packet[:4], packet[4:].rstrip(b'\0').decode('utf-8', 'replace')
        if status == b'INFO':
            infos.append(value)
            print('(bootloader) ' + value)
        elif status == b'TEXT':
            print(value, end='')
        elif status == b'OKAY':
            print('OKAY' + (' ' + value if value else ''))
            return infos
        elif status == b'FAIL':
            raise RuntimeError('Device returned FAIL: ' + value)
        else:
            raise RuntimeError('Unexpected fastboot response: ' + repr(packet))
    raise RuntimeError('Timed out waiting for final fastboot response')

def discover(backend):
    matches = []
    for dev in usb.core.find(find_all=True, backend=backend):
        try:
            for cfg in dev:
                for intf in cfg:
                    if (intf.bInterfaceClass, intf.bInterfaceSubClass,
                        intf.bInterfaceProtocol) != (0xff, 0x42, 0x03):
                        continue
                    endpoints = [e for e in intf if usb.util.endpoint_type(e.bmAttributes) == 2]
                    inp = next((e for e in endpoints if usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN), None)
                    out = next((e for e in endpoints if usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT), None)
                    if inp is not None and out is not None:
                        matches.append((dev, intf, inp, out))
        except usb.core.USBError:
            continue
    return matches

def main():
    parser = argparse.ArgumentParser(description='Send only oemowninfo get queries; no flash/erase/set commands.')
    parser.add_argument('field', nargs='?', choices=FIELDS)
    parser.add_argument('--list', action='store_true', help='List USB interfaces without sending a command')
    args = parser.parse_args()
    if not args.field and not args.list:
        parser.error('Specify a field, for example sn, or --list')
    backend = libusb_package.get_libusb1_backend()
    if backend is None:
        raise RuntimeError('Cannot load the bundled libusb library')
    matches = discover(backend)
    if args.list:
        for dev, intf, _, _ in matches:
            print(f'Fastboot USB {dev.idVendor:04x}:{dev.idProduct:04x} bus={dev.bus} address={dev.address} interface={intf.bInterfaceNumber}')
        print(f'{len(matches)} fastboot interface(s) found. No command sent.')
        return
    if len(matches) != 1:
        raise RuntimeError(f'Found {len(matches)} fastboot interfaces. Connect exactly one device in bootloader fastboot mode.')
    dev, intf, inp, out = matches[0]
    try:
        # Existing configuration and alternate setting are retained.
        usb.util.claim_interface(dev, intf.bInterfaceNumber)
        print(f'Sending: oemowninfo get {args.field}', flush=True)
        exchange(lambda data: out.write(data, timeout=5000),
                 lambda: inp.read(4096, timeout=5000),
                 'oemowninfo get ' + args.field)
    finally:
        usb.util.dispose_resources(dev)

if __name__ == '__main__':
    try:
        main()
    except (usb.core.USBError, RuntimeError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        print('Use bootloader fastboot mode and close other USB tools. No driver replacement is performed.', file=sys.stderr)
        sys.exit(1)
