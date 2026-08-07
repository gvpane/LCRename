import struct, zlib, os

def decode_xor(b):
    return ''.join(chr(x ^ 0xFF) if 0x20 <= (x ^ 0xFF) <= 0x7E else '.' for x in b)

rows = []
for f in sorted(os.listdir('.')):
    if not f.endswith(('.lqm', '.lqc')):
        continue
    if f.startswith('modified'):
        continue
    with open(f, 'rb') as fh:
        data = fh.read()
    name12 = bytes(data[0x0208:0x0214])
    desc32 = bytes(data[0x03DC:0x03FC])
    pre_a = struct.unpack('<I', data[0x200:0x204])[0]
    pre_b = bytes(data[0x204:0x208])
    file_id = struct.unpack('<I', data[0:4])[0]
    display = decode_xor(name12).rstrip('.')
    desc_str = decode_xor(desc32).rstrip('.')
    rows.append((f, data, file_id, pre_a, pre_b, name12, desc32, display, desc_str))

# Test: pre_a = CRC32 of desc32 (32 bytes at 0x03DC)
print('=== Is pre_a = CRC32(desc32 at 0x03DC-0x03FB)? ===')
for f, data, file_id, pre_a, pre_b, name12, desc32, display, desc_str in rows:
    crc = zlib.crc32(desc32) & 0xFFFFFFFF
    m = 'YES' if crc == pre_a else 'no '
    print(f'  {m}  {display!r:<18}  expect=0x{pre_a:08X}  got=0x{crc:08X}')

print()

# Test: pre_a = CRC32(name12 + desc32) = CRC32 of 44 bytes
print('=== Is pre_a = CRC32(name12 + desc32)? ===')
for f, data, file_id, pre_a, pre_b, name12, desc32, display, desc_str in rows:
    combined = name12 + desc32
    crc = zlib.crc32(combined) & 0xFFFFFFFF
    m = 'YES' if crc == pre_a else 'no '
    print(f'  {m}  {display!r:<18}  expect=0x{pre_a:08X}  got=0x{crc:08X}')

print()

# Test: pre_a = CRC32(0x0208-0x03FB) = name + zero block + desc
print('=== Is pre_a = CRC32(0x0208-0x03FB)? ===')
for f, data, file_id, pre_a, pre_b, name12, desc32, display, desc_str in rows:
    block = data[0x0208:0x03FC]
    crc = zlib.crc32(block) & 0xFFFFFFFF
    m = 'YES' if crc == pre_a else 'no '
    print(f'  {m}  {display!r:<18}  expect=0x{pre_a:08X}  got=0x{crc:08X}')

print()

# Test: is file_id = CRC32(desc32)?
print('=== Is file_id = CRC32(desc32)? ===')
for f, data, file_id, pre_a, pre_b, name12, desc32, display, desc_str in rows:
    crc = zlib.crc32(desc32) & 0xFFFFFFFF
    m = 'YES' if crc == file_id else 'no '
    print(f'  {m}  {display!r:<18}  expect=0x{file_id:08X}  got=0x{crc:08X}')

print()

# Test: pre_a = CRC32(data from 0x0200 to 0x03FB) -- metadata block
print('=== Is pre_a = CRC32(0x0200-0x03FB with pre_a zeroed)? ===')
for f, data, file_id, pre_a, pre_b, name12, desc32, display, desc_str in rows:
    block = bytearray(data[0x0200:0x03FC])
    block[0:4] = b'\x00\x00\x00\x00'  # zero out pre_a itself
    crc = zlib.crc32(bytes(block)) & 0xFFFFFFFF
    m = 'YES' if crc == pre_a else 'no '
    print(f'  {m}  {display!r:<18}  expect=0x{pre_a:08X}  got=0x{crc:08X}')

print()

# Observe: description at 0x03DC is 32 bytes padded with 0xDF (XOR=space)
# What if pre_a is just a simple polynomial hash used in 1990s-2000s embedded systems?
# Try: djb2 hash
def djb2(data_bytes):
    h = 5381
    for b in data_bytes:
        h = ((h << 5) + h + b) & 0xFFFFFFFF
    return h

print('=== Is pre_a = djb2(name12)? ===')
for f, data, file_id, pre_a, pre_b, name12, desc32, display, desc_str in rows:
    h = djb2(name12)
    m = 'YES' if h == pre_a else 'no '
    print(f'  {m}  {display!r:<18}  expect=0x{pre_a:08X}  got=0x{h:08X}')

print()

print('=== Is pre_a = djb2(desc32)? ===')
for f, data, file_id, pre_a, pre_b, name12, desc32, display, desc_str in rows:
    h = djb2(desc32)
    m = 'YES' if h == pre_a else 'no '
    print(f'  {m}  {display!r:<18}  expect=0x{pre_a:08X}  got=0x{h:08X}')

print()

# Let's print all the decoded data to better see patterns
print('=== Summary of all fields ===')
for f, data, file_id, pre_a, pre_b, name12, desc32, display, desc_str in rows:
    ext = os.path.splitext(f)[1]
    print(f'  {ext}  name={display!r:<15}  desc={desc_str!r:<35}  pre_a=0x{pre_a:08X}  file_id=0x{file_id:08X}')
