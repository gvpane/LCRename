"""
Focusrite Liquid Channel emulation renamer.
Edits the display name embedded in .lqm / .lqc files.

Format notes (reverse-engineered):
  - File size: always 33280 bytes
  - Magic at 0x000C: b"Liquid Channel (tm) file format"
  - Name field: 12 bytes at 0x0208 AND 0x4208, each byte XOR'd with 0xFF
  - Padding: 0xDF fills unused characters (space ^ 0xFF)
  - First 4 bytes: per-file ID, NOT a checksum - safe to leave untouched
"""

import os
import sys
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

MAGIC = b"Liquid Channel (tm) file format"
MAGIC_OFFSET = 0x000C
FILE_SIZE = 33280
NAME_OFFSETS = (0x0208, 0x4208)
NAME_LEN = 12
XOR_KEY = 0xFF
PAD_BYTE = 0xDF  # space ^ 0xFF

EXTENSIONS = (".lqm", ".lqc")


# ---------- file I/O ----------

def is_valid_lq_file(data: bytes) -> tuple[bool, str]:
    if len(data) != FILE_SIZE:
        return False, f"Wrong size: {len(data)} bytes (expected {FILE_SIZE})"
    if data[MAGIC_OFFSET: MAGIC_OFFSET + len(MAGIC)] != MAGIC:
        return False, "Missing Liquid Channel magic bytes"
    # Both name copies should match
    n1 = data[NAME_OFFSETS[0]: NAME_OFFSETS[0] + NAME_LEN]
    n2 = data[NAME_OFFSETS[1]: NAME_OFFSETS[1] + NAME_LEN]
    if n1 != n2:
        return False, "Name copies at 0x0208 and 0x4208 do not match"
    return True, "OK"


def decode_name(data: bytes) -> str:
    raw = data[NAME_OFFSETS[0]: NAME_OFFSETS[0] + NAME_LEN]
    chars = []
    for b in raw:
        decoded = b ^ XOR_KEY
        if decoded == (PAD_BYTE ^ XOR_KEY):  # space
            chars.append(" ")
        elif 0x20 <= decoded <= 0x7E:
            chars.append(chr(decoded))
        else:
            chars.append("?")
    return "".join(chars).rstrip()


def encode_name(name: str) -> bytes:
    if len(name) > NAME_LEN:
        raise ValueError(f"Name too long: max {NAME_LEN} characters")
    result = bytearray(NAME_LEN)
    for i in range(NAME_LEN):
        if i < len(name):
            c = ord(name[i])
            if c < 0x20 or c > 0x7E:
                raise ValueError(f"Character '{name[i]}' is not printable ASCII")
            result[i] = c ^ XOR_KEY
        else:
            result[i] = PAD_BYTE
    return bytes(result)


def patch_file(path: str, new_name: str, backup: bool = True) -> str:
    with open(path, "rb") as f:
        data = bytearray(f.read())

    ok, reason = is_valid_lq_file(bytes(data))
    if not ok:
        raise ValueError(f"File validation failed: {reason}")

    encoded = encode_name(new_name)
    for offset in NAME_OFFSETS:
        data[offset: offset + NAME_LEN] = encoded

    # Verify round-trip
    decoded = decode_name(bytes(data))
    if decoded.strip() != new_name.strip():
        raise RuntimeError(f"Round-trip check failed: got '{decoded}'")

    if backup:
        shutil.copy2(path, path + ".bak")

    with open(path, "wb") as f:
        f.write(data)

    return path + ".bak" if backup else ""


# ---------- GUI ----------

class App(tk.Tk):
    def __init__(self, directory: str = ""):
        super().__init__()
        self.title("Liquid Channel Emulation Renamer")
        self.resizable(True, True)
        self.minsize(700, 420)

        self.directory = tk.StringVar(value=directory)
        self.backup_var = tk.BooleanVar(value=True)
        self.files: list[dict] = []

        self._build_ui()
        if directory:
            self._scan()

    def _build_ui(self):
        # Top bar: directory picker
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Folder:").pack(side=tk.LEFT)
        ttk.Entry(top, textvariable=self.directory, width=55).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Browse…", command=self._browse).pack(side=tk.LEFT)
        ttk.Button(top, text="Scan", command=self._scan).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(top, text="Create .bak backup", variable=self.backup_var).pack(side=tk.RIGHT)

        # Table
        cols = ("file", "current_name", "new_name", "status")
        frame = ttk.Frame(self, padding=8)
        frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("file",         text="File")
        self.tree.heading("current_name", text="Name in file (current)")
        self.tree.heading("new_name",     text="New name  (max 12 chars)")
        self.tree.heading("status",       text="Status")
        self.tree.column("file",         width=220)
        self.tree.column("current_name", width=150, anchor=tk.CENTER)
        self.tree.column("new_name",     width=170, anchor=tk.CENTER)
        self.tree.column("status",       width=120, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", self._on_double_click)

        # Bottom bar
        bot = ttk.Frame(self, padding=8)
        bot.pack(fill=tk.X)
        self.status_label = ttk.Label(bot, text="Double-click a row to edit its name.")
        self.status_label.pack(side=tk.LEFT)
        ttk.Button(bot, text="Apply all changes", command=self._apply_all).pack(side=tk.RIGHT)

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.directory.get() or ".")
        if d:
            self.directory.set(d)
            self._scan()

    def _scan(self):
        d = self.directory.get()
        if not d or not os.path.isdir(d):
            messagebox.showerror("Error", "Please choose a valid folder first.")
            return

        self.files.clear()
        for row in self.tree.get_children():
            self.tree.delete(row)

        found = 0
        errors = 0
        for fname in sorted(os.listdir(d)):
            if not fname.lower().endswith(EXTENSIONS):
                continue
            path = os.path.join(d, fname)
            try:
                with open(path, "rb") as f:
                    data = f.read()
                ok, reason = is_valid_lq_file(data)
                if not ok:
                    status = f"SKIP: {reason}"
                    current = "—"
                    errors += 1
                else:
                    current = decode_name(data)
                    status = "ready"
                    found += 1
                entry = {"path": path, "fname": fname, "current": current,
                         "new": "", "status": status}
                self.files.append(entry)
                self.tree.insert("", tk.END, iid=str(len(self.files) - 1),
                                 values=(fname, current, "", status))
            except Exception as e:
                self.tree.insert("", tk.END, values=(fname, "—", "", f"ERROR: {e}"))
                errors += 1

        self.status_label.config(
            text=f"Found {found} valid file(s)" + (f", {errors} skipped." if errors else "."))

    def _on_double_click(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        idx = int(iid)
        entry = self.files[idx]
        if entry["status"].startswith(("SKIP", "ERROR")):
            messagebox.showwarning("Skipped", entry["status"])
            return

        win = tk.Toplevel(self)
        win.title("Edit name")
        win.resizable(False, False)
        win.grab_set()

        ttk.Label(win, text=f"File: {entry['fname']}", padding=10).grid(
            row=0, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(win, text=f"Current name: \"{entry['current']}\"", padding=(10, 0, 10, 6)).grid(
            row=1, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(win, text="New name (max 12 chars):").grid(row=2, column=0, padx=10, sticky=tk.W)

        var = tk.StringVar(value=entry["new"] or entry["current"])
        entry_w = ttk.Entry(win, textvariable=var, width=18)
        entry_w.grid(row=2, column=1, padx=10, pady=6)
        entry_w.select_range(0, tk.END)
        entry_w.focus()

        counter = ttk.Label(win, text="12 / 12")
        counter.grid(row=3, column=1, padx=10, sticky=tk.W)

        def _update_counter(*_):
            n = len(var.get())
            counter.config(text=f"{n} / 12",
                           foreground="red" if n > 12 else "black")
        var.trace_add("write", _update_counter)
        _update_counter()

        def _ok():
            new = var.get()
            if len(new) == 0:
                messagebox.showerror("Error", "Name cannot be empty.", parent=win)
                return
            if len(new) > 12:
                messagebox.showerror("Error", f"Name is {len(new)} characters — max is 12.", parent=win)
                return
            try:
                encode_name(new)  # validate chars
            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=win)
                return
            entry["new"] = new
            entry["status"] = "pending"
            self.tree.item(iid, values=(entry["fname"], entry["current"], new, "pending"))
            win.destroy()

        ttk.Button(win, text="OK", command=_ok).grid(row=4, column=1, padx=10, pady=10, sticky=tk.E)
        ttk.Button(win, text="Cancel", command=win.destroy).grid(
            row=4, column=0, padx=10, pady=10, sticky=tk.W)
        win.bind("<Return>", lambda _: _ok())
        win.bind("<Escape>", lambda _: win.destroy())

    def _apply_all(self):
        pending = [(i, e) for i, e in enumerate(self.files) if e["status"] == "pending"]
        if not pending:
            messagebox.showinfo("Nothing to do", "No files have pending renames.")
            return

        msg = f"Apply {len(pending)} rename(s)?"
        if self.backup_var.get():
            msg += "\n\nA .bak backup will be created for each file."
        if not messagebox.askyesno("Confirm", msg):
            return

        ok_count = 0
        for idx, entry in pending:
            iid = str(idx)
            try:
                patch_file(entry["path"], entry["new"], backup=self.backup_var.get())
                entry["current"] = entry["new"]
                entry["new"] = ""
                entry["status"] = "done ✓"
                self.tree.item(iid, values=(entry["fname"], entry["current"], "", "done ✓"))
                ok_count += 1
            except Exception as e:
                entry["status"] = f"FAILED: {e}"
                self.tree.item(iid, values=(entry["fname"], entry["current"],
                                            entry["new"], entry["status"]))

        self.status_label.config(text=f"{ok_count} / {len(pending)} file(s) renamed successfully.")


def main():
    start_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    app = App(directory=start_dir)
    app.mainloop()


if __name__ == "__main__":
    main()
