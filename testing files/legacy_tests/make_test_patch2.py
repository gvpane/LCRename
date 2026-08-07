"""
Test patch v2: patch all 4 name/desc fields AND zero out pre_a + pre_b.
If device accepts this, we know pre_a/pre_b are hash fields that need recomputing.
"""
import struct, os

def decode_xor(b):
    return ''.join(chr(x ^ 0xFF) if 0x20 <= (x ^ 0xFF) <= 0x7E else '.' for x in b)

def encode_xor(text, length, pad=0xDF):
    result = bytearray(length)
    for i in range(length):
        if i < len(text):
            result[i] = ord(text[i]) ^ 0xFF
        else:
            result[i] = pad
    return bytes(result)

src = 'original FF ISA 110.lqm'

with open(src, 'rb') as f:
    data = bytearray(f.read())

new_display = 'FF ISA 110 T'   # 12 chars
new_desc    = 'FOCUSRITE CLASSIC ISA 110 TEST  '  # 32 chars

enc_display = encode_xor(new_display, 12)
enc_desc    = encode_xor(new_desc, 32)

# Patch all 4 name/desc fields
data[0x0208:0x0214] = enc_display
data[0x4208:0x4214] = enc_display
data[0x03DC:0x03FC] = enc_desc
data[0x43DC:0x43FC] = enc_desc

# --- NEW: zero out pre_a and pre_b ---
pre_a_before = struct.unpack('<I', data[0x0200:0x0204])[0]
pre_b_before = struct.unpack('<I', data[0x4200:0x4204])[0]
data[0x0200:0x0204] = b'\x00\x00\x00\x00'
data[0x4200:0x4204] = b'\x00\x00\x00\x00'

dst = 'PATCHED_TEST2_ZERO_PRE FF ISA 110.lqm'
with open(dst, 'wb') as f:
    f.write(data)

print("Source: %s" % src)
print("Dest:   %s" % dst)
print()
print("Patches applied:")
print("  0x0208 name A  -> %r" % decode_xor(data[0x0208:0x0214]).rstrip('.'))
print("  0x4208 name B  -> %r" % decode_xor(data[0x4208:0x4214]).rstrip('.'))
print("  0x03DC desc A  -> %r" % decode_xor(data[0x03DC:0x03FC]).rstrip('.'))
print("  0x43DC desc B  -> %r" % decode_xor(data[0x43DC:0x43FC]).rstrip('.'))
print("  0x0200 pre_a   was 0x%08X -> now 0x00000000 (ZEROED)" % pre_a_before)
print("  0x4200 pre_b   was 0x%08X -> now 0x00000000 (ZEROED)" % pre_b_before)
print()
print("=== TEST ===")
print("If device shows 'FF ISA 110 T' WITHOUT corruption -> pre_a/pre_b are hash fields,")
print("  zeroing disables the check, need to find the hash algorithm to do it properly.")
print("If still corrupted -> something else (file_id, audio data checksum, etc.)")
