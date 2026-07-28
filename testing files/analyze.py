import struct, math, os, sys

def analyze_file(path):
    with open(path, 'rb') as f:
        data = f.read()

    fname = os.path.basename(path)
    lines = []
    def w(s=''): lines.append(s)

    w('=' * 65)
    w(f'  FILE: {fname}')
    w(f'  SIZE: {len(data)} bytes')
    w('=' * 65)
    w()

    # ID bytes
    id_bytes = data[0:4]
    w(f'  [0x0000]  File ID:  {" ".join(f"{b:02X}" for b in id_bytes)}  = uint32-LE {struct.unpack_from("<I", data, 0)[0]}')

    # Fields at 0x0008
    w(f'  [0x0008]  Field:    {" ".join(f"{data[8+i]:02X}" for i in range(4))}  = uint32-LE {struct.unpack_from("<I", data, 8)[0]}')

    # Magic string
    magic_end = data.index(b'\x00', 0x000C)
    magic_str = data[0x000C:magic_end].decode('ascii')
    w(f'  [0x000C]  Magic:    "{magic_str}"')

    # Pre-name fields
    w(f'  [0x0200]  Pre-name A: {" ".join(f"{data[0x200+i]:02X}" for i in range(4))}  = uint32-LE {struct.unpack_from("<I", data, 0x200)[0]}')
    w(f'  [0x0204]  Pre-name B: {" ".join(f"{data[0x204+i]:02X}" for i in range(4))}  = int32-LE  {struct.unpack_from("<i", data, 0x204)[0]}')

    # Name at 0x0208
    raw_name = data[0x0208:0x0214]
    decoded = ''.join(chr(b ^ 0xFF) if 0x20 <= (b ^ 0xFF) <= 0x7E else '.' for b in raw_name)
    w(f'  [0x0208]  Name:     {" ".join(f"{b:02X}" for b in raw_name)}  -> "{decoded.rstrip(".")}"')

    # Name copy at 0x4208
    raw2 = data[0x4208:0x4214]
    dec2 = ''.join(chr(b ^ 0xFF) if 0x20 <= (b ^ 0xFF) <= 0x7E else '.' for b in raw2)
    match = raw_name == raw2
    w(f'  [0x4208]  Name cp:  {" ".join(f"{b:02X}" for b in raw2)}  -> "{dec2.rstrip(".")}"  match={match}')
    w()

    # Non-FF regions in data block 1
    regions = []
    i = 0x0214
    while i < 0x4208:
        if data[i] != 0xFF:
            start = i
            while i < 0x4208 and data[i] != 0xFF:
                i += 1
            regions.append((start, i))
        else:
            i += 1

    w(f'  Non-FF regions in data block A (0x0214-0x4207):')
    for s, e in regions:
        aligned = s if s % 4 == 0 else s + (4 - s % 4)
        floats = []
        for off in range(aligned, e - 3, 4):
            v = struct.unpack_from('<f', data, off)[0]
            floats.append((off, v))
        w(f'    0x{s:04X}-0x{e-1:04X} ({e-s} bytes, ~{len(floats)} float32):')
        shown = 0
        for off, v in floats:
            if math.isnan(v) or math.isinf(v):
                continue
            b4 = data[off:off+4]
            w(f'      0x{off:04X}: {" ".join(f"{x:02X}" for x in b4)}  {v:>14.6f}')
            shown += 1
            if shown >= 30:
                w(f'      ... ({len(floats)-shown} more)')
                break
    w()

    # Block 2 mirror check
    diffs = 0
    for i in range(min(0x4207 - 0x0214, 0x81FF - 0x4214)):
        if data[0x0214 + i] != data[0x4214 + i]:
            diffs += 1
    w(f'  Data block B (0x4214-0x81FF) differs from block A by: {diffs} bytes')
    w()

    return '\n'.join(lines)


# Compare all files in folder
folder = os.path.dirname(os.path.abspath(__file__))
files = sorted(f for f in os.listdir(folder) if f.endswith(('.lqm', '.lqc')) and f.startswith('original'))

print(f'Analyzing {len(files)} original files...\n')

all_output = []
id_table = []

for fname in files:
    path = os.path.join(folder, fname)
    with open(path, 'rb') as f:
        data = f.read()
    file_id = ' '.join(f'{data[i]:02X}' for i in range(4))
    pre_a   = ' '.join(f'{data[0x200+i]:02X}' for i in range(4))
    pre_b   = ' '.join(f'{data[0x204+i]:02X}' for i in range(4))
    raw_name = data[0x0208:0x0214]
    decoded = ''.join(chr(b ^ 0xFF) if 0x20 <= (b ^ 0xFF) <= 0x7E else '.' for b in raw_name)
    decoded = decoded.rstrip('.')
    id_table.append((fname, file_id, pre_a, pre_b, decoded))

print('=== COMPARISON TABLE (all original files) ===')
print(f'{"File":<35} {"ID (0x0000)":<14} {"PreA (0x0200)":<14} {"PreB (0x0204)":<14} {"Name"}')
print('-' * 100)
for row in id_table:
    print(f'{row[0]:<35} {row[1]:<14} {row[2]:<14} {row[3]:<14} {row[4]}')

print()

# Full detail on each file
for fname in files:
    path = os.path.join(folder, fname)
    txt = analyze_file(path)
    all_output.append(txt)
    print(txt)

with open(os.path.join(folder, 'file_format_analysis.txt'), 'w', encoding='utf-8') as f:
    f.write('=== COMPARISON TABLE (all original files) ===\n')
    f.write(f'{"File":<35} {"ID (0x0000)":<14} {"PreA (0x0200)":<14} {"PreB (0x0204)":<14} {"Name"}\n')
    f.write('-' * 100 + '\n')
    for row in id_table:
        f.write(f'{row[0]:<35} {row[1]:<14} {row[2]:<14} {row[3]:<14} {row[4]}\n')
    f.write('\n\n')
    f.write('\n\n'.join(all_output))

print('Saved: file_format_analysis.txt')
