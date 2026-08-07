"""
Create a properly patched test file in the sandbox.
Patches ALL four name-related fields:
  0x0208-0x0213: display name A (12 bytes, XOR 0xFF)
  0x4208-0x4213: display name B copy (12 bytes, XOR 0xFF)
  0x03DC-0x03FB: description A (32 bytes, XOR 0xFF)
  0x43DC-0x43FB: description B copy (32 bytes, XOR 0xFF)
"""
import struct, os

def decode_xor(b):
    return ''.join(chr(x ^ 0xFF) if 0x20 <= (x ^ 0xFF) <= 0x7E else '.' for x in b)

def encode_xor(text, length, pad=0xDF):
    result = bytearray(length)
    for i in range(length):
        if i < len(text):
            c = ord(text[i])
            result[i] = c ^ 0xFF
        else:
            result[i] = pad  # space XOR 0xFF = 0xDF
    return bytes(result)

src = 'original FF ISA 110.lqm'
dst = 'PATCHED_TEST FF ISA 110.lqm'

with open(src, 'rb') as f:
    data = bytearray(f.read())

print(f'Source: {src}')
print(f'Original display name: {decode_xor(data[0x0208:0x0214]).rstrip(".")!r}')
print(f'Original description:  {decode_xor(data[0x03DC:0x03FC]).rstrip(".")!r}')
print()

# New names — testing that the device accepts ANY valid 12-char name
# Using "FOCUSRITE ISA" (12 chars exactly) as test
new_display = 'FOCUSRITE ISA'  # 13 chars -- too long, trim to 12
new_display = 'FCUSRITE ISA1'  # Actually let me use something 12 chars
# For the description, make it match: 32 chars, space-padded
new_display = 'FF ISA 110 TE'  # 13 -- no
new_display = 'FF ISA 110 T'   # 12 chars - test
new_desc    = 'FOCUSRITE CLASSIC ISA 110 TEST  '  # 32 chars

print(f'New display name ({len(new_display)} chars): {new_display!r}')
print(f'New description  ({len(new_desc)} chars): {new_desc!r}')
print()

# Encode and patch
enc_display = encode_xor(new_display, 12)
enc_desc    = encode_xor(new_desc, 32)

# Verify
assert decode_xor(enc_display).rstrip('.') == new_display, "Display name encode failed"
decoded_back = decode_xor(enc_desc)
assert decoded_back == new_desc, f"Description encode failed: got {decoded_back!r}"

# Apply patches
data[0x0208:0x0214] = enc_display  # name A
data[0x4208:0x4214] = enc_display  # name B (must match A)
data[0x03DC:0x03FC] = enc_desc     # desc A
data[0x43DC:0x43FC] = enc_desc     # desc B (must match A)

# Verify patches
print('Verification after patch:')
print(f'  0x0208 name A: {decode_xor(data[0x0208:0x0214]).rstrip(".")!r}')
print(f'  0x4208 name B: {decode_xor(data[0x4208:0x4214]).rstrip(".")!r}')
print(f'  0x03DC desc A: {decode_xor(data[0x03DC:0x03FC]).rstrip(".")!r}')
print(f'  0x43DC desc B: {decode_xor(data[0x43DC:0x43FC]).rstrip(".")!r}')
print(f'  Name A == B: {data[0x0208:0x0214] == data[0x4208:0x4214]}')
print(f'  Desc A == B: {data[0x03DC:0x03FC] == data[0x43DC:0x43FC]}')
print()

# Note the file ID and pre_a fields (NOT patching these — testing if they matter)
file_id = struct.unpack_from('<I', data, 0)[0]
pre_a   = struct.unpack_from('<I', data, 0x200)[0]
print(f'  File ID at 0x0000: 0x{file_id:08X} (UNCHANGED - testing if hardware cares)')
print(f'  Pre-A at  0x0200: 0x{pre_a:08X} (UNCHANGED - testing if hardware cares)')
print()

with open(dst, 'wb') as f:
    f.write(data)

print(f'Patched file written to: {dst}')
print()
print('=== TEST INSTRUCTIONS ===')
print('1. Load this file onto the Focusrite Liquid Channel hardware')
print('2. If device shows "FF ISA 110 T" without corruption error -> name+desc patching works')
print('3. If still corrupted -> file_id (0x0000) or pre_a (0x0200) also need updating')
print()
print('For comparison, also test original file to confirm it loads fine.')
