#!/usr/bin/env python3

import argparse
import asyncio
import glob
import re
import struct
from binascii import crc32
from pathlib import Path

import serial
from bleak import BleakClient, BleakScanner

SERVICE = "0000fd02-0000-1000-8000-00805f9b34fb"
RX_CHAR = "0000fd02-0001-1000-8000-00805f9b34fb"
TX_CHAR = "0000fd02-0002-1000-8000-00805f9b34fb"

INFO_REQUEST = 0x00
INFO_RESPONSE = 0x01
START_UPLOAD_REQUEST = 0x0C
START_UPLOAD_RESPONSE = 0x0D
TRANSFER_CHUNK_REQUEST = 0x10
TRANSFER_CHUNK_RESPONSE = 0x11
PROGRAM_FLOW_REQUEST = 0x1E
PROGRAM_FLOW_RESPONSE = 0x1F
PROGRAM_FLOW_NOTIFICATION = 0x20
CONSOLE_NOTIFICATION = 0x21
TUNNEL_MESSAGE = 0x32
CLEAR_SLOT_REQUEST = 0x46
CLEAR_SLOT_RESPONSE = 0x47

DELIMITER = 0x02
MAX_BLOCK_SIZE = 84
XOR = 0x03
IMPORT_PATTERN = re.compile(r"^from\s+([\w\d_]+)\s+import\s+\*\s*$")
SLOT_PATTERN = re.compile(
    r"^#\s*LEGO\s+slot:\s*(\d+)(?:\s+autostart)?\s*$",
    re.IGNORECASE,
)


def slot_from_header(path):
    for line in path.read_text(encoding="utf-8").splitlines()[:5]:
        match = SLOT_PATTERN.match(line)
        if match:
            slot = int(match.group(1))
            if slot not in range(20):
                raise ValueError(f"LEGO slot must be between 0 and 19, got {slot}")
            return slot
    return None


def crc(data, seed=0):
    remainder = len(data) % 4
    if remainder:
        data += b"\0" * (4 - remainder)
    return crc32(data, seed)


def encode(data):
    buffer = bytearray()
    code_index = 0
    block = 0

    def begin_block():
        nonlocal code_index, block
        code_index = len(buffer)
        buffer.append(0xFF)
        block = 1

    begin_block()
    for byte in data:
        if byte > DELIMITER:
            buffer.append(byte)
            block += 1
        if byte <= DELIMITER or block > MAX_BLOCK_SIZE:
            if byte <= DELIMITER:
                buffer[code_index] = byte * MAX_BLOCK_SIZE + block + DELIMITER
            begin_block()
    buffer[code_index] = block + DELIMITER
    return buffer


def decode(data):
    buffer = bytearray()

    def unescape(code):
        if code == 0xFF:
            return None, MAX_BLOCK_SIZE + 1
        value, block = divmod(code - DELIMITER, MAX_BLOCK_SIZE)
        if block == 0:
            block = MAX_BLOCK_SIZE
            value -= 1
        return value, block

    value, block = unescape(data[0])
    for byte in data[1:]:
        block -= 1
        if block > 0:
            buffer.append(byte)
            continue
        if value is not None:
            buffer.append(value)
        value, block = unescape(byte)
    return bytes(buffer)


def pack(data):
    encoded = encode(data)
    for index in range(len(encoded)):
        encoded[index] ^= XOR
    encoded.append(DELIMITER)
    return bytes(encoded)


def unpack(frame):
    start = 1 if frame[0] == 0x01 else 0
    unframed = bytes(byte ^ XOR for byte in frame[start:-1])
    return decode(unframed)


def assemble(path, included=None):
    path = path.resolve()
    included = included or set()
    if path in included:
        return ""
    included.add(path)

    output = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = IMPORT_PATTERN.match(line)
        if not match:
            output.append(line)
            continue
        include_path = next(
            (
                parent / f"{match.group(1)}.py"
                for parent in path.parent.parents
                if (parent / f"{match.group(1)}.py").exists()
            ),
            None,
        )
        if include_path is None:
            output.append(line)
            continue
        output.append(assemble(include_path, included))
    return "\n".join(output) + "\n"


class HubConnection:
    def __init__(self, client):
        self.client = client
        self.pending = {}
        self.receive_buffer = bytearray()
        self.max_packet_size = 20
        self.max_chunk_size = 100

    def on_data(self, _, data):
        self.receive_buffer.extend(data)
        while DELIMITER in self.receive_buffer:
            end = self.receive_buffer.index(DELIMITER)
            frame = bytes(self.receive_buffer[: end + 1])
            del self.receive_buffer[: end + 1]
            try:
                message = unpack(frame)
            except Exception as error:
                print(f"Ignored malformed hub message: {error}")
                continue
            message_id = message[0]
            future = self.pending.pop(message_id, None)
            if future and not future.done():
                future.set_result(message)
            elif message_id == CONSOLE_NOTIFICATION:
                print(message[1:].rstrip(b"\0").decode("utf-8", errors="replace"))
            elif message_id not in (PROGRAM_FLOW_NOTIFICATION, TUNNEL_MESSAGE):
                print(f"Ignored hub message 0x{message_id:02x}")

    async def send(self, payload):
        frame = pack(payload)
        for index in range(0, len(frame), self.max_packet_size):
            packet = frame[index : index + self.max_packet_size]
            if isinstance(self.client, serial.Serial):
                await asyncio.to_thread(self.client.write, packet)
            else:
                await self.client.write_gatt_char(RX_CHAR, packet, response=False)

    async def request(self, payload, response_id, timeout=10):
        future = asyncio.get_running_loop().create_future()
        self.pending[response_id] = future
        await self.send(payload)
        try:
            return await asyncio.wait_for(future, timeout)
        finally:
            self.pending.pop(response_id, None)

    async def initialize(self):
        response = await self.request(bytes((INFO_REQUEST,)), INFO_RESPONSE)
        values = struct.unpack("<BBBHBBHHHHH", response)
        self.max_packet_size = values[7]
        self.max_chunk_size = values[9]
        print(
            f"Connected: firmware {values[4]}.{values[5]}.{values[6]}, "
            f"RPC {values[1]}.{values[2]}.{values[3]}"
        )

    async def clear_slot(self, slot):
        response = await self.request(
            struct.pack("<BB", CLEAR_SLOT_REQUEST, slot),
            CLEAR_SLOT_RESPONSE,
        )
        if response[1] != 0:
            print("Slot was already empty or could not be cleared; continuing.")

    async def upload(self, program, slot):
        response = await self.request(
            struct.pack(
                "<B11sBI",
                START_UPLOAD_REQUEST,
                b"program.py\0",
                slot,
                crc(program),
            ),
            START_UPLOAD_RESPONSE,
        )
        if response[1] != 0:
            raise RuntimeError("Hub rejected the file upload")

        running_crc = 0
        for index in range(0, len(program), self.max_chunk_size):
            chunk = program[index : index + self.max_chunk_size]
            running_crc = crc(chunk, running_crc)
            response = await self.request(
                struct.pack(
                    f"<BIH{len(chunk)}s",
                    TRANSFER_CHUNK_REQUEST,
                    running_crc,
                    len(chunk),
                    chunk,
                ),
                TRANSFER_CHUNK_RESPONSE,
            )
            if response[1] != 0:
                raise RuntimeError(f"Hub rejected upload chunk at byte {index}")
            print(f"Uploaded {min(index + len(chunk), len(program))}/{len(program)} bytes")

    async def start(self, slot):
        response = await self.request(
            struct.pack("<BBB", PROGRAM_FLOW_REQUEST, 0, slot),
            PROGRAM_FLOW_RESPONSE,
        )
        if response[1] != 0:
            raise RuntimeError(f"Hub rejected start request for slot {slot}")


async def transfer_program(connection, program, slot, start):
    await connection.initialize()
    await connection.clear_slot(slot)
    await connection.upload(program, slot)
    print(f"Upload to slot {slot} complete.")
    if start:
        await connection.start(slot)
        print(f"Started slot {slot}.")
        await asyncio.sleep(2)


async def clear_slots(connection, slots):
    await connection.initialize()
    for slot in slots:
        await connection.clear_slot(slot)
        print(f"Cleared slot {slot}.")


async def upload_bluetooth(program, slot, start):
    print("Scanning for a SPIKE Prime hub. Press its Bluetooth button if needed.")
    device = await BleakScanner.find_device_by_filter(
        lambda _, advertisement: SERVICE.lower() in advertisement.service_uuids,
        timeout=15,
    )
    if device is None:
        raise RuntimeError("No SPIKE Prime hub found over Bluetooth")

    async with BleakClient(device) as client:
        connection = HubConnection(client)
        await client.start_notify(TX_CHAR, connection.on_data)
        await transfer_program(connection, program, slot, start)


async def clear_bluetooth_slots(slots):
    print("Scanning for a SPIKE Prime hub. Press its Bluetooth button if needed.")
    device = await BleakScanner.find_device_by_filter(
        lambda _, advertisement: SERVICE.lower() in advertisement.service_uuids,
        timeout=15,
    )
    if device is None:
        raise RuntimeError("No SPIKE Prime hub found over Bluetooth")

    async with BleakClient(device) as client:
        connection = HubConnection(client)
        await client.start_notify(TX_CHAR, connection.on_data)
        await clear_slots(connection, slots)


def open_usb(port=None):
    if port is None:
        ports = sorted(glob.glob("/dev/cu.usbmodem*"))
        if not ports:
            raise RuntimeError("No SPIKE Prime USB serial port found")
        port = ports[0]
    elif not Path(port).exists():
        raise RuntimeError(f"USB serial port not found: {port}")

    print(f"Opening {port}")
    try:
        return serial.Serial(port, baudrate=115200, timeout=0.1)
    except serial.SerialException as error:
        raise RuntimeError(
            "USB port is busy. Disconnect the LEGO Hub extension, then retry."
        ) from error


async def upload_usb(program, slot, start, port=None):
    client = open_usb(port)

    connection = HubConnection(client)

    async def receive():
        while client.is_open:
            data = await asyncio.to_thread(client.read_until, bytes((DELIMITER,)))
            if data:
                connection.on_data(None, data)

    receiver = asyncio.create_task(receive())
    try:
        await transfer_program(connection, program, slot, start)
    finally:
        client.close()
        receiver.cancel()
        try:
            await receiver
        except asyncio.CancelledError:
            pass


async def clear_usb_slots(slots, port=None):
    client = open_usb(port)
    connection = HubConnection(client)

    async def receive():
        while client.is_open:
            data = await asyncio.to_thread(client.read_until, bytes((DELIMITER,)))
            if data:
                connection.on_data(None, data)

    receiver = asyncio.create_task(receive())
    try:
        await clear_slots(connection, slots)
    finally:
        client.close()
        receiver.cancel()
        try:
            await receiver
        except asyncio.CancelledError:
            pass


async def upload_program(path, slot, start, transport, port):
    program = assemble(path).encode("utf-8")
    print(f"Prepared {len(program)} bytes from {path.name}")
    if transport == "usb":
        await upload_usb(program, slot, start, port)
    else:
        await upload_bluetooth(program, slot, start)


def main():
    parser = argparse.ArgumentParser(description="Upload Python to a SPIKE Prime HubOS3 hub")
    parser.add_argument("file", type=Path, nargs="?")
    parser.add_argument("--slot", type=int, choices=range(20))
    parser.add_argument("--clear-slot", type=int, action="append", choices=range(20))
    parser.add_argument("--clear-all", action="store_true")
    parser.add_argument("--no-start", action="store_true")
    parser.add_argument("--transport", choices=("usb", "bluetooth"), default="usb")
    parser.add_argument("--port")
    args = parser.parse_args()

    slots_to_clear = list(range(20)) if args.clear_all else args.clear_slot
    if slots_to_clear:
        clear_operation = clear_usb_slots if args.transport == "usb" else clear_bluetooth_slots
        if args.transport == "usb":
            asyncio.run(clear_operation(slots_to_clear, args.port))
        else:
            asyncio.run(clear_operation(slots_to_clear))
        return

    if args.file is None:
        parser.error("file is required unless --clear-slot or --clear-all is used")
    slot = args.slot
    if slot is None:
        slot = slot_from_header(args.file)
        if slot is None:
            slot = 0
        else:
            print(f"Using slot {slot} from {args.file.name}")
    asyncio.run(
        upload_program(
            args.file,
            slot,
            not args.no_start,
            args.transport,
            args.port,
        )
    )


if __name__ == "__main__":
    main()
