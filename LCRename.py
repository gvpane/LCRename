import sys
import struct
import argparse
import os

MAGIC_CONSTANT = 0x29A7FE19

def unobfuscate(data):
    """Inverts the payload bits starting from 0x0200 to reveal plaintext."""
    for i in range(0x200, len(data)):
        data[i] = ~data[i] & 0xFF

def obfuscate(data):
    """Inverts the payload bits starting from 0x0200 to obfuscate it again."""
    for i in range(0x200, len(data)):
        data[i] = ~data[i] & 0xFF

def calculate_checksum(data):
    """
    Calculates the required checksum (File ID) for a Liquid Control replica file.
    Note: The checksum is calculated OVER THE OBFUSCATED DATA!
    """
    num_dwords = (len(data) - 4) // 4
    words = struct.unpack(f'<{num_dwords}I', data[4:4+num_dwords*4])
    checksum = sum(words) & 0xFFFFFFFF
    return checksum ^ MAGIC_CONSTANT

def rename_replica(in_file, out_file, new_name, new_desc=None):
    with open(in_file, 'rb') as f:
        data = bytearray(f.read())
        
    print(f"[*] Processing {in_file}...")
    
    # 1. Unobfuscate payload to reveal the headers
    unobfuscate(data)
    
    # Extract existing names to show the user
    old_name = data[0x0208:0x0218].split(b'\x00')[0].decode('utf-8', errors='ignore')
    old_desc = data[0x03DC:0x03FC].split(b'\x00')[0].decode('utf-8', errors='ignore')
    print(f"    Old Name: {old_name}")
    print(f"    Old Desc: {old_desc}")
    
    # 2. Modify strings
    # The Name field is exactly 16 bytes. Bytes after 0x0217 contain critical DSP struct data!
    name_bytes = new_name.encode('utf-8')[:15].ljust(16, b'\x00')
    data[0x0208:0x0208+16] = name_bytes
    if new_desc:
        desc_bytes = new_desc.encode('utf-8')[:31].ljust(32, b'\x00')
        data[0x03DC:0x03DC+32] = desc_bytes
        
    # Block B (High Sample Rate)
    if len(data) >= 0x4208 + 16:
        data[0x4208:0x4208+16] = name_bytes
        if new_desc:
            data[0x43DC:0x43DC+32] = desc_bytes
            
    print(f"    New Name: {new_name}")
    if new_desc:
        print(f"    New Desc: {new_desc}")

    # 3. Re-obfuscate payload
    obfuscate(data)
    
    # 4. Calculate new Checksum/File ID
    new_checksum = calculate_checksum(data)
    
    # 5. Overwrite the first 4 bytes (File ID)
    data[0:4] = struct.pack('<I', new_checksum)
    
    with open(out_file, 'wb') as f:
        f.write(data)
        
    print(f"[*] Saved to {out_file} (New ID: 0x{new_checksum:08X})\n")

def main():
    parser = argparse.ArgumentParser(description="Rename Focusrite Liquid Channel Replica (.lqm/.lqc) files.")
    parser.add_argument('input', help="Input replica file")
    parser.add_argument('output', help="Output replica file")
    parser.add_argument('-n', '--name', required=True, help="New display name (max 31 chars)")
    parser.add_argument('-d', '--desc', help="New description (max 31 chars)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: File {args.input} does not exist.")
        sys.exit(1)
        
    rename_replica(args.input, args.output, args.name, args.desc)

if __name__ == '__main__':
    main()
