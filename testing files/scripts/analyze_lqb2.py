import struct, zlib, os

def decode_xor(b):
    return ''.join(chr(x ^ 0xFF) if 0x20 <= (x ^ 0xFF) <= 0x7E else '.' for x in b)

lqb_path = r'D:\LQData\V2.0_40PRES&COMPS.lqb'
with open(lqb_path, 'rb') as f:
    lqb = f.read()

size = len(lqb)
print(f'LQB size: {size} bytes = 0x{size:X}')
print()

# The LQB has one magic at 0x000C -- that means 0x0000-0x000B is its own header
# Let's dump the full header region
print('=== LQB header (0x0000-0x01FF) ===')
print(f'  [0x0000-0x0003]: {" ".join(f"{lqb[i]:02X}" for i in range(4))}  = uint32-LE {struct.unpack_from("<I", lqb, 0)[0]}')
print(f'  [0x0004-0x0007]: {" ".join(f"{lqb[i]:02X}" for i in range(4,8))}')
print(f'  [0x0008-0x000B]: {" ".join(f"{lqb[i]:02X}" for i in range(8,12))}  = uint32-LE {struct.unpack_from("<I", lqb, 8)[0]}')
magic_end = lqb.index(b'\x00', 0x000C)
print(f'  [0x000C-0x{magic_end:04X}]: "{lqb[0x000C:magic_end].decode("ascii")}"')
print()

# Find all non-zero bytes in 0x0066-0x01FF (after copyright)
nonzero = [(i, lqb[i]) for i in range(0x66, 0x200) if lqb[i] != 0]
print(f'Non-zero bytes in 0x0066-0x01FF: {[(f"0x{o:04X}", f"0x{v:02X}") for o, v in nonzero]}')
print()

# Pre-name region 0x0200-0x0213
print(f'  [0x0200-0x0203]: {" ".join(f"{lqb[0x200+i]:02X}" for i in range(4))}')
print(f'  [0x0204-0x0207]: {" ".join(f"{lqb[0x204+i]:02X}" for i in range(4))}')
raw_name = lqb[0x0208:0x0214]
print(f'  [0x0208-0x0213]: name={" ".join(f"{b:02X}" for b in raw_name)} -> "{decode_xor(raw_name).rstrip(".")}"')
print()

# After the name, what comes?
# In individual files, 0x0214-0x4207 is data block A
# Let's search for what's at key offsets
print('=== LQB data at offsets matching individual file structure ===')
for off in [0x0214, 0x0250, 0x03DC, 0x4208, 0x4214]:
    raw = lqb[off:off+16]
    decoded = decode_xor(raw)
    print(f'  [0x{off:04X}]: {" ".join(f"{b:02X}" for b in raw)}  -> "{decoded.rstrip(".")}"')

print()

# The LQB might have a directory/index followed by data
# Let's search for all XOR'd name-like strings throughout the file
# A valid XOR-encoded name would have: multiple bytes where (b^0xFF) is printable ASCII
def looks_like_xor_name(data_slice, min_len=4):
    decoded = [chr(b ^ 0xFF) for b in data_slice]
    printable = sum(1 for c in decoded if 0x20 <= ord(c) <= 0x7E)
    return printable >= min_len

print('=== Scanning LQB for XOR-encoded name strings (32-byte windows with >20 printable) ===')
hits = []
for i in range(0, size - 32, 4):
    window = lqb[i:i+32]
    decoded = ''.join(chr(b ^ 0xFF) if 0x20 <= (b ^ 0xFF) <= 0x7E else '.' for b in window)
    # Count non-dot (printable after XOR)
    printable = decoded.count('.')
    non_dot = 32 - printable
    if non_dot >= 20:
        stripped = decoded.rstrip('.')
        hits.append((i, stripped))

print(f'Found {len(hits)} candidate name strings')
print()
print('First 40:')
for off, s in hits[:40]:
    print(f'  0x{off:08X}: {s!r}')

print()
if len(hits) > 40:
    spacing = [hits[i+1][0] - hits[i][0] for i in range(min(20, len(hits)-1))]
    print(f'Gaps between first 20 hits: {spacing}')
