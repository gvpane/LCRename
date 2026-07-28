import struct, zlib, os

rows = []
for f in sorted(os.listdir('.')):
    if not f.endswith(('.lqm', '.lqc')):
        continue
    if f.startswith('modified'):
        continue
    with open(f, 'rb') as fh:
        data = fh.read()
    name_bytes = bytes(data[0x0208:0x0214])
    decoded = ''.join(chr(b ^ 0xFF) if 0x20 <= (b ^ 0xFF) <= 0x7E else '.' for b in name_bytes).rstrip('.')
    pre_a = struct.unpack('<I', data[0x200:0x204])[0]
    pre_b = data[0x204:0x208]
    file_id = struct.unpack('<I', data[0:4])[0]
    rows.append((f, data, file_id, pre_a, pre_b, name_bytes, decoded))

# KEY FINDING: 0x0204 = file type tag
# .lqm preamps:   FF FF FD FF  -> bytes [FF, FF, FD, FF]
# .lqc compressors: FD FF FF FF -> bytes [FD, FF, FF, FF]
# Same bytes, different order — clearly a type discriminator

print('=== FILE TYPE TAG at 0x0204 ===')
for f, data, file_id, pre_a, pre_b, name_bytes, decoded in rows:
    ext = os.path.splitext(f)[1]
    print(f'  {ext}  {pre_b.hex()}  {decoded}')

print()

# Test: is pre_a the CRC32 of the data blocks using type-dependent seed?
# .lqm pre_b = FFFFFDFF = 0xFFFFFDFF = 4294836223
# .lqc pre_b = FDFFFFFF = 0xFDFFFFFF = 4244635647
print('=== Is pre_a = CRC32(data_block_A, seed=pre_b_as_int)? ===')
for f, data, file_id, pre_a, pre_b, name_bytes, decoded in rows:
    seed = struct.unpack('<I', pre_b)[0]
    block = data[0x0214:0x4208]
    crc = zlib.crc32(block, seed) & 0xFFFFFFFF
    m = 'YES' if crc == pre_a else 'no '
    print(f'  {m}  {decoded:<15}  expect=0x{pre_a:08X}  got=0x{crc:08X}')

print()

# Test: is pre_a CRC32(name_bytes, seed=pre_b_as_int)?
print('=== Is pre_a = CRC32(name_bytes, seed=pre_b_as_int)? ===')
for f, data, file_id, pre_a, pre_b, name_bytes, decoded in rows:
    seed = struct.unpack('<I', pre_b)[0]
    crc = zlib.crc32(name_bytes, seed) & 0xFFFFFFFF
    m = 'YES' if crc == pre_a else 'no '
    print(f'  {m}  {decoded:<15}  expect=0x{pre_a:08X}  got=0x{crc:08X}')

print()

# Test: is file_id CRC32(whole file from 0x0004, zeroing 0x0200-0x0207)?
print('=== Is file_id = CRC32(file[0x0004:] with 0x0200-0x0207 zeroed)? ===')
for f, data, file_id, pre_a, pre_b, name_bytes, decoded in rows:
    patched = bytearray(data[0x0004:])
    # Adjust offsets: 0x0200 - 0x0004 = 0x01FC, 0x0208 - 0x0004 = 0x0204
    patched[0x01FC:0x0204] = b'\x00' * 8
    crc = zlib.crc32(bytes(patched)) & 0xFFFFFFFF
    m = 'YES' if crc == file_id else 'no '
    print(f'  {m}  {decoded:<15}  expect=0x{file_id:08X}  got=0x{crc:08X}')

print()

# Test: name bytes embedded in data block? Search for name in 0x0214-0x4207
print('=== Name bytes appearing in data blocks? ===')
for f, data, file_id, pre_a, pre_b, name_bytes, decoded in rows:
    # Find positions of each name byte (excluding padding 0xDF)
    non_pad = [(i, name_bytes[i]) for i in range(12) if name_bytes[i] != 0xDF]
    # Check if they appear consecutively in data block
    found = []
    for off in range(0x0214, 0x4200):
        if data[off] == non_pad[0][1] if non_pad else False:
            # check sequence
            seq = [data[off + j] for j in range(min(6, len(non_pad)))]
            expected = [b for _, b in non_pad[:6]]
            if seq == expected:
                found.append(f'0x{off:04X}')
    print(f'  {decoded:<15}  {found if found else "not found"}')

print()

# Print raw bytes at 0x0218-0x021F (just after name block start) for each file
print('=== Bytes at 0x0214-0x0220 (start of data block A) ===')
for f, data, file_id, pre_a, pre_b, name_bytes, decoded in rows:
    hex_vals = ' '.join(f'{data[i]:02X}' for i in range(0x0214, 0x0222))
    print(f'  {decoded:<15}  {hex_vals}')

print()
# Zoom on the name region to check if data block is a name echo
print('=== Raw name bytes vs data at the small non-FF region (0x03DC-0x03FF) ===')
for f, data, file_id, pre_a, pre_b, name_bytes, decoded in rows:
    region = ' '.join(f'{data[i]:02X}' for i in range(0x03DC, 0x03FC))
    name_hex = ' '.join(f'{b:02X}' for b in name_bytes)
    print(f'  {decoded:<15}')
    print(f'    name:     {name_hex}')
    print(f'    0x03DC:   {region}')
