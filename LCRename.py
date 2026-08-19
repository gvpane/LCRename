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
    CRITICAL: The checksum MUST be calculated OVER THE UNOBFUSCATED DATA!
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
    # The Name field is strictly 12 characters (space-padded), followed by 4 null bytes. 
    # Bytes after 0x0217 contain critical DSP struct data!
    name_str = new_name[:12].ljust(12, ' ')
    name_bytes = name_str.encode('ascii') + b'\x00\x00\x00\x00'
    data[0x0208:0x0208+16] = name_bytes
    
    if new_desc:
        # Description is strictly 32 bytes (space-padded). NO NULL BYTES!
        desc_str = new_desc[:32].ljust(32, ' ')
        desc_bytes = desc_str.encode('ascii')
        data[0x03DC:0x03DC+32] = desc_bytes
        
    # Block B (High Sample Rate)
    if len(data) >= 0x4208 + 16:
        data[0x4208:0x4208+16] = name_bytes
        if new_desc:
            data[0x43DC:0x43DC+32] = desc_bytes
            
    # 3. Recalculate Block Checksums (pre_a)
    BLOCK_MAGIC = 0xEF94B156
    
    # Block A
    num_dwords_a = (0x4200 - 0x204) // 4
    words_a = struct.unpack(f'<{num_dwords_a}I', data[0x204:0x4200])
    sum_a = sum(words_a) & 0xFFFFFFFF
    pre_a = sum_a ^ BLOCK_MAGIC
    data[0x0200:0x0204] = struct.pack('<I', pre_a)
    
    # Block B (if exists)
    if len(data) >= 0x8200:
        num_dwords_b = (0x8200 - 0x4204) // 4
        words_b = struct.unpack(f'<{num_dwords_b}I', data[0x4204:0x8200])
        sum_b = sum(words_b) & 0xFFFFFFFF
        pre_b = sum_b ^ BLOCK_MAGIC
        data[0x4200:0x4204] = struct.pack('<I', pre_b)
            
    print(f"    New Name: {new_name}")
    if new_desc:
        print(f"    New Desc: {new_desc}")

    # 4. Calculate new Checksum/File ID
    # CRITICAL: The master File ID checksum is mathematically calculated on the UNOBFUSCATED payload!
    new_checksum = calculate_checksum(data)
    
    # 5. Re-obfuscate payload
    obfuscate(data)
    
    # 6. Overwrite the first 4 bytes (File ID)
    # The File ID itself is never obfuscated, so we can write it after obfuscating the rest of the payload.
    data[0:4] = struct.pack('<I', new_checksum)
    
    with open(out_file, 'wb') as f:
        f.write(data)
        
    print(f"[*] Saved to {out_file} (New ID: 0x{new_checksum:08X})\n")

def read_replica(in_file):
    with open(in_file, 'rb') as f:
        data = bytearray(f.read())
        
    print(f"[*] Reading {in_file}...")
    
    # Unobfuscate payload to reveal the headers
    unobfuscate(data)
    
    # Extract existing names
    old_name = data[0x0208:0x0218].split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
    old_desc = data[0x03DC:0x03FC].split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
    print(f"    Name: {old_name}")
    print(f"    Description: {old_desc}")

def main():
    parser = argparse.ArgumentParser(description="Read or Rename Focusrite Liquid Channel Replica (.lqm/.lqc) files.")
    parser.add_argument('input', help="Input replica file")
    parser.add_argument('output', nargs='?', help="Output replica file (required for renaming)")
    parser.add_argument('-n', '--name', help="New display name (max 12 chars, space-padded)")
    parser.add_argument('-d', '--desc', help="New description (max 32 chars, space-padded)")
    parser.add_argument('-r', '--read', action='store_true', help="Read and display current name and description without modifying")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: File {args.input} does not exist.")
        sys.exit(1)
        
    if args.read:
        read_replica(args.input)
    else:
        if not args.output or not args.name:
            print("Error: For renaming, both 'output' and '--name' arguments are required.")
            parser.print_help()
            sys.exit(1)
        rename_replica(args.input, args.output, args.name, args.desc)

if __name__ == '__main__':
    main()
