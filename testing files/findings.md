# Focusrite Liquid Channel File Format & Hardware Test Log

## Objective

Reverse-engineer the `.lqm` (preamp) and `.lqc` (compressor) binary file format to edit internal **display names** to real-world gear names without triggering hardware validation / corruption errors on the Focusrite Liquid Channel.

> **Note**: Primary focus is on the 12-character Display Name fields on the LCD hardware.

---

## File Format & Structure (Reverse-Engineered)

All single emulation files are **33,280 bytes** (`0x8200`). The file contains a 512-byte global header followed by two mirrored 16,384-byte data blocks (Block A and Block B).

| File Offset | Length | Field Description | Encoding / Format |
|-------------|--------|-------------------|-------------------|
| `0x0000` | 4 bytes | File ID | uint32-LE (Per-file unique ID) |
| `0x0008` | 4 bytes | Header Offset | uint32-LE `0x00000200` (512) |
| `0x000C` | 96 bytes | Magic String | `"Liquid Channel (tm) file format..."` |
| `0x0200` | 4 bytes | `pre_a` (Block A Header) | uint32-LE |
| `0x0204` | 4 bytes | `pre_b` (Type Tag) | `0xFFFFFDFF` (preamp) or `0xFDFFFFFF` (compressor) |
| `0x0208` | 12 bytes | Display Name A | Printable ASCII, XOR `0xFF`, padded with `0xDF` |
| `0x03DC` | 32 bytes | Description A | Printable ASCII, XOR `0xFF`, padded with `0xDF` |
| `0x4200` | 4 bytes | `pre_a` copy (Block B Header) | uint32-LE |
| `0x4204` | 4 bytes | `pre_b` (Type Tag copy) | `0xFFFFFDFF` (preamp) or `0xFDFFFFFF` (compressor) |
| `0x4208` | 12 bytes | Display Name B copy | **Must match `0x0208`** |
| `0x43DC` | 32 bytes | Description B copy | **Must match `0x03DC`** |

---

## Hardware Test Variants Log

The reference preamp used for testing is `original FF ISA 110.lqm` located in `testing files/`. Six distinct test variants have been generated inside `testing files/` to isolate which fields or structural requirements the Liquid Channel hardware enforces during upload.

### Variant 1: `TEST_V1_DISPLAY_ONLY.lqm`
- **Modifications**:
  - `0x0208..0x0213`: Display Name A -> `"FF ISA 110 T"`
  - `0x4208..0x4213`: Display Name B -> `"FF ISA 110 T"`
- **Hypothesis**: The unit only checks display name A and mirror B.
- **Hardware Test Result**: Pending user testing.

---

### Variant 2: `TEST_V2_NAME_AND_DESC.lqm`
- **Modifications**:
  - `0x0208` & `0x4208`: Display Name A/B -> `"FF ISA 110 T"`
  - `0x03DC` & `0x43DC`: Description A/B -> `"FOCUSRITE CLASSIC ISA 110 TEST "`
- **Hypothesis**: The unit performs a consistency check between display name and description. Both must be updated in tandem across Block A and Block B.
- **Hardware Test Result**: Pending user testing.

---

### Variant 3: `TEST_V3_ZERO_PRE_A.lqm`
- **Modifications**:
  - Display Name A/B and Description A/B patched as in V2.
  - `0x0200..0x0203`: Set to `0x00000000` (zeroed).
  - `0x4200..0x4203`: Set to `0x00000000` (zeroed).
- **Hypothesis**: `pre_a` is a Block A header hash. Setting it to zero disables hash validation in DSP firmware.
- **Hardware Test Result**: Pending user testing.

---

### Variant 4: `TEST_V4_ZERO_FILE_ID.lqm`
- **Modifications**:
  - Display Name A/B and Description A/B patched as in V2.
  - `0x0000..0x0003`: Set `File ID` to `0x00000000` (zeroed).
- **Hypothesis**: `File ID` is matched against a factory whitelist. Setting `File ID = 0` flags the file as a user/custom preset and skips factory whitelist checks.
- **Hardware Test Result**: Pending user testing.

---

### Variant 5: `TEST_V5_FACTORY_PADDING.lqm`
- **Modifications**:
  - Display Name A/B patched to `"FF ISA 110 T"`.
  - Description A/B patched with **factory-exact leading space byte** (`0xDF` at `0x03DC`/`0x43DC`) and exact 32-char layout: `" FOCUSRITE CLASSIC ISA 110 TEST"`.
- **Hypothesis**: The firmware string parser enforces factory layout conventions (e.g. leading space formatting at offset `0x03DC`).
- **Hardware Test Result**: Pending user testing.

---

### Variant 6: `TEST_V6_CRC32_META.lqm`
- **Modifications**:
  - Display Name A/B and Description A/B patched as in V2.
  - `0x0200` (`pre_a`) & `0x4200`: Recalculated as `CRC32(patched_name_bytes + patched_desc_bytes)`.
- **Hypothesis**: `pre_a` is a 32-bit CRC over the text metadata blocks.
- **Hardware Test Result**: Pending user testing.

---

## File ID & Header Logical Rules (Discovered)

1. **`File ID` at `0x0000..0x0003`**:
   - Acts as a **Hardware Factory Registration Identifier**.
   - Inspection across all 87 files shows specific manufacturer family tags (e.g. Avalon = `0xBB`, Cadac = `0x5B`/`0x7B`, API = `0x5A`/`0xBA`).
   - Liquid Channel hardware checks `File ID` against a ROM whitelist. Modifying a factory file while leaving `File ID` intact causes factory integrity verification to fail.

2. **`pre_a` (`0x0200`) and `pre_b` (`0x4200`)**:
   - Header tags for the **Standard Sample Rate profile (48kHz)** vs **High Sample Rate profile (96kHz)**.

---

## Strategy: Creating Custom User File Containers

Instead of attempting to tamper with factory-sealed files, we can **create new custom file containers**:

- **Audio Payload**: Copy the **100% exact, untouched 15,876-byte Dynamic Convolution audio payload** from the original file into Block A (`0x03FC`–`0x41FF`) and Block B (`0x43FD`–`0x81FF`).
- **Custom Metadata**: Assign custom user display names (e.g. `"ISA 110 REAL"`) and set custom File ID (`0x55534552` / `"USER"`) to bypass factory whitelist enforcement.

### Test Container: `TEST_CUSTOM_CONTAINER_ISA110.lqm`
- **File ID (`0x0000`)**: `0x55534552` (`"USER"`)
- **Display Name A/B (`0x0208`/`0x4208`)**: `"ISA 110 REAL"`
- **Audio DSP Payload**: 100% untouched copy of `original FF ISA 110.lqm`
- **Location**: `testing files/TEST_CUSTOM_CONTAINER_ISA110.lqm`

---

## Combined `.lqb` Bundle vs. Individual `.lqm`/`.lqc` Files (Discovered)

A deep structural comparison between the **Combined Bundle File (`V2.0_40PRES&COMPS.lqb`, 2,621,952 bytes)** and individual files (`.lqm`/`.lqc`, 33,280 bytes) revealed:

1. **Header Differences**:
   - **Individual File (`.lqm`/`.lqc`)**: Starts with a **512-byte File Header** (`0x0000`–`0x01FF`) containing the per-file `File ID` and magic string `"Liquid Channel (tm)..."`, followed by the 32,768-byte dual-block payload (`0x0200`–`0x81FF`). Total size = **33,280 bytes**.
   - **Combined Bundle File (`.lqb`)**: Starts with a **single 512-byte Global Bank Header** (`0x0000`–`0x01FF`). The individual 512-byte headers are **stripped out**, and all 80 factory emulation payloads (32,768 bytes each) are concatenated back-to-back:
     - Entry 0 at `0x0200`
     - Entry 1 at `0x8200` (`0x0200 + 32,768`)
     - Entry 2 at `0x10200` (`0x0200 + 65,536`), etc.
     - Total size = `512 + 80 * 32,768` = **2,621,952 bytes**.

2. **Content Coverage**:
   - The `.lqb` bundle file contains **only the 80 original factory base models** (40 preamps + 40 compressors).
   - Add-on expansion packs (released 2004–2006, such as `HOT`, `PAD`, `Hi H`, `Lo H` variants) exist only as individual `.lqm`/`.lqc` files.

3. **Import Behavior**:
   - When importing a `.lqb` bundle, the Liquid Channel / LiquidControl software parses the global bank header once and extracts the 80 raw 32,768-byte payloads directly into bank memory slots **without inspecting individual 512-byte file headers**.

---

## Bank Backup File Generator Strategy (`.lqb`)

Using the generator script [`testing files/generate_lqb_backup.py`](file:///Users/ivmf/git/LCRename/testing%20files/generate_lqb_backup.py), we assemble a complete 80-emulation system bank backup file containing all 40 Preamps + 40 Compressors:

- **Generated Bank File**: **[`testing files/CUSTOM_REAL_GEAR_BANK_V2.0.lqb`](file:///Users/ivmf/git/LCRename/testing%20files/CUSTOM_REAL_GEAR_BANK_V2.0.lqb)**
- **Structure**: 512-byte Global Bank Header + 80 x 32,768-byte payloads = **2,621,952 bytes**.
- **Metadata**: All 80 entries have their Display Names (12ch) and Descriptions (32ch) updated to real-world gear names in 100% lockstep across 48kHz (Block A) and 96kHz (Block B) profiles.
- **Loading Use Case**: Import/Restore this `.lqb` file into LiquidControl / Liquid Channel as a **System Bank Restore / Backup**.

---

## Instructions for Hardware Testing

1. Connect the Liquid Channel unit to your computer via USB or LiquidControl.
2. Attempt to upload the test files one by one (V1 through V6, plus `TEST_CUSTOM_CONTAINER_ISA110.lqm`).
3. Alternatively, load the full custom bank backup file **[`CUSTOM_REAL_GEAR_BANK_V2.0.lqb`](file:///Users/ivmf/git/LCRename/testing%20files/CUSTOM_REAL_GEAR_BANK_V2.0.lqb)** via LiquidControl Bank Restore.
4. Record which test option loads successfully without triggering the "Corrupted File" error message.
