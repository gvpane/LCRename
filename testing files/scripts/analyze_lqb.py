import struct, zlib, os

def decode_xor(data_bytes):
    return ''.join(chr(b ^ 0xFF) if 0x20 <= (b ^ 0xFF) <= 0x7E else '.' for b in data_bytes)

lqb_path = r'D:\LQData\V2.0_40PRES&COMPS.lqb'
with open(lqb_path, 'rb') as f:
    lqb = f.read()

size = len(lqb)
print(f'LQB size: {size} bytes (0x{size:X})')
print(f'Divisible by 33280: {size % 33280} remainder ({"yes" if size % 33280 == 0 else "no"})')
print(f'= {size // 33280} full chunks + {size % 33280} bytes')
print()

# Check for magic string occurrences
magic = b'Liquid Channel (tm) file format'
positions = []
pos = 0
while True:
    idx = lqb.find(magic, pos)
    if idx < 0:
        break
    positions.append(idx)
    pos = idx + 1

print(f'Magic string found {len(positions)} times at offsets:')
for p in positions[:10]:
    print(f'  0x{p:08X}  (={p})')
if len(positions) > 10:
    print(f'  ... and {len(positions)-10} more')
print()

# Compute the spacing between magic occurrences
if len(positions) > 1:
    gaps = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
    unique_gaps = set(gaps)
    print(f'Gaps between consecutive magic strings: {unique_gaps}')
    print()

# If gaps are consistent, the bundle is just a sequence of individual files
if len(positions) >= 2:
    chunk_size = positions[1] - positions[0]
    header_offset = positions[0] - 0x000C  # magic starts at 0x000C in each chunk
    print(f'First magic at 0x{positions[0]:08X} -> chunk offset = {header_offset}')
    print(f'Chunk size = {chunk_size} bytes (from magic spacing)')
    print()

# Read first few emulation entries
print('=== First 10 emulations in LQB bundle ===')
# Each entry should start at a fixed offset; let's check starting at 0 or after a bundle header
# First, search for the first name field by looking for XOR'd printable text
for chunk_idx, magic_pos in enumerate(positions[:80]):
    chunk_start = magic_pos - 0x000C
    # Read name at offset 0x0208 relative to chunk start
    name_offset = chunk_start + 0x0208
    if name_offset + 12 > size:
        break
    name_bytes = lqb[name_offset:name_offset + 12]
    decoded = decode_xor(name_bytes).rstrip('.')
    pre_b = lqb[chunk_start + 0x0204:chunk_start + 0x0208]
    ext = '.lqm' if pre_b == b'\xff\xff\xfd\xff' else '.lqc' if pre_b == b'\xfd\xff\xff\xff' else f'[{pre_b.hex()}]'
    long_name_bytes = lqb[chunk_start + 0x03DC:chunk_start + 0x03FC]
    long_decoded = decode_xor(long_name_bytes).rstrip('.')
    print(f'  [{chunk_idx:2d}] offset=0x{chunk_start:08X}  type={ext}  name={decoded!r:<15}  desc={long_decoded!r}')

print()
print('=== Bundle vs individual files: do the name fields match? ===')
# Load all individual files
individual = {}
for fn in sorted(os.listdir(r'D:\LQData')):
    if not fn.endswith(('.lqm', '.lqc')):
        continue
    path = os.path.join(r'D:\LQData', fn)
    with open(path, 'rb') as fh:
        d = fh.read()
    if len(d) != 33280:
        continue
    magic_check = b'Liquid Channel (tm) file format'
    if d[0x000C:0x000C+len(magic_check)] != magic_check:
        continue
    name_b = bytes(d[0x0208:0x0214])
    disp = decode_xor(name_b).rstrip('.')
    individual[disp] = d

# Check each bundle chunk against individual
matched = 0
for chunk_idx, magic_pos in enumerate(positions[:80]):
    chunk_start = magic_pos - 0x000C
    if chunk_start + 33280 > size:
        continue
    bundle_chunk = lqb[chunk_start:chunk_start + 33280]
    name_bytes = bundle_chunk[0x0208:0x0214]
    disp = decode_xor(name_bytes).rstrip('.')

    if disp in individual:
        indiv_chunk = individual[disp]
        # Compare data blocks (skip headers that may differ)
        data_a_match = bundle_chunk[0x0214:0x4208] == indiv_chunk[0x0214:0x4208]
        data_b_match = bundle_chunk[0x4214:] == indiv_chunk[0x4214:]
        if data_a_match and data_b_match:
            print(f'  [{chunk_idx}] {disp!r}: FULL DATA MATCH with individual file')
            matched += 1
        else:
            diff_a = sum(1 for i in range(len(bundle_chunk[0x0214:0x4208])) if bundle_chunk[0x0214+i] != indiv_chunk[0x0214+i])
            print(f'  [{chunk_idx}] {disp!r}: DIFFERS (block_A diffs={diff_a})')
    else:
        print(f'  [{chunk_idx}] {disp!r}: not in individual files')

print(f'\nMatched {matched} / min(80, {len(positions)}) checked')
