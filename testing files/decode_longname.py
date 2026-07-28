import struct, zlib, os

def decode_xor(data_bytes):
    return ''.join(chr(b ^ 0xFF) if 0x20 <= (b ^ 0xFF) <= 0x7E else '.' for b in data_bytes)

rows = []
for f in sorted(os.listdir('.')):
    if not f.endswith(('.lqm', '.lqc')):
        continue
    if f.startswith('modified'):
        continue
    with open(f, 'rb') as fh:
        data = fh.read()
    name_bytes = bytes(data[0x0208:0x0214])
    display_name = decode_xor(name_bytes).rstrip('.')
    pre_a = struct.unpack('<I', data[0x200:0x204])[0]
    file_id = struct.unpack('<I', data[0:4])[0]
    rows.append((f, data, file_id, pre_a, name_bytes, display_name))

print('=== LONG NAME / DESCRIPTION at 0x03DC ===')
print('(decoding XOR 0xFF, stopping at heavy padding)')
print()
for f, data, file_id, pre_a, name_bytes, display_name in rows:
    region = data[0x03DC:0x03DC + 50]
    decoded = decode_xor(region)
    # find where meaningful text ends
    stripped = decoded.rstrip('.')
    print(f'  {display_name!r:<18} -> {stripped!r}')

print()

# Now test: is pre_a a checksum of the long name at 0x03DC?
# First, find the actual length of the long name (stop at 0xDF padding)
def get_long_name(data, start=0x03DC):
    end = start
    while end < start + 64 and data[end] != 0xDF:
        end += 1
    # Include trailing DFs up to where non-DF content ends + padding
    while end < start + 64 and data[end] == 0xDF:
        end += 1
    return data[start:end]

print('=== Long name as raw bytes ===')
long_names = []
for f, data, file_id, pre_a, name_bytes, display_name in rows:
    # The long name starts at 0x03DC; find its run
    # Detect by first byte: if it's DF (space), name starts from the next non-DF
    region = data[0x03DC:0x03DC + 48]
    # Find the string: all non-DF, then trailing DFs
    i = 0
    while i < len(region) and region[i] == 0xDF:
        i += 1  # skip leading spaces
    j = i
    while j < len(region) and region[j] != 0xDF:
        j += 1  # find end of text
    long_name_bytes = region[i:j]
    decoded = decode_xor(long_name_bytes)
    long_names.append((f, long_name_bytes, decoded, pre_a, file_id))
    print(f'  {display_name!r:<18}: {" ".join(f"{b:02X}" for b in long_name_bytes)!r:<50}  -> {decoded!r}')

print()
print('=== Testing if pre_a = CRC32(long name bytes at 0x03DC) ===')
for f, long_name_bytes, decoded, pre_a, file_id in long_names:
    crc = zlib.crc32(long_name_bytes) & 0xFFFFFFFF
    m = 'YES' if crc == pre_a else 'no '
    print(f'  {m}  {decoded!r:<25}  expect=0x{pre_a:08X}  got=0x{crc:08X}')

print()
# Try full 0x03DC block including leading/trailing DFs
print('=== Testing if pre_a = CRC32(full 0x03DC region fixed 32 bytes) ===')
for f, data, file_id, pre_a, name_bytes, display_name in rows:
    region = data[0x03DC:0x03DC + 32]
    crc = zlib.crc32(region) & 0xFFFFFFFF
    m = 'YES' if crc == pre_a else 'no '
    print(f'  {m}  {display_name!r:<18}  expect=0x{pre_a:08X}  got=0x{crc:08X}')

print()
# Try: find where 0x03DC region ends exactly (at fixed length?)
print('=== Lengths and boundaries of the description region ===')
for f, data, file_id, pre_a, name_bytes, display_name in rows:
    # Find start and end of non-FF or non-DF region around 0x03DC
    # Start: last 0xFF before 0x03DC
    start = 0x03DC
    while start > 0x03D0 and data[start-1] != 0xFF:
        start -= 1
    # End: first 0xFF after the region
    end = 0x03DC
    while end < 0x0420 and data[end] != 0xFF:
        end += 1
    region = data[start:end]
    decoded = decode_xor(region).rstrip('.')
    print(f'  {display_name!r:<18}: start=0x{start:04X} end=0x{end:04X} len={end-start}  decoded={decoded!r}')
