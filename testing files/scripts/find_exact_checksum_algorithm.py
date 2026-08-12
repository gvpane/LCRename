import glob
import struct
import zlib

files = sorted(glob.glob("testing files/originals/*.lqm") + glob.glob("testing files/originals/*.lqc"))

print(f"Loaded {len(files)} original replica files for checksum cracking.\n")

# Load file data
data_list = []
for f in files:
    with open(f, "rb") as fp:
        d = fp.read()
    fid = struct.unpack("<I", d[0:4])[0]
    pre_a = struct.unpack("<I", d[0x200:0x204])[0]
    pre_b = struct.unpack("<I", d[0x4200:0x4204])[0]
    data_list.append((f, d, fid, pre_a, pre_b))

sample_f, sample_d, sample_fid, sample_pre_a, sample_pre_b = data_list[0]
print(f"Sample File: {sample_f}")
print(f"  File ID (0x0000): 0x{sample_fid:08X}")
print(f"  PreA    (0x0200): 0x{sample_pre_a:08X}")
print(f"  PreB    (0x4200): 0x{sample_pre_b:08X}")

# Test 1: Checksum over Block A payload (0x0204 to 0x41FF)
# Let's test various CRC32 polynomials and initial values
def crc32_custom(data, poly, init, xor_out, reflect_in, reflect_out):
    crc = init
    for b in data:
        if reflect_in:
            b = int('{:08b}'.format(b)[::-1], 2)
        crc ^= (b << 24)
        for _ in range(8):
            if crc & 0x80000000:
                crc = ((crc << 1) ^ poly) & 0xFFFFFFFF
            else:
                crc = (crc << 1) & 0xFFFFFFFF
    if reflect_out:
        crc = int('{:032b}'.format(crc)[::-1], 2)
    return crc ^ xor_out

# Test Additive Checksums
def sum32(data):
    s = 0
    for i in range(0, len(data), 4):
        val = struct.unpack("<I", data[i:i+4])[0]
        s = (s + val) & 0xFFFFFFFF
    return s

def sum32_be(data):
    s = 0
    for i in range(0, len(data), 4):
        val = struct.unpack(">I", data[i:i+4])[0]
        s = (s + val) & 0xFFFFFFFF
    return s

def xor32(data):
    x = 0
    for i in range(0, len(data), 4):
        val = struct.unpack("<I", data[i:i+4])[0]
        x ^= val
    return x

# Test DJB2 / SDBP / Rotating hashes
def djb2(data):
    h = 5381
    for b in data:
        h = ((h << 5) + h + b) & 0xFFFFFFFF
    return h

def sdbm(data):
    h = 0
    for b in data:
        h = (b + (h << 6) + (h << 16) - h) & 0xFFFFFFFF
    return h

# Test region candidates for PreA (0x0200)
# Region 1: 0x0204..0x4200 (Block A body, 16380 bytes)
# Region 2: 0x0208..0x0214 (Name A, 12 bytes)
# Region 3: 0x0208..0x03FC (Name + Desc + Params, 500 bytes)
# Region 4: 0x0000..0x0200 (512-byte header)

block_a_body = sample_d[0x0204:0x4200]
name_a = sample_d[0x0208:0x0214]

print("\n--- Testing Mathematical Hash Functions on Block A ---")
print(f"sum32(block_a_body):    0x{sum32(block_a_body):08X}")
print(f"sum32_be(block_a_body): 0x{sum32_be(block_a_body):08X}")
print(f"xor32(block_a_body):    0x{xor32(block_a_body):08X}")
print(f"djb2(block_a_body):     0x{djb2(block_a_body):08X}")
print(f"sdbm(block_a_body):     0x{sdbm(block_a_body):08X}")
print(f"adler32(block_a_body):  0x{zlib.adler32(block_a_body):08X}")
