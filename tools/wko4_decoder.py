#!/usr/bin/env python3
"""WKO4/WKO5 binary file decoder.

Reverse-engineered from PowerKitOSX.framework (ARM64 disassembly).
Decodes .wko4 activity files and .wko5athlete profile files.

Binary format: Custom protobuf-like encoding (PKEncoder/PKDecoder).
- Tags: field_id << 3 | wire_type (same as protobuf)
- Wire types: 0=varint, 1=fixed64, 2=length-delimited(doubles), 3=start_group, 4=end_group, 5=vectorArchive
- Signed integers use zigzag encoding
- Time-series data uses INT32_DELTA storage: zigzag first value + zigzag deltas

PKVectorStorageX fields (field_ids 111-122):
  111: StorageType  enum {0=INT32_DELTA, 1=DOUBLE, 2=FLOAT, 3=STRING}
  112: Count        number of samples
  114: Multiplier   scale factor (default 1.0)
  115: VectorData   nested blob (tag wire5): size_varint + encoded samples
  122: ChangeCount  modification counter
"""

import struct
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


def decode_varint(data: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        result |= (b & 0x7F) << shift
        pos += 1
        shift += 7
        if not (b & 0x80):
            break
    return result, pos


def zigzag_decode(n: int) -> int:
    return (n >> 1) ^ -(n & 1)


# Tag bytes for PKVectorStorageX fields
TAG_STORAGE_TYPE = b'\xf8\x06'   # F111 wire0
TAG_COUNT = b'\x80\x07'          # F112 wire0
TAG_MULTIPLIER = b'\x92\x07'     # F114 wire2
TAG_VECTOR_DATA = b'\x9d\x07'    # F115 wire5
TAG_CHANGE_COUNT = b'\xd0\x07'   # F122 wire0

# Channel header marker (F102 END_GROUP)
TAG_CHANNEL_HEADER = b'\xb4\x06'

# Sentinel for NULL/NA values in INT32 storage
SENTINEL_THRESHOLD = 10_000_000

CHANNEL_NAMES = [
    b'elapsedtime', b'power', b'heartrate', b'cadence',
    b'speed', b'elevation', b'elapseddistance', b'_elevation',
]


@dataclass
class ChannelHeader:
    storage_type: int = 0    # 0=INT32_DELTA, 1=DOUBLE, 2=FLOAT, 3=STRING
    count: int = 0
    multiplier: float = 1.0
    data_offset: int = 0
    blob_size: int = 0


@dataclass
class Channel:
    name: str
    values: list
    count: int
    multiplier: float = 1.0
    null_count: int = 0


@dataclass
class WKO4Activity:
    filename: str
    channels: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


def find_data_channels(data: bytes) -> dict[str, int]:
    """Find channel positions by locating name + b4 06 header pattern."""
    channels = {}
    for name in CHANNEL_NAMES:
        idx = -1
        while True:
            idx = data.find(name, idx + 1)
            if idx == -1:
                break
            after = data[idx + len(name):idx + len(name) + 2]
            if after == TAG_CHANNEL_HEADER:
                channels[name.decode()] = idx
    return channels


def parse_channel_header(data: bytes, channel_offset: int, name_len: int) -> ChannelHeader:
    """Parse PKVectorStorageX fields from channel header."""
    header = ChannelHeader()
    start = channel_offset + name_len
    end = start + 100

    for tag_bytes, attr, parser in [
        (TAG_STORAGE_TYPE, 'storage_type', lambda d, p: decode_varint(d, p)),
        (TAG_COUNT, 'count', lambda d, p: decode_varint(d, p)),
        (TAG_CHANGE_COUNT, None, None),  # skip
    ]:
        idx = data.find(tag_bytes, start, end)
        if idx >= 0 and parser:
            val, _ = parser(data, idx + len(tag_bytes))
            setattr(header, attr, val)

    # Multiplier (double, 8 raw bytes after tag)
    idx = data.find(TAG_MULTIPLIER, start, end)
    if idx >= 0:
        header.multiplier = struct.unpack('<d', data[idx + 2:idx + 10])[0]

    # VectorData blob (varint size + data)
    idx = data.find(TAG_VECTOR_DATA, start, end)
    if idx >= 0:
        blob_size, data_start = decode_varint(data, idx + 2)
        header.data_offset = data_start
        header.blob_size = blob_size

    return header


def decode_int32_delta(data: bytes, offset: int, blob_size: int) -> tuple[list, int]:
    """Decode INT32_DELTA: zigzag first value + zigzag deltas with sentinel handling."""
    end = offset + blob_size
    first_raw, pos = decode_varint(data, offset)
    current = zigzag_decode(first_raw)

    vals = []
    null_count = 0

    if abs(current) > SENTINEL_THRESHOLD:
        vals.append(None)
        null_count += 1
    else:
        vals.append(current)

    while pos < end:
        v, pos = decode_varint(data, pos)
        zz = zigzag_decode(v)
        current += zz

        if abs(current) > SENTINEL_THRESHOLD:
            vals.append(None)
            null_count += 1
        else:
            vals.append(current)

    return vals, null_count


def decode_wko4(filepath: str) -> WKO4Activity:
    """Decode a .wko4 activity file."""
    data = Path(filepath).read_bytes()

    if data[:4] != b'wko4':
        raise ValueError(f"Not a WKO4 file: {filepath}")

    activity = WKO4Activity(filename=Path(filepath).name)

    # Extract metadata strings from header
    for m in re.finditer(rb'[\x20-\x7e]{4,}', data[:1000]):
        text = m.group().decode('ascii', errors='replace')
        if 'T' in text and ':' in text and '-' in text and len(text) == 19:
            activity.metadata['start_time'] = text
        elif not activity.metadata.get('name') and len(text) > 5 and text != 'wko4':
            activity.metadata['name'] = text

    # Decode channels
    channel_positions = find_data_channels(data)

    for name, offset in channel_positions.items():
        if name.startswith('_'):
            continue

        header = parse_channel_header(data, offset, len(name))

        if header.storage_type == 0 and header.data_offset > 0:
            values, null_count = decode_int32_delta(
                data, header.data_offset, header.blob_size
            )

            if header.multiplier != 1.0:
                values = [
                    v * header.multiplier if v is not None else None
                    for v in values
                ]

            activity.channels[name] = Channel(
                name=name,
                values=values,
                count=header.count,
                multiplier=header.multiplier,
                null_count=null_count,
            )

    return activity


def channel_stats(channel: Channel) -> dict:
    """Compute basic statistics for a channel."""
    valid = [v for v in channel.values if v is not None]
    if not valid:
        return {'count': 0}
    return {
        'count': len(channel.values),
        'valid': len(valid),
        'null': channel.null_count,
        'min': min(valid),
        'max': max(valid),
        'avg': sum(valid) / len(valid),
    }


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: wko4_decoder.py <file.wko4> [--json]")
        sys.exit(1)

    filepath = sys.argv[1]
    as_json = '--json' in sys.argv

    activity = decode_wko4(filepath)

    if as_json:
        import json
        out = {
            'filename': activity.filename,
            'metadata': activity.metadata,
            'channels': {},
        }
        for name, ch in activity.channels.items():
            stats = channel_stats(ch)
            out['channels'][name] = {
                'stats': stats,
                'multiplier': ch.multiplier,
                'values': ch.values,
            }
        print(json.dumps(out, indent=2, default=str))
    else:
        print(f"File: {activity.filename}")
        if activity.metadata:
            for k, v in activity.metadata.items():
                print(f"  {k}: {v}")
        print()
        for name, ch in sorted(activity.channels.items()):
            stats = channel_stats(ch)
            print(f"  {name}: {stats.get('count', 0)} samples, "
                  f"avg={stats.get('avg', 0):.1f}, "
                  f"min={stats.get('min', 0)}, max={stats.get('max', 0)}, "
                  f"null={stats.get('null', 0)}")
