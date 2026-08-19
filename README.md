# LCRename & Liquid Channel Replica Modifier

LCRename is a specialized tool suite built for renaming and manipulating replica emulation files (`.lqm` and `.lqc`) designed for the **Focusrite Liquid Channel** and **Sintefex Liquid 4Pre** hardware units. 

## The Problem
Manually renaming or modifying the display names of these replica files using a hex editor inevitably leads to the `LiquidControl` software or the hardware unit rejecting the file with a "The file may be corrupted" error. This is because the files utilize a complex proprietary format that includes:
- Bitwise obfuscation across the payload.
- Extremely strict string length and space-padding constraints.
- Multiple hidden cryptographic checksum validations, including undocumented checksums for specific data blocks and a master File ID checksum.

## The Solution
The `LCRename` suite completely bypasses these limitations by automating the mathematical operations required to safely edit the files. It handles the de-obfuscation, strict memory padding, and recalculates all three proprietary checksum algorithms perfectly, allowing you to create customized replica files that load seamlessly into the hardware.

---

## 🖥️ Graphical User Interface (LCRename_GUI.py)

We highly recommend using the included Desktop Application for the best experience. It features an authentic, hardware-accurate "Liquid Channel" metallic UI design.

### Features
* **Batch Processing:** Load multiple `.lqm` and `.lqc` files at once.
* **Hardware Auto-Suggestions 💡:** The app features a built-in database (`hardware_mapping.json`) of over 200 factory hardware emulations. Click the **Idea (Lightbulb)** icon next to any file to instantly auto-fill its true hardware counterpart name and description!
* **Safe Exporting:** Ensures your original source files are never overwritten.
* **Authentic Styling:** Features Light and Dark metallic themes styled exactly like the physical Focusrite hardware unit (complete with Power Blue, +48V Red, and Signal Green UI elements).

### Usage
Run the GUI using Python 3 and PySide6:
```bash
pip install PySide6
python LCRename_GUI.py
```

---

## 💻 Command Line Interface (LCRename.py)

If you prefer scripting or batch automation, you can use the core Python library directly.

```bash
# Read existing metadata
python LCRename.py input.lqm --read

# Modify and save as a new file
python LCRename.py input.lqm output.lqm --name "NEW NAME" --desc "NEW DESCRIPTION"
```

### Constraints:
* `--name`: Maximum of **12 characters**.
* `--desc`: Maximum of **32 characters**.

*The script will handle all required space-padding automatically.*

---

## Included Files & Directories

* `LCRename_GUI.py`: The PySide6 Desktop Application.
* `LCRename.py`: The core command-line utility and cryptographic engine.
* `hardware_mapping.json`: A static database mapping over 200 obfuscated replica names to their true physical hardware models.
* `final/`: Contains factory replicas that have already been batch-processed.
* `original/` & `renamed_by_hardware/`: Raw testing and original source files.
* `docs/`: Contains original PDF user manuals, preamp details, and compressor documentation for the Liquid Channel.
* `findings.md`: A complete, comprehensive technical breakdown of the reverse-engineered `.lqm` and `.lqc` file format. Read this if you are interested in the mathematical formulas, offsets, and cryptographic constants discovered during the development of this tool.
