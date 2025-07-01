import tkinter as tk
from tkinter import filedialog, messagebox

from cli.cli_main import transfer
from utils.logger import get_logger

logger = get_logger(__name__)

def launch_gui() -> None:
    """Launch the GUI mode of the application."""
    logger.info("Launching GUI")
    root = tk.Tk()
    root.title("WinMigrate - Transfer Method Selection")

    def select_method(method: str) -> None:
        logger.info("Selected transfer method: %s", method)
        src_dir = filedialog.askdirectory(parent=root, title="Select source directory")
        if not src_dir:
            return
        dst_dir = filedialog.askdirectory(parent=root, title="Select destination directory")
        if not dst_dir:
            return
        transfer(src_dir, dst_dir)
        messagebox.showinfo(
            "Transfer Complete",
            f"Transferred files from {src_dir} to {dst_dir}",
            parent=root,
        )

    tk.Label(root, text="Select Transfer Method").pack(pady=10)

    methods = ["USB Drive", "Network", "External HDD"]
    for method in methods:
        tk.Button(
            root,
            text=method,
            width=20,
            command=lambda m=method: select_method(m),
        ).pack(pady=5)

    tk.Label(root, text="(Functionality coming soon)").pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    launch_gui()
