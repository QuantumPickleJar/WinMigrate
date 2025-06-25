import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import time
import logging

from utils import programs

from utils.logger import get_logger
from utils.permissions import copy_with_permissions

logger = get_logger(__name__)

def launch_gui() -> None:
    """Launch the GUI mode of the application."""
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

        
    def choose_and_transfer() -> None:
        src = filedialog.askopenfilename(title="Select Source File", parent=root)
        if not src:
            return
        dst = filedialog.asksaveasfilename(title="Select Destination", parent=root)
        if not dst:
            return

        start = time.time()

    def update(copied: int, total: int) -> None:
            percent = copied / total * 100 if total else 100
            progress['value'] = percent
            logger.debug("Copied %s/%s bytes", copied, total)

        success = copy_with_permissions(src, dst, cli=False, root=root, progress_cb=update)
        duration = time.time() - start
        if success:
            messagebox.showinfo("Transfer", f"Completed in {duration:.1f}s. See log for details.", parent=root)
        else:
            messagebox.showerror("Transfer", "Operation failed or canceled. See log for details.", parent=root)

    tk.Button(frame, text="Transfer File", width=20, command=choose_and_transfer).pack(pady=5)
    tk.Button(frame, text="Generate Program Report", width=20, command=generate_report_gui).pack(pady=5)
    tk.Label(frame, text="(Functionality coming soon)").pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    launch_gui()
