import os
import json
import threading
import time
import tkinter as tk

from tkinter import ttk, filedialog, messagebox
from utils.logger import get_logger, configure_logger
from utils import programs
from utils.permissions import copy_with_permissions
from utils.config import load_config
from utils.transfer_control import TransferControl
from utils.restore import generate_restore_script
from typing import Callable
import logging

logger = get_logger(__name__)


def _path_size(path: str) -> int:
    """Return size of a file or directory in bytes."""
    if os.path.isdir(path):
        total = 0
        for root, _, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
        return total
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def select_items(parent: tk.Tk) -> list[str] | None:
    """Open a dialog to select multiple files and folders."""
    dialog = tk.Toplevel(parent)
    dialog.title("Select Items")
    paths: list[str] = []

    listbox = tk.Listbox(dialog, width=60, selectmode=tk.EXTENDED)
    listbox.pack(padx=10, pady=5, fill="both", expand=True)

    size_var = tk.StringVar(value="Total size: 0 bytes")
    tk.Label(dialog, textvariable=size_var).pack(pady=2)

    def _update_size() -> None:
        total = sum(_path_size(p) for p in paths)
        size_var.set(f"Total size: {total} bytes")

    def _add_files() -> None:
        files = filedialog.askopenfilenames(parent=dialog)
        for f in files:
            if f and f not in paths:
                paths.append(f)
                listbox.insert(tk.END, f)
        _update_size()

    def _add_folder() -> None:
        folder = filedialog.askdirectory(parent=dialog)
        if folder and folder not in paths:
            paths.append(folder)
            listbox.insert(tk.END, folder)
            _update_size()

    def _remove_selected() -> None:
        sel = list(listbox.curselection())
        for index in reversed(sel):
            item = listbox.get(index)
            paths.remove(item)
            listbox.delete(index)
        _update_size()

    def _save_preset() -> None:
        fp = filedialog.asksaveasfilename(
            parent=dialog,
            defaultextension=".json",
            filetypes=[("Preset", "*.json"), ("Backup Job", "*.bakjob")],
        )
        if fp:
            try:
                with open(fp, "w", encoding="utf-8") as f:
                    json.dump(paths, f, indent=2)
            except Exception as exc:
                messagebox.showerror("Error", str(exc), parent=dialog)

    def _load_preset() -> None:
        fp = filedialog.askopenfilename(
            parent=dialog,
            filetypes=[("Preset", "*.json"), ("Backup Job", "*.bakjob")],
        )
        if not fp:
            return
        try:
            with open(fp, "r", encoding="utf-8") as f:
                items = json.load(f)
            paths.clear()
            listbox.delete(0, tk.END)
            for item in items:
                paths.append(item)
                listbox.insert(tk.END, item)
            _update_size()
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=dialog)

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="Add Files", command=_add_files).pack(side="left", padx=2)
    tk.Button(btn_frame, text="Add Folder", command=_add_folder).pack(side="left", padx=2)
    tk.Button(btn_frame, text="Remove", command=_remove_selected).pack(side="left", padx=2)
    tk.Button(btn_frame, text="Load Preset", command=_load_preset).pack(side="left", padx=2)
    tk.Button(btn_frame, text="Save Preset", command=_save_preset).pack(side="left", padx=2)

    result: list[str] | None = []

    def _ok() -> None:
        nonlocal result
        result = paths.copy()
        dialog.destroy()

    def _cancel() -> None:
        nonlocal result
        result = None
        dialog.destroy()

    action_frame = tk.Frame(dialog)
    action_frame.pack(pady=5)
    tk.Button(action_frame, text="OK", width=10, command=_ok).pack(side="left", padx=5)
    tk.Button(action_frame, text="Cancel", width=10, command=_cancel).pack(side="left", padx=5)

    dialog.transient(parent)
    dialog.grab_set()
    parent.wait_window(dialog)
    return result


def launch_gui() -> None:
    """Launch the GUI mode of the application."""
    config = load_config(None)
    level = getattr(logging, config.verbosity.upper(), logging.INFO)
    configure_logger(level=level, log_path=config.log_path)
    logger.info("Launching GUI")
    root = tk.Tk()
    root.title("WinMigrate - Transfer Method Selection")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    tk.Label(frame, text="Select Transfer Method").pack(pady=10)

    methods = ["USB Drive", "Network", "External HDD"]
    for method in methods:
        tk.Button(frame, text=method, width=20).pack(pady=5)

    progress = ttk.Progressbar(frame, length=300)
    progress.pack(pady=5, fill="x")

    control = TransferControl()

    btn_frame = tk.Frame(frame)
    btn_frame.pack(pady=5)
    pause_btn = tk.Button(btn_frame, text="Pause", state="disabled")
    resume_btn = tk.Button(btn_frame, text="Resume", state="disabled")
    cancel_btn = tk.Button(btn_frame, text="Cancel", state="disabled")
    pause_btn.pack(side="left", padx=5)
    resume_btn.pack(side="left", padx=5)
    cancel_btn.pack(side="left", padx=5)

    def pause_transfer() -> None:
        control.pause.set()
        pause_btn.config(state="disabled")
        resume_btn.config(state="normal")
        status_var.set("Paused")

    def resume_transfer() -> None:
        control.pause.clear()
        pause_btn.config(state="normal")
        resume_btn.config(state="disabled")
        status_var.set("Resuming...")

    def cancel_transfer() -> None:
        control.cancel.set()
        pause_btn.config(state="disabled")
        resume_btn.config(state="disabled")
        cancel_btn.config(state="disabled")
        status_var.set("Canceling...")

    pause_btn.config(command=pause_transfer)
    resume_btn.config(command=resume_transfer)
    cancel_btn.config(command=cancel_transfer)

    status_var = tk.StringVar(value="")
    status_label = tk.Label(frame, textvariable=status_var)
    status_label.pack(pady=2)
    
    log_text = tk.Text(frame, height=10, width=50, state="disabled")
    log_text.pack(pady=5)

    class TextHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            msg = self.format(record)
            log_text.configure(state="normal")
            log_text.insert(tk.END, msg + "\n")
            log_text.see(tk.END)
            log_text.configure(state="disabled")

    text_handler = TextHandler()
    text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(text_handler)

    def generate_report_gui() -> None:
        out_dir = filedialog.askdirectory(title="Select Output Directory", parent=root)
        if not out_dir:
            return
        path = programs.generate_report(out_dir)
        messagebox.showinfo("Report", f"Report generated at {path}", parent=root)

    def restore_wizard() -> None:
        preset = filedialog.askopenfilename(
            title="Select Preset", parent=root, filetypes=[("Preset", "*.json")]
        )
        if not preset:
            return
        try:
            with open(preset, "r", encoding="utf-8") as f:
                sources = json.load(f)
            if not isinstance(sources, list):
                raise ValueError("Invalid preset file")
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=root)
            return
        backup_root = filedialog.askdirectory(title="Select Backup Root", parent=root)
        if not backup_root:
            return
        program_json = filedialog.askopenfilename(
            title="Select Program JSON (optional)",
            parent=root,
            filetypes=[("JSON", "*.json"), ("All", "*")],
        )
        script_path = filedialog.asksaveasfilename(
            title="Save Restore Script",
            defaultextension=".ps1",
            filetypes=[("PowerShell", "*.ps1")],
            parent=root,
        )
        if not script_path:
            return
        pairs = [
            (s, os.path.join(backup_root, os.path.basename(s.rstrip(os.sep))))
            for s in sources
        ]
        generate_restore_script(pairs, script_path, program_json or None)
        messagebox.showinfo(
            "Restore Script",
            f"Script saved to {script_path}. Review before running.",
            parent=root,
        )

    def choose_and_transfer() -> None:
        sources = select_items(root)
        if not sources:
            return
        dst_root = filedialog.askdirectory(title="Select Destination Directory", parent=root)
        if not dst_root:
            return

        control.pause.clear()
        control.cancel.clear()
        start = time.time()
        pause_btn.config(state="normal")
        cancel_btn.config(state="normal")
        resume_btn.config(state="disabled")
        status_var.set("Transferring...")

        total_size = sum(_path_size(p) for p in sources)
        copied_total = 0

        def make_update(start_offset: int) -> Callable[[int, int], None]:
            def _update(copied: int, total: int) -> None:
                percent = (start_offset + copied) / total_size * 100 if total_size else 100
                progress['value'] = percent
                logger.debug("Copied %s/%s bytes", start_offset + copied, total_size)
            return _update

        def retry_cb(seconds: int) -> None:
            status_var.set(f"Retrying in {seconds}s...")
            root.update_idletasks()

        def run() -> None:
            nonlocal copied_total
            success = True
            for src in sources:
                if control.cancel.is_set():
                    success = False
                    break
                if os.path.isdir(src):
                    base = os.path.basename(src.rstrip(os.sep))
                    for r, _, files in os.walk(src):
                        for f in files:
                            if control.cancel.is_set():
                                success = False
                                break
                            src_file = os.path.join(r, f)
                            rel = os.path.relpath(src_file, src)
                            dst = os.path.join(dst_root, base, rel)
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            file_size = os.path.getsize(src_file)
                            cb = make_update(copied_total)
                            if not copy_with_permissions(
                                src_file,
                                dst,
                                cli=False,
                                root=root,
                                progress_cb=cb,
                                retry_cb=retry_cb,
                                timeout=config.timeout,
                                chunk_size=config.chunk_size,
                                control=control,
                            ):
                                success = False
                                break
                            copied_total += file_size
                        if not success:
                            break
                else:
                    dst = os.path.join(dst_root, os.path.basename(src))
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    file_size = os.path.getsize(src)
                    cb = make_update(copied_total)
                    if not copy_with_permissions(
                        src,
                        dst,
                        cli=False,
                        root=root,
                        progress_cb=cb,
                        retry_cb=retry_cb,
                        timeout=config.timeout,
                        chunk_size=config.chunk_size,
                        control=control,
                    ):
                        success = False
                        break
                    copied_total += file_size

            duration = time.time() - start
            def finish() -> None:
                pause_btn.config(state="disabled")
                resume_btn.config(state="disabled")
                cancel_btn.config(state="disabled")
                status_var.set("")
                if success:
                    messagebox.showinfo(
                        "Transfer",
                        f"Completed in {duration:.1f}s. See log for details.",
                        parent=root,
                    )
                else:
                    messagebox.showerror(
                        "Transfer",
                        "Operation failed or canceled. See log for details.",
                        parent=root,
                    )
            root.after(0, finish)

        threading.Thread(target=run, daemon=True).start()

    tk.Button(frame, text="Transfer File", width=20, command=choose_and_transfer).pack(pady=5)

    tk.Button(frame, text="Generate Program Report", width=20, command=generate_report_gui).pack(pady=5)

    tk.Button(frame, text="Restore Wizard", width=20, command=restore_wizard).pack(pady=5)


    root.mainloop()


if __name__ == "__main__":
    launch_gui()
