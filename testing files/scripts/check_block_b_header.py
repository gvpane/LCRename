import struct, os

def decode_xor(b):
    return ''.join(chr(x ^ 0xFF) if 0x20 <= (x ^ 0xFF) <= 0x7E else '.' for x in b)

rows = []
for fn in sorted(os.listdir('.')):
    if not fn.endswith(('.lqm', '.lqc')):
        continue
    if fn.startswith('modified'):
        continue
    with open(fn, 'rb') as f:
        d = f.read()
    rows.append((fn, d))

print('=== Block A vs Block B header comparison ===')
print()
for fn, d in rows:
    file_id_a = struct.unpack('<I', d[0x0000:0x0004])[0]
    pre_a     = struct.unpack('<I', d[0x0200:0x0204])[0]
    tag_a     = d[0x0204:0x0208].hex()
    name_a    = decode_xor(d[0x0208:0x0214]).rstrip('.')

    # Block B equivalents
    file_id_b = struct.unpack('<I', d[0x4000:0x4004])[0]
    pre_b     = struct.unpack('<I', d[0x4200:0x4204])[0]
    tag_b     = d[0x4204:0x4208].hex()
    name_b    = decode_xor(d[0x4208:0x4214]).rstrip('.')

    print(fn)
    print("  A: file_id=0x%08X  pre=0x%08X  tag=%s  name=%r" % (file_id_a, pre_a, tag_a, name_a))
    print("  B: file_id=0x%08X  pre=0x%08X  tag=%s  name=%r" % (file_id_b, pre_b, tag_b, name_b))
    print("  Match: id=%s  pre=%s  tag=%s  name=%s" % (
        'YES' if file_id_a == file_id_b else 'NO',
        'YES' if pre_a == pre_b else 'NO',
        'YES' if tag_a == tag_b else 'NO',
        'YES' if name_a == name_b else 'NO',
    ))
    print()
