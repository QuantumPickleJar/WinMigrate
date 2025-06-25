import tkinter as tk

from utils.logger import get_logger

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

    tk.Label(root, text="(Functionality coming soon)").pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    launch_gui()
