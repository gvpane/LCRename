# Liquid Control Format Findings

## High-Level Summary
- **Replica Files (.lqm / .lqc)**: These represent single Liquid Channel emulations (e.g., preamps or compressors). They are exactly 33,280 bytes (`0x8200`).
- **Bank Files (.lqb)**: Used to bundle multiple replicas. These start with a 512-byte global header containing the signature `"LIQC"`.

## The Checksum and Obfuscation Algorithm (CRACKED)

The core misunderstanding in previous reverse-engineering attempts was that the hardware relies on standard cryptographic hashes and plaintext headers. Instead, Sintefex implemented a custom obfuscation and checksum routine:

### 1. Payload Obfuscation
The file is NOT natively encrypted with an advanced cipher. However, the entire payload from `0x0200` to `EOF` (including all display strings, descriptions, and DSP data) is **bitwise inverted (`~byte`)**.
- To read or modify the strings in a hex editor, you must first invert every bit from `0x0200` to the end of the file.
- `LiquidControl.exe` does this inversion in memory when loading the file into the PC software.

### 2. The Checksum (File ID)
The `File ID` located at `0x0000` is **NOT an arbitrary "Hardware Registration Identifier" string like `"LIQC"` or `"USER"`.**
The first 4 bytes are actually a proprietary 32-bit checksum that protects the integrity of the file.

The algorithm to calculate this checksum is:
1. Ensure the file has been correctly obfuscated (bitwise inversion from `0x0200` to `EOF`).
2. Sum all 32-bit Little Endian `DWORD`s starting from `0x0004` to `EOF`.
3. XOR the sum with the magic constant: `0x29A7FE19`.
4. The resulting 32-bit integer is the correct `File ID` checksum and must be written to `0x0000-0x0003`.

### 3. File Structure (De-obfuscated)
Once the payload from `0x0200` is de-obfuscated, the true structure is visible:

* **0x0000**: `File ID` / Checksum
* **0x0004 - 0x01FF**: Unknown binary structure (Likely parameters or meta tags, untouched by obfuscation).
* **0x0200**: `pre_a` (`0xdeeeeca5` for Preamp A, etc.)
* **0x0204**: `pre_b` (Type Tag - e.g., `0x00020000`)
* **0x0208**: Display Name (Max 15 chars, null-terminated. Exactly 16 bytes long. Data immediately following `0x0217` contains critical DSP variables that will cause corruption if overwritten!)
* **0x03DC**: Description (Max 31 chars, null-terminated)
* **0x0400 - 0x41FF**: DSP Data for Standard Sample Rates (44.1k / 48k)
* **0x4200 - 0x81FF**: Block B (High Sample Rate 88.2k / 96k). Exact same header structure as Block A, including another copy of the Display Name and Description.

### Renaming Files
A custom tool `LCRename.py` has been written to properly handle the unobfuscation, string replacement, re-obfuscation, and checksum regeneration. Modifying strings blindly with a hex editor and leaving the `File ID` intact causes the hardware to throw the "possibly corrupted" error due to a checksum mismatch.
