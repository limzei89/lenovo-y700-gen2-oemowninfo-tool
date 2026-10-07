"""Write sn/countrycode with an explicit --write option and readback."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import oemowninfo_get as transport

def make_payload(field, value):
    if field not in ('sn', 'countrycode'):
        raise ValueError('Only sn and countrycode are supported')
    if not value or len(value) > 31 or any(ord(c) < 33 or ord(c) > 126 or c == ',' for c in value):
        raise ValueError('Value must be 1-31 printable ASCII characters, without spaces or commas')
    raw = value.encode('ascii')
    # ABL copies exactly 32 bytes from the value pointer, not strlen(value).
    return ('oemowninfo set ' + field + ',').encode('ascii') + raw + b'\0' * (32 - len(raw))

def read_value(write, read, field):
    infos = transport.exchange(write, read, 'oemowninfo get ' + field)
    if len(infos) != 1 or infos[0] == '\tnull':
        raise RuntimeError('Cannot obtain an unambiguous current value; no write attempted')
    return infos[0]

def main():
    parser = argparse.ArgumentParser(description='Set sn/countrycode; default is an offline preview. Use --write to apply.')
    parser.add_argument('field', choices=('sn', 'countrycode'))
    parser.add_argument('value', help='New value; clear is unavailable because this ABL rejects empty values')
    parser.add_argument('--write', action='store_true', help='Apply the write to the connected bootloader')
    args = parser.parse_args()
    if args.field == 'countrycode' and args.value == 'clear':
        raise ValueError('Cannot clear to 0x00 using this ABL: oemowninfo set rejects an empty value. No USB access or command sent. Writing null or 00000000 would store text, not zero bytes.')
    payload = make_payload(args.field, args.value)
    print(f'Command: oemowninfo set {args.field},{args.value}')
    print(f'Value region: 32 bytes; {32-len(args.value)} trailing zero bytes')
    if not args.write:
        print('PREVIEW ONLY. No USB access or command sent. Add --write to apply.')
        return
    backend = transport.libusb_package.get_libusb1_backend()
    if backend is None:
        raise RuntimeError('Cannot load libusb')
    matches = transport.discover(backend)
    if len(matches) != 1:
        raise RuntimeError(f'Found {len(matches)} fastboot interfaces; connect exactly one device')
    dev, intf, inp, out = matches[0]
    try:
        transport.usb.util.claim_interface(dev, intf.bInterfaceNumber)
        write = lambda p: out.write(p, timeout=5000)
        read = lambda: inp.read(4096, timeout=5000)
        previous = read_value(write, read, args.field)
        print('Current value: ' + previous)
        if previous == args.value:
            print('Already matches. No write performed.')
            return
        backup_dir = Path(__file__).resolve().parent / 'backups'
        backup_dir.mkdir(exist_ok=True)
        now = datetime.now(timezone.utc)
        backup = backup_dir / (now.strftime('%Y%m%dT%H%M%S.%fZ') + '-' + args.field + '.json')
        with backup.open('x', encoding='utf-8') as f:
            json.dump({'utc': now.isoformat(), 'usb_vid': dev.idVendor, 'usb_pid': dev.idProduct,
                       'field': args.field, 'previous_value': previous, 'requested_value': args.value},
                      f, ensure_ascii=False, indent=2)
        print('Previous value saved: ' + str(backup), flush=True)
        print('Writing...', flush=True)
        transport.exchange(write, read, payload)
        current = read_value(write, read, args.field)
        if current != args.value:
            raise RuntimeError(f'Readback mismatch: requested {args.value!r}, got {current!r}. Previous value is saved in {backup}')
        print('VERIFIED: ' + args.field + ' = ' + current)
    finally:
        transport.usb.util.dispose_resources(dev)

if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError, transport.usb.core.USBError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        print('No automatic retry or rollback performed. If writing started, read the field before retrying.', file=sys.stderr)
        sys.exit(1)
