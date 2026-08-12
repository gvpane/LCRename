# Testing Files Directory Layout

This folder contains all research, analysis, specifications, and test candidates for the **Focusrite Liquid Channel** binary reverse-engineering project.

---

## Directory Structure

```
testing files/
├── findings.md                    # Complete research findings, logs, & hypotheses
├── file_structure_spec.txt        # Binary file structure & memory offset layout
├── test_variants/                # ACTIVE HARDWARE TEST CANDIDATE FILES
│   ├── TEST_V1_DISPLAY_ONLY.lqm       (Display Name patched only)
│   ├── TEST_V2_NAME_AND_DESC.lqm      (Display Name + Description patched)
│   ├── TEST_V3_ZERO_PRE_A.lqm         (Name + Desc + Zeroed pre_a)
│   ├── TEST_V4_ZERO_FILE_ID.lqm       (Name + Desc + Zeroed File ID)
│   ├── TEST_V5_FACTORY_PADDING.lqm    (Name + Desc with exact factory leading space)
│   ├── TEST_V6_CRC32_META.lqm         (Name + Desc + CRC32 pre_a calculation)
│   ├── TEST_CUSTOM_CONTAINER_ISA110.lqm (Custom User Preset Container)
│   └── CUSTOM_REAL_GEAR_BANK_V2.0.lqb   (Full 80-emulation Real Gear Bank Backup)
├── originals/                     # Clean, untouched factory reference files
│   ├── original FF ISA 110.lqm
│   ├── original FF GREEN 5.lqm
│   ├── V2.0_40PRES&COMPS.lqb
│   └── ... (additional reference files)
├── scripts/                       # Analysis, verification, & generator scripts
│   ├── create_hardware_test_suite.py
│   ├── create_custom_file_from_audio_data.py
│   ├── generate_lqb_backup.py
│   └── ... (research & checksum scripts)
└── legacy_tests/                  # Archived legacy patch attempts & test code
    ├── PATCHED_TEST FF ISA 110.lqm
    └── make_test_patch.py
```

---

## How to Test on Hardware

1. For individual file testing: Upload files from `test_variants/` one by one.
2. For full bank restore testing: Load `test_variants/CUSTOM_REAL_GEAR_BANK_V2.0.lqb` via LiquidControl Bank Restore.
3. Record hardware test results in `findings.md`.
