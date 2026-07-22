# Liquid Channel Renamer — Handoff

## What was done

The Focusrite Liquid Channel ships emulation files (`.lqm` preamps, `.lqc` compressors) with fictional names embedded in the binary for copyright reasons. This session reverse-engineered the file format and renamed all 92 emulations to their real gear names — both the filenames and the embedded binary names.

### File format discovered

- Fixed size: 33280 bytes per file
- Display name: 12-byte field at offset `0x0208`, XOR'd with `0xFF`, space-padded with `0xDF`
- Duplicate name copy at `0x4208` — both must match
- First 4 bytes: per-file unique ID (confirmed NOT a checksum — safe to leave untouched)
- `.lqb` bundle file is a different format; left untouched

### Changes made

1. All `.lqm` and `.lqc` files renamed (filename) from fictional names to real gear names
2. Embedded binary name field patched in both copies (`0x0208` and `0x4208`) for all files
3. `lqm_rename.py` written — tkinter GUI for future interactive renaming with validation and `.bak` backups

### Fictional → real name mapping source

The PDFs in this repo are the authoritative source. `Preamps_40_Original_Factory_Emulations.pdf` and `Compressors_40_Original_Factory_Emulations.pdf` cover the factory set. The dated PDFs cover add-on packs released 2004–2006.

## Known constraints

- Name field: max **12 characters**, printable ASCII only
- Some gear names are truncated to fit — e.g. "NEVE 1073 H" (11 chars) for the Hø impedance variant, since "NEVE 1073 Hø" is 13 chars (the `ø` is non-ASCII anyway)
- The `HOT` / `PAD` / `DRV` suffixes in filenames are intentional; they are not in the binary name due to the 12-char limit

## What's left / could be improved

- The `lqm_rename.py` GUI tool does not rename the file on disk — it only patches the binary name. If you want the filename to match the new embedded name, rename the file separately.
- The `.lqb` bundle file format has not been investigated — it contains all 40 factory preamps and compressors bundled but its internal structure is unknown.
- Some variant files (Hø/Lø/Mø) have the impedance character in the filename but not in the embedded name (12-char limit). This is acceptable — the device shows the embedded name.
