import tkinter as tk
from tkinter import ttk

from utils.logger import get_logger

logger = get_logger(__name__)


def launch_gui() -> None:
    """Launch the GUI mode of the application."""
    logger.info("Launching GUI")
    root = tk.Tk()
    root.title("WinMigrate - Transfer Method Selection")

    ttk.Label(root, text="Select Transfer Method").pack(pady=10)

    selected = tk.StringVar(value="usb")

    def show_middleman_info(*_args: object) -> None:
        if selected.get() == "middleman":
            space_lbl.pack(pady=(10, 0))
            size_lbl.pack(pady=(0, 10))
        else:
            space_lbl.pack_forget()
            size_lbl.pack_forget()

    methods = [
        ("usb", "Use external medium (USB)", "Transfer files using a USB drive."),
        ("middleman", "Use middleman device", "Connect both PCs through an intermediate device."),
        ("network", "Use Wi-Fi / Ethernet (local network)", "Transfer directly over your local network."),
    ]

    for value, title, desc in methods:
        frame = ttk.Frame(root)
        frame.pack(fill="x", pady=5, padx=10)
        ttk.Radiobutton(frame, text=title, variable=selected, value=value, command=show_middleman_info).pack(anchor="w")
        ttk.Label(frame, text=desc, wraplength=300).pack(anchor="w", padx=20)

    space_lbl = ttk.Label(root, text="Available space on destination: --")
    size_lbl = ttk.Label(root, text="Estimated size of selected files: --")

    show_middleman_info()

    def continue_action() -> None:
        logger.info("Selected transfer method: %s", selected.get())
        ttk.Label(root, text="Next screen not yet implemented").pack(pady=10)

    ttk.Button(root, text="Continue", command=continue_action).pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    launch_gui()
