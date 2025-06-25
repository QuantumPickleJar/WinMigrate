import tkinter as tk
from tkinter import filedialog, messagebox

from utils.logger import get_logger
from utils.permissions import copy_with_permissions

logger = get_logger(__name__)

def launch_gui() -> None:
    """Launch the GUI mode of the application."""
    logger.info("Launching GUI")
    root = tk.Tk()
    root.title("WinMigrate - Transfer Method Selection")

    tk.Label(root, text="Select Transfer Method").pack(pady=10)

    methods = ["USB Drive", "Network", "External HDD"]
    for method in methods:
        tk.Button(root, text=method, width=20).pack(pady=5)

    def choose_and_transfer() -> None:
        src = filedialog.askopenfilename(title="Select Source File", parent=root)
        if not src:
            return
        dst = filedialog.asksaveasfilename(title="Select Destination", parent=root)
        if not dst:
            return
        copy_with_permissions(src, dst, cli=False, root=root)
        messagebox.showinfo("Transfer", "Operation completed. Check logs for details.", parent=root)

    tk.Button(root, text="Transfer File", width=20, command=choose_and_transfer).pack(pady=5)

    tk.Label(root, text="(Functionality coming soon)").pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    launch_gui()
