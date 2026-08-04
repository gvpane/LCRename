# Liquid Channel Binary Format — Research Findings

## Confirmed File Structure

Every `.lqm` / `.lqc` file is exactly **33280 bytes**, split into two independent blocks (A and B).

| Offset | Len | Field | Notes |
|--------|-----|-------|-------|
| `0x0000` | 4 | Block A file_id | Unique per file. Not a simple checksum. |
| `0x000C` | ~55 | Magic string | `Liquid Channel (tm) file format (c) Sintefex...` |
| `0x0200` | 4 | Block A hash/pre | **Likely a hash of Block A data. Different from Block B hash.** |
| `0x0204` | 4 | File type tag | `FF FF FD FF` = preamp (`.lqm`), `FD FF FF FF` = compressor (`.lqc`) |
| `0x0208` | 12 | Display name A | XOR 0xFF, space-padded with `0xDF` |
| `0x03DC` | 32 | Description A | XOR 0xFF, space-padded with `0xDF` |
| `0x4000` | 4 | Block B file_id | Different from Block A file_id |
| `0x4200` | 4 | Block B hash/pre | **Different from Block A hash.** |
| `0x4204` | 4 | File type tag copy | Same value as `0x0204` |
| `0x4208` | 12 | Display name B | Must match `0x0208` exactly |
| `0x43DC` | 32 | Description B | Must match `0x03DC` exactly |

**XOR encoding:** each byte = `(char_code) XOR 0xFF`. Space padding = `0xDF` (= `0x20 XOR 0xFF`).

**Key insight:** Block A and Block B are NOT mirrors of each other at the header level. `file_id` and `hash/pre` differ between blocks. Only the name and description fields need to match.

---

## Algorithm for Renaming

To rename a file without corruption:
1. Patch `0x0208` — 12-byte display name (XOR encoded)
2. Patch `0x4208` — 12-byte display name copy (must match)
3. Patch `0x03DC` — 32-byte description (XOR encoded)
4. Patch `0x43DC` — 32-byte description copy (must match)
5. **Recompute** `0x0200` (Block A hash) — algorithm unknown, see Open Questions
6. **Recompute** `0x4200` (Block B hash) — algorithm unknown, see Open Questions

Step 5 and 6 are blocking — we cannot reliably rename without knowing the hash algorithm.

---

## Hardware Test Log

| # | File | What was changed | Result |
|---|------|-----------------|--------|
| 1 | `PATCHED_TEST FF ISA 110.lqm` | All 4 name+desc fields patched. `pre_a`/`pre_b` left unchanged from original. | **CORRUPTED** — device reported "may be corrupted" |
| 2 | `PATCHED_TEST2_ZERO_PRE FF ISA 110.lqm` | All 4 name+desc fields patched. `pre_a` (0x0200) and `pre_b` (0x4200) zeroed to `0x00000000`. | **PENDING — not yet tested on hardware** |

---

## What We Ruled Out

- **0x0204 is NOT a checksum** — it is a fixed file-type discriminator tag.
- **Standard hash algorithms do NOT match `pre_a`/`pre_b`**: tested CRC32, CRC32C, Adler32, FNV-1a, djb2, byte-sum, XOR-fold, brute-force range scan over `0x0200–0x4300`.
- **The description field at `0x03DC` was the missing patch** — earlier tools only patched 2 of 4 name fields, which is why the original rename tool caused corruption.
- **Git LF→CRLF warning does NOT affect `.lqm` files** — only `.py` scripts are affected; binaries are opened in `rb`/`wb` mode.

---

## Open Questions (ranked by priority)

1. **What algorithm produces `pre_a` / `pre_b`?**
   - Zeroing test (Test #2) will tell us if the device validates these or skips them when zero.
   - If validation is skippable by zeroing → the rename tool can zero them as a workaround.
   - If not → need to reverse-engineer the Sintefex firmware or find the algorithm by statistical analysis.

2. **Are `file_id` fields (`0x0000`, `0x4000`) validated?**
   - Currently unchanged in all tests. If Test #2 still fails, try zeroing these too.

3. **Is `pre_a` a hash of Block A audio data (`0x0214–0x3FFF`), or of metadata only?**
   - Comparing similar files (e.g. `COPY CAT 2` vs `COPY CAT 3`) shows `pre_a` differs even when audio data is nearly identical — suggests it includes the name/description bytes.

---

## Files in `testing files\`

| File | Purpose |
|------|---------|
| `original FF ISA 110.lqm` | Clean original — ground truth |
| `PATCHED_TEST FF ISA 110.lqm` | Test 1: all 4 fields patched, hashes unchanged → CORRUPTED |
| `PATCHED_TEST2_ZERO_PRE FF ISA 110.lqm` | Test 2: all 4 fields patched, hashes zeroed → PENDING |
| `make_test_patch.py` | Creates Test 1 file |
| `make_test_patch2.py` | Creates Test 2 file |
| `check_block_b_header.py` | Confirmed Block A/B headers are independent |
| `check_desc_mirror.py` | Confirmed `0x03DC` == `0x43DC` in all originals |
| `checksums.py` | Comprehensive hash algorithm testing (all failed) |
| `analyze.py` | Multi-file binary analysis, generates `file_format_analysis.txt` |
| `analyze_lqb2.py` | Scans the `.lqb` bundle file |

---

## Next Hardware Test

**Load `PATCHED_TEST2_ZERO_PRE FF ISA 110.lqm` onto the Focusrite Liquid Channel.**

- If device shows `FF ISA 110 T` **without** corruption → zeroing `pre_a`/`pre_b` works as a workaround. Update `lqm_rename.py` to zero both hash fields when renaming.
- If device **still shows corruption** → `file_id` fields may also be validated. Create Test 3: zero `0x0000` and `0x4000` as well.
