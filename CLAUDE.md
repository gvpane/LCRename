# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal backup and tooling repository for the **Focusrite Liquid Channel** — a discontinued hardware channel strip that uses Dynamic Convolution to emulate vintage preamps and compressors. The original factory emulations shipped with fictional/obfuscated names for copyright reasons (e.g. "THE GUV", "CLASS A 2A"). This repo contains those emulations renamed to their real gear names, plus a GUI tool to do further renaming.

## Running the rename tool

```
python lqm_rename.py
```

Opens a tkinter GUI. Point it at the folder containing `.lqm`/`.lqc` files, double-click a row to edit its name, then "Apply all changes". Backups (`.bak`) are created by default.

## .lqm / .lqc binary format (reverse-engineered)

Every emulation file is exactly **33280 bytes**. Structure:

| Offset | Length | Content |
|--------|--------|---------|
| `0x0000` | 4 | Per-file unique ID (not a checksum — safe to ignore) |
| `0x000C` | 31 | Magic: `Liquid Channel (tm) file format (c) Sintefex...` |
| `0x0208` | 12 | Display name, each byte XOR'd with `0xFF` |
| `0x4208` | 12 | Exact duplicate of the name field — **both must be patched together** |

Padding for unused name characters: `0xDF` (= space `0x20` XOR `0xFF`).

**Name constraints:** max 12 printable ASCII characters (0x20–0x7E). The `.lqb` bundle file (`V2.0_40PRES&COMPS.lqb`) has a different format — do not treat it as an individual emulation.

## File naming conventions

- Base name: real gear name, e.g. `NEVE 1073.lqm`
- `HOT` suffix: driven-hard / hot-input variant (not a temperature — intentional)
- `PAD` suffix: padded/attenuated input variant
- `Hø` / `Lø` / `Mø` suffix: high/low/mid impedance variant
- `DRV` suffix: driven variant
- `.lqm` = preamp emulation, `.lqc` = compressor emulation

## PDFs

The `Preamps_*.pdf` and `Compressors_*.pdf` files are the authoritative fictional→real name mapping source. The dated PDFs (`July_2004`, `January_2005`, etc.) document emulation packs added after the initial factory set of 40 preamps + 40 compressors.
