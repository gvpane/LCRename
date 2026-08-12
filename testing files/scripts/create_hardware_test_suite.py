import os
import struct
import zlib

def encode_field(text, length, leading_space=False):
    result = bytearray(length)
    idx = 0
    if leading_space:
        result[0] = 0xDF  # space XOR 0xFF
        idx = 1
    for c in text:
        if idx < length:
            result[idx] = ord(c) ^ 0xFF
            idx += 1
    while idx < length:
        result[idx] = 0xDF
        idx += 1
    return bytes(result)

src_file = "testing files/originals/original FF ISA 110.lqm"
with open(src_file, "rb") as f:
    orig_data = bytearray(f.read())

enc_name12 = encode_field("FF ISA 110 T", 12)
enc_desc32 = encode_field("FOCUSRITE CLASSIC ISA 110 TEST ", 32)
enc_desc32_lead = encode_field("FOCUSRITE CLASSIC ISA 110 TEST", 32, leading_space=True)

# Variant 1: Display Name Only (0x0208 & 0x4208)
v1 = bytearray(orig_data)
v1[0x0208:0x0214] = enc_name12
v1[0x4208:0x4214] = enc_name12
with open("testing files/test_variants/TEST_V1_DISPLAY_ONLY.lqm", "wb") as f:
    f.write(v1)

# Variant 2: Display Name + Description (0x0208, 0x4208, 0x03DC, 0x43DC)
v2 = bytearray(orig_data)
v2[0x0208:0x0214] = enc_name12
v2[0x4208:0x4214] = enc_name12
v2[0x03DC:0x03FC] = enc_desc32
v2[0x43DC:0x43FC] = enc_desc32
with open("testing files/test_variants/TEST_V2_NAME_AND_DESC.lqm", "wb") as f:
    f.write(v2)

# Variant 3: Name + Desc + Zeroed pre_a (0x0200 & 0x4200)
v3 = bytearray(v2)
v3[0x0200:0x0204] = b"\x00\x00\x00\x00"
v3[0x4200:0x4204] = b"\x00\x00\x00\x00"
with open("testing files/test_variants/TEST_V3_ZERO_PRE_A.lqm", "wb") as f:
    f.write(v3)

# Variant 4: Name + Desc + Zeroed File ID (0x0000)
v4 = bytearray(v2)
v4[0x0000:0x0004] = b"\x00\x00\x00\x00"
with open("testing files/test_variants/TEST_V4_ZERO_FILE_ID.lqm", "wb") as f:
    f.write(v4)

# Variant 5: Name + Desc with exact Factory Leading Space (0xDF at 0x03DC)
v5 = bytearray(orig_data)
v5[0x0208:0x0214] = enc_name12
v5[0x4208:0x4214] = enc_name12
v5[0x03DC:0x03FC] = enc_desc32_lead
v5[0x43DC:0x43FC] = enc_desc32_lead
with open("testing files/test_variants/TEST_V5_FACTORY_PADDING.lqm", "wb") as f:
    f.write(v5)

# Variant 6: Name + Desc + CRC32 calculated pre_a & pre_b
v6 = bytearray(v2)
crc_a = zlib.crc32(enc_name12 + enc_desc32) & 0xFFFFFFFF
v6[0x0200:0x0204] = struct.pack("<I", crc_a)
v6[0x4200:0x4204] = struct.pack("<I", crc_a)
with open("testing files/test_variants/TEST_V6_CRC32_META.lqm", "wb") as f:
    f.write(v6)

print("Generated 6 test variants in 'testing files/':")
print("  1. TEST_V1_DISPLAY_ONLY.lqm")
print("  2. TEST_V2_NAME_AND_DESC.lqm")
print("  3. TEST_V3_ZERO_PRE_A.lqm")
print("  4. TEST_V4_ZERO_FILE_ID.lqm")
print("  5. TEST_V5_FACTORY_PADDING.lqm")
print("  6. TEST_V6_CRC32_META.lqm")
