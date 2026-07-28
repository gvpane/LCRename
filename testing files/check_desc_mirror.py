import struct, os

def decode_xor(b):
    return ''.join(chr(x ^ 0xFF) if 0x20 <= (x ^ 0xFF) <= 0x7E else '.' for x in b)

# Check if data block B mirrors block A exactly (specifically the description field)
f = 'original FF ISA 110.lqm'
with open(f, 'rb') as fh:
    data = fh.read()

print(f'=== Checking block A vs block B mirror for {f} ===')
print()

# Description at 0x03DC (relative to block A start 0x0214 = offset 0x01C8 into block)
# If block B starts at 0x4214, same relative offset = 0x43DC
desc_a = data[0x03DC:0x03FC]
desc_b = data[0x43DC:0x43FC]
name_a = data[0x0208:0x0214]
name_b = data[0x4208:0x4214]

print(f'  Name A (0x0208): {decode_xor(name_a).rstrip(".")!r}')
print(f'  Name B (0x4208): {decode_xor(name_b).rstrip(".")!r}')
print(f'  Name A == Name B: {name_a == name_b}')
print()
print(f'  Desc A (0x03DC): {decode_xor(desc_a).rstrip(".")!r}')
print(f'  Desc B (0x43DC): {decode_xor(desc_b).rstrip(".")!r}')
print(f'  Desc A == Desc B: {desc_a == desc_b}')
print()

# Check full block comparison
print(f'  Full block A (0x0214-0x4207) == Full block B (0x4214-0x81FF)?')
block_a = data[0x0214:0x4208]
block_b = data[0x4214:len(data)]  # to end
min_len = min(len(block_a), len(block_b))
diffs = sum(1 for i in range(min_len) if block_a[i] != block_b[i])
print(f'  Total diffs: {diffs} (over {min_len} bytes)')
print()

# Look for description in all files at both A and B block positions
print('=== Description at 0x03DC and 0x43DC for all files ===')
print()
for fn in sorted(os.listdir('.')):
    if not fn.endswith(('.lqm', '.lqc')):
        continue
    if fn.startswith('modified'):
        continue
    with open(fn, 'rb') as fh:
        d = fh.read()
    name12 = d[0x0208:0x0214]
    desc_a2 = d[0x03DC:0x03FC]
    desc_b2 = d[0x43DC:0x43FC]
    display = decode_xor(name12).rstrip('.')
    desc_a_str = decode_xor(desc_a2).rstrip('.')
    desc_b_str = decode_xor(desc_b2).rstrip('.')
    match = 'MATCH' if desc_a2 == desc_b2 else 'DIFFER'
    print(f'  {display!r:<18} ({match})')
    print(f'    A: {desc_a_str!r}')
    if desc_a2 != desc_b2:
        print(f'    B: {desc_b_str!r}')
    else:
        print(f'    B: (same)')

print()
print('=== HYPOTHESIS: device checks name(0x0208) is contained in desc(0x03DC) ===')
print('Testing: is decode(name12) a substring of decode(desc32)?')
print()
for fn in sorted(os.listdir('.')):
    if not fn.endswith(('.lqm', '.lqc')):
        continue
    if fn.startswith('modified'):
        continue
    with open(fn, 'rb') as fh:
        d = fh.read()
    name12 = d[0x0208:0x0214]
    desc32 = d[0x03DC:0x03FC]
    name_str = decode_xor(name12).strip('.')
    desc_str = decode_xor(desc32).strip('.')
    contained = name_str.strip() in desc_str
    print(f'  {"YES" if contained else "no "} | name={name_str.strip()!r:<15} in desc={desc_str!r}')

print()
print('=== CRITICAL: does the name at 0x03DC need patching too? ===')
print('If we rename "FF ISA 110" -> "FOCUSRITE ISA 110", the desc field still says')
print('"FOCUSRITE CLASSIC ISA 110". This mismatch might cause the corruption error.')
print()
print('Patches needed per rename:')
print('  0x0208-0x0213: 12-byte display name (XOR)')
print('  0x4208-0x4213: 12-byte display name copy (XOR)')
print('  0x03DC-0x03FB: 32-byte description field (XOR) -- ALSO NEEDS PATCHING?')
print('  0x43DC-0x43FB: 32-byte description copy (XOR) -- ALSO NEEDS PATCHING?')
