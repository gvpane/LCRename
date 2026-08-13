# LCRename

LCRename is a specialized tool built for renaming and manipulating replica emulation files (`.lqm` and `.lqc`) designed for the **Focusrite Liquid Channel** and **Sintefex Liquid 4Pre** hardware units.

## The Problem
Manually renaming or modifying the display names of these replica files using a hex editor inevitably leads to the `LiquidControl` software or the hardware unit rejecting the file with a "The file may be corrupted" error. This is because the files utilize a complex proprietary format that includes:
- Bitwise obfuscation across the payload.
- Extremely strict string length and space-padding constraints.
- Multiple hidden cryptographic checksum validations, including undocumented checksums for specific data blocks and a master File ID checksum.

## The Solution
`LCRename.py` completely bypasses these limitations by automating the mathematical operations required to safely edit the files. It handles the de-obfuscation, strict memory padding, and recalculates all three proprietary checksum algorithms perfectly, allowing you to create customized replica files that load seamlessly into the hardware.

### Features
* Modifies both the Display Name and Description embedded within the replica files.
* Automatically recalculates the `pre_a` (Block A) and `pre_b` (Block B) checksums.
* Automatically recalculates the Master File ID Checksum over the unobfuscated payload.
* Automatically handles obfuscation and de-obfuscation of the file payload.

## Usage
`LCRename.py` requires Python 3. It can be run from the command line:

```bash
python3 LCRename.py <input_file> <output_file> --name "NEW NAME" --desc "NEW DESCRIPTION"
```

### Constraints:
* `--name`: Maximum of **12 characters**.
* `--desc`: Maximum of **32 characters**.

The script will handle all required space-padding automatically.

## Included Files & Directories

* `final_replicas/`: Contains over 80 factory replicas that have already been batch-processed. Their internal display names and descriptions have been cleaned up and properly checksum-validated.
* `docs/`: Contains original PDF user manuals, preamp details, and compressor documentation for the Liquid Channel.
* `findings.md`: A complete, comprehensive technical breakdown of the reverse-engineered `.lqm` and `.lqc` file format. Read this if you are interested in the mathematical formulas, offsets, and cryptographic constants discovered during the development of this tool.
