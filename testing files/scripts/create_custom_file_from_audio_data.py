import os
import struct

def encode_field(text, length):
    result = bytearray(length)
    for i in range(length):
        if i < len(text):
            result[i] = ord(text[i]) ^ 0xFF
        else:
            result[i] = 0xDF
    return bytes(result)

src_path = "testing files/originals/original FF ISA 110.lqm"
with open(src_path, "rb") as f:
    orig_data = bytearray(f.read())

# Create a Custom User Preset container:
# 1. Start with clean base data
custom_file = bytearray(orig_data)

# 2. Assign a custom non-factory File ID (e.g. 0x00000000 or 0x55534552 = "USER" LE)
custom_file[0x0000:0x0004] = b"USER" # Custom user file magic ID

# 3. Set custom Display Name A (0x0208) & Display Name B (0x4208)
custom_name = encode_field("ISA 110 REAL", 12)
custom_file[0x0208:0x0214] = custom_name
custom_file[0x4208:0x4214] = custom_name

# 4. Zero out pre_a (0x0200) & pre_b (0x4200) to flag as un-checksummed user data
custom_file[0x0200:0x0204] = b"\x00\x00\x00\x00"
custom_file[0x4200:0x4204] = b"\x00\x00\x00\x00"

# 5. AUDIO CONVOLUTION DATA (0x03FC to 0x41FF and 0x43FD to 0x81FF) IS 100% UNTOUCHED ORIGINAL DATA!

dst_path = "testing files/test_variants/TEST_CUSTOM_CONTAINER_ISA110.lqm"
with open(dst_path, "wb") as f:
    f.write(custom_file)

print(f"Successfully generated custom file container: {dst_path}")
print("  - Audio Convolution DSP Payload: 100% identical copy of original ISA 110")
print("  - File ID: Custom 'USER' ID (0x55534552)")
print("  - Display Name: 'ISA 110 REAL'")
