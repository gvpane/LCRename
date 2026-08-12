import os
import struct
import shutil

# Master real gear mapping dictionary for all 80 factory models
MAPPINGS = {
    # Preamps (Indices 0..39)
    "THE GUV": ("AMEK PURE", "AMEK PURE PATH MIC PREAMP"),
    "VALVE": ("APHEX 1100", "APHEX 1100 CLASS A TUBE PREAMP"),
    "TRANY 1": ("API 3124+", "API 3124+ DISCRETE MIC PREAMP"),
    "SILVER 1A": ("AVALON 22 Hi", "AVALON AD2022 HIGH IMP PREAMP"),
    "SILVER 1B": ("AVALON 2022", "AVALON AD2022 CLASS A MIC PRE"),
    "SILVER 2": ("AVALON 737SP", "AVALON VT-737SP TUBE PREAMP"),
    "BRIT 70'S": ("CADAC G268E", "CADAC G268E CONSOLE MIC PRE"),
    "BIRD BRAIN": ("CS FLAMINGO", "CRANE SONG FLAMINGO MIC PREAMP"),
    "BIG BLUE A": ("DBX 786 Hi", "DBX 786 HIGH IMPEDANCE PREAMP"),
    "BIG BLUE B": ("DBX 786 Lo", "DBX 786 LOW IMPEDANCE PREAMP"),
    "WASP 1": ("DRAWMER 1960", "DRAWMER 1960 TUBE PREAMP"),
    "SCARLET": ("DW FEARN VT2", "DW FEARN VT-2 TUBE PREAMP"),
    "FF ISA 110": ("FF ISA 110", "FOCUSRITE ISA 110 MIC PREAMP"),
    "FF GREEN 5": ("FF GREEN 5", "FOCUSRITE GREEN 5 MIC PREAMP"),
    "FF RED 1": ("FF RED 1", "FOCUSRITE RED 1 MIC PREAMP"),
    "BIG TUBE A": ("GT VIPRE Lo", "GROOVE TUBES VIPRE LOW IMP PRE"),
    "BIG TUBE B": ("GT VIPRE", "GROOVE TUBES VIPRE TUBE PREAMP"),
    "SAV ROW": ("HELIOS PRE", "HELIOS CONSOLE MIC PREAMP"),
    "SAVILLEROW": ("HELIOS PRE", "HELIOS CONSOLE MIC PREAMP"),
    "BRICK": ("JOEMEECK PRE", "JOEMEECK VOICE CHANNEL PREAMP"),
    "DUNK": ("MANLEY SLAM", "MANLEY SLAM TUBE PREAMP"),
    "NEW AGE 1": ("MILLENNIAHV3", "MILLENNIA HV-3D MIC PREAMP"),
    "NEW AGE 2A": ("MILLENNIA 2A", "MILLENNIA STT-1 VACUUM TUBE 2A"),
    "NEW AGE 2B": ("MILLENNIA 2B", "MILLENNIA STT-1 VACUUM TUBE 2B"),
    "NEW AGE 2E": ("MILLENNIA 2E", "MILLENNIA STT-1 VACUUM TUBE 2E"),
    "NEW AGE 2F": ("MILLENNIA 2F", "MILLENNIA STT-1 VACUUM TUBE 2F"),
    "CLASS A 2A": ("NEVE 1073 Hi", "NEVE 1073 HIGH IMPEDANCE PRE"),
    "CLASS A 2B": ("NEVE 1073 Lo", "NEVE 1073 LOW IMPEDANCE PRE"),
    "CLASS AB3A": ("NEVE 1081 Hi", "NEVE 1081 HIGH IMPEDANCE PRE"),
    "CLASS AB3B": ("NEVE 1081 Lo", "NEVE 1081 LOW IMPEDANCE PRE"),
    "CLASS A 1": ("NEVE 33114", "NEVE 33114 MIC PREAMP"),
    "HOTROD": ("NEVE 3416B", "NEVE 3416B HOTROD MIC PREAMP"),
    "BRIT DESK1": ("NEVE VR PRE", "NEVE VR CONSOLE MIC PREAMP"),
    "BRITDESK1": ("NEVE VR PRE", "NEVE VR CONSOLE MIC PREAMP"),
    "NEW TUBE": ("PEAVEY VMP2", "PEAVEY VMP-2 TUBE PREAMP"),
    "OLD TUBE": ("PULTEC MB-1", "PULTEC MB-1 TUBE MIC PREAMP"),
    "RE-ISSUE": ("SI V72 PRE", "TELEFUNKEN V72 TUBE PREAMP"),
    "BRIT DESK2": ("SSL 4000G+", "SSL 4000G+ CONSOLE MIC PREAMP"),
    "BRITDESK2": ("SSL 4000G+", "SSL 4000G+ CONSOLE MIC PREAMP"),
    "SWISS ROLL": ("STUDER D19", "STUDER D19 TUBE MIC PREAMP"),
    "SWISSDRIVE": ("STUDER D19D", "STUDER D19 TUBE PRE DRIVEN"),
    "DEUTSCH 72": ("TELEFUNK V72", "TELEFUNKEN V72 TUBE PREAMP"),
    "DEUTSCH 76": ("TELEFUNK V76", "TELEFUNKEN V76 TUBE PREAMP"),
    "BRIT TUBE1": ("TL AUDIO PA1", "TL AUDIO PA1 TUBE PREAMP"),
    "NASHVILLE": ("TRIDENT A", "TRIDENT A SERIES MIC PREAMP"),
    "VIKING 1": ("TUBE TECH", "TUBE-TECH MEC1A TUBE PREAMP"),
    "STELLAR 1A": ("UA M610 Hi", "UNIVERSAL AUDIO M610 HIGH IMP"),
    "STELLAR 1B": ("UA M610 Lo", "UNIVERSAL AUDIO M610 LOW IMP"),

    # Compressors (Indices 40..79)
    "TRANY C": ("API 2500 C", "API 2500 STEREO COMPRESSOR C"),
    "TRANY A": ("API 2500 A", "API 2500 STEREO COMPRESSOR A"),
    "TRANY R": ("API 2500 R", "API 2500 STEREO COMPRESSOR R"),
    "LIVE SOUND": ("BSS DPR402", "BSS DPR402 DUAL COMPRESSOR"),
    "LONDON": ("CHISWICK 436", "CHISWICK REACH TUBE COMPRESSOR"),
    "WASP 2": ("DRAWMER 221X", "DRAWMER DL221X COMPRESSOR"),
    "BIG BLUE C": ("DBX 160S C", "DBX 160S STEREO COMPRESSOR"),
    "US RADIO": ("DBX 165", "DBX 165 COMPRESSOR LIMITER"),
    "COPY CAT": ("DISTRESSOR 1", "EMPIRICAL LABS DISTRESSOR 1"),
    "COPY CAT 2": ("DISTRESSOR 2", "EMPIRICAL LABS DISTRESSOR 2"),
    "COPY CAT 3": ("DISTRESSOR 3", "EMPIRICAL LABS DISTRESSOR 3"),
    "VINTAGE": ("FAIRCHILD670", "FAIRCHILD MODEL 670 TUBE COMP"),
    "FF ISA 130": ("FF ISA 130", "FOCUSRITE ISA 130 COMPRESSOR"),
    "FF RED 7": ("FF RED 7", "FOCUSRITE RED 7 COMPRESSOR"),
    "DUNK A": ("MANLEY FET", "MANLEY SLAM FET LIMITER"),
    "DUNK B": ("MANLEY ELOP", "MANLEY SLAM ELOP OPTO LIMITER"),
    "PRIMITIVE": ("MANLEY VARIMU", "MANLEY STEREO VARIABLE MU COMP"),
    "BIG GREEN": ("JOEMEECK SC2", "JOEMEECK SC2 OPTICAL COMP"),
    "MEAT PIE": ("PYE 4060", "PYE 4060 CLASS A COMPRESSOR"),
    "GRINDER A": ("SMART C2 A", "SMART RESEARCH C2 COMPRESSOR A"),
    "GRINDER B": ("SMART C2 B", "SMART RESEARCH C2 COMPRESSOR B"),
    "MIX BUSS": ("SSL G384 BUS", "SSL FX G384 STEREO BUS COMP"),
    "BRIT DESK3": ("SSL 510 DYN", "SSL 510 DYNAMICS MODULE"),
    "ACME 1": ("SUMMIT DCL200", "SUMMIT DCL-200 TUBE COMPRESSOR"),
    "ACME 2": ("SUMMIT TLA100", "SUMMIT TLA-100A TUBE LEVELLER"),
    "LEVELLER": ("LA-2A TUBE", "TELETRONIX LA-2A TUBE LEVELLER"),
    "BRIT TUBE": ("TL AUDIO C1", "TL AUDIO C-1 TUBE COMPRESSOR"),
    "VIKING 2": ("TUBE TECH 2", "TUBE-TECH LCA 2B STEREO COMP"),
    "STELLAR 1": ("UA 1176LN", "UNIVERSAL AUDIO 1176LN BLACK"),
    "STELLAR 2": ("UREI 1176LN", "UREI 1176LN SILVER FACE"),
    "STELLAR 3": ("LA-3A OPTO", "UREI LA-3A OPTO LEVELLER"),
    "STELLAR 4": ("UREI LA-4", "UREI LA-4 OPTICAL COMPRESSOR"),
}

def encode_field(text, length):
    result = bytearray(length)
    for i in range(length):
        if i < len(text):
            result[i] = ord(text[i]) ^ 0xFF
        else:
            result[i] = 0xDF
    return bytes(result)

def decode_field(data, offset, length):
    raw = data[offset:offset+length]
    chars = []
    for b in raw:
        dec = b ^ 0xFF
        if dec == (0xDF ^ 0xFF): chars.append(" ")
        elif 0x20 <= dec <= 0x7E: chars.append(chr(dec))
        else: chars.append("?")
    return "".join(chars).rstrip()

src_lqb = "testing files/originals/V2.0_40PRES&COMPS.lqb"
dst_lqb = "testing files/test_variants/CUSTOM_REAL_GEAR_BANK_V2.0.lqb"

with open(src_lqb, "rb") as f:
    bundle_data = bytearray(f.read())

print(f"Reading base template '{src_lqb}' ({len(bundle_data)} bytes)...")

patched_entries = 0
num_entries = (len(bundle_data) - 512) // 32768

for i in range(num_entries):
    base_a = 0x0200 + i * 32768
    base_b = base_a + 16384

    curr_name = decode_field(bundle_data, base_a + 0x0008, 12)
    curr_desc = decode_field(bundle_data, base_a + 0x01DC, 32)

    # Match key in database
    match_key = None
    sorted_keys = sorted(MAPPINGS.keys(), key=len, reverse=True)
    for k in sorted_keys:
        if k in curr_name or k in curr_desc:
            match_key = k
            break

    if match_key:
        real_name, real_desc = MAPPINGS[match_key]
        enc_name = encode_field(real_name, 12)
        enc_desc = encode_field(real_desc, 32)

        # Patch Block A (Standard SR 48kHz profile)
        bundle_data[base_a + 0x0008 : base_a + 0x0008 + 12] = enc_name
        bundle_data[base_a + 0x01DC : base_a + 0x01DC + 32] = enc_desc

        # Patch Block B (High SR 96kHz profile)
        bundle_data[base_b + 0x0008 : base_b + 0x0008 + 12] = enc_name
        bundle_data[base_b + 0x01DC : base_b + 0x01DC + 32] = enc_desc

        patched_entries += 1

with open(dst_lqb, "wb") as f:
    f.write(bundle_data)

print(f"\nGenerated Custom Real Gear Bank Backup file: '{dst_lqb}'")
print(f"  - Size: {len(bundle_data)} bytes (512B Global Bank Header + 80 Real Gear Payloads)")
print(f"  - Patched Entries: {patched_entries} / {num_entries} Emulations")
