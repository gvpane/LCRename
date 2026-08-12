import struct, os

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
    file_id = struct.unpack('<I', data[0:4])[0]
    display = decode_xor(name12).rstrip('.')
    desc_str = decode_xor(desc32).rstrip('.')
    rows.append((f, data, file_id, pre_a, name12, desc32, display, desc_str))

# Try CRC-32C (Castagnoli) - used in iSCSI, ext4, etc.
try:
    import crcmod
    crc32c_fn = crcmod.predefined.mkCrcFun('crc-32c')

    print('=== Is pre_a = CRC32C(data block A)? ===')
    for f, data, file_id, pre_a, name12, desc32, display, desc_str in rows:
        block = data[0x0214:0x4208]
        crc = crc32c_fn(block)
        m = 'YES' if crc == pre_a else 'no '
        print(f'  {m}  {display!r:<18}  expect=0x{pre_a:08X}  got=0x{crc:08X}')

    print()
    print('=== Is pre_a = CRC32C(name12)? ===')
    for f, data, file_id, pre_a, name12, desc32, display, desc_str in rows:
        crc = crc32c_fn(name12)
        m = 'YES' if crc == pre_a else 'no '
        print(f'  {m}  {display!r:<18}  expect=0x{pre_a:08X}  got=0x{crc:08X}')
except ImportError:
    print('crcmod not available, skipping CRC32C')

print()

# Try CRC-16 / CCITT families stored as 32-bit
import zlib

def crc16_ccitt(data, poly=0x1021, init=0xFFFF):
    crc = init
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
        crc &= 0xFFFF
    return crc

print('=== Is low 16 bits of pre_a = CRC16-CCITT(name12)? ===')
for f, data, file_id, pre_a, name12, desc32, display, desc_str in rows:
    crc = crc16_ccitt(name12)
    low16 = pre_a & 0xFFFF
    m = 'YES' if crc == low16 else 'no '
    print(f'  {m}  {display!r:<18}  expect=0x{low16:04X}  got=0x{crc:04X}')

print()

# Key question: is this even a checksum at all?
# Let's examine what changes when content is very similar (COPY CAT 2 vs COPY CAT 3)
print('=== Comparing similar pairs: pre_a and description ===')
print()
for i in range(len(rows)):
    for j in range(i+1, len(rows)):
        fi, datai, idi, prea_i, n12i, d32i, disp_i, desc_i = rows[i]
        fj, dataj, idj, prea_j, n12j, d32j, disp_j, desc_j = rows[j]
        # Find files with similar names
        if desc_i[:10] == desc_j[:10]:
            xor_prea = prea_i ^ prea_j
            xor_id   = idi ^ idj
            xor_n12  = bytes(a ^ b for a, b in zip(n12i, n12j))
            xor_d32  = bytes(a ^ b for a, b in zip(d32i, d32j))
            # How much of the data block differs?
            diff_block = sum(1 for a, b in zip(datai[0x0214:0x4208], dataj[0x0214:0x4208]) if a != b)
            print(f'  {disp_i!r:<15} vs {disp_j!r:<15}')
            print(f'    pre_a XOR: 0x{xor_prea:08X}')
            print(f'    file_id XOR: 0x{xor_id:08X}')
            print(f'    name XOR: {xor_n12.hex()}')
            print(f'    desc XOR: {xor_d32.hex()}')
            print(f'    data block A diffs: {diff_block} bytes out of {0x4208-0x0214}')
            print()

# Check: maybe pre_a IS the CRC32 of data block A but we calculated the range wrong
# Let's try every possible start/end within reasonable bounds
print('=== Brute-force: find range where CRC32 matches pre_a ===')
import zlib
for f, data, file_id, pre_a, name12, desc32, display, desc_str in rows[:2]:
    print(f'  Checking {display!r}:')
    # Try all start offsets from 0x0200 to 0x0400, end from start+16 to 0x4300
    found = False
    for start in range(0x0200, 0x0400, 4):
        for end in range(start + 16, min(start + 0x4200, len(data)), 4):
            crc = zlib.crc32(data[start:end]) & 0xFFFFFFFF
            if crc == pre_a:
                print(f'    MATCH! CRC32(data[0x{start:04X}:0x{end:04X}]) = 0x{pre_a:08X}')
                found = True
    if not found:
        print('    No matching range found in tested bounds')
    print()
