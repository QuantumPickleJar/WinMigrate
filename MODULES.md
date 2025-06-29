# WinMigrate – Modules Overview

This document outlines the major modules in the WinMigrate project and their responsibilities.

---

## 📁 `main.py`
- **Purpose:** Entry point for the application. Parses arguments and dispatches to GUI or CLI modes.

## 📁 `cli/cli_main.py`
- **Purpose:** CLI interface controller. Handles user prompts, path selections, and invokes transfer logic.

## 📁 `gui/gui_main.py`
- **Purpose:** Launches the GUI version of the tool. Manages UI components for method selection, progress display, etc.

## 📁 `utils/logger.py`
- **Purpose:** Sets up shared logging across CLI and GUI modes. Configurable verbosity.

## 📁 `transfers/transfer_manager.py` *(if applicable)*
- **Purpose:** Orchestrates file transfers (local, networked, or Nextcloud). Handles retries and error states.

## 📁 `cloud/nextcloud_uploader.py`
- **Purpose:** Handles authenticated WebDAV communication with Nextcloud servers. Uses chunked upload and resumable transfer logic.

## 📁 `reports/program_scanner.py`
- **Purpose:** Scans installed programs and outputs markdown reports, optionally checking for reinstallation links.

## 📄 `FLOW.md` — *Describes the user interaction flow*

> Explains the user’s journey through the app from entry point to completion.


---

## 🗺️ Module Interaction Flow (Mermaid)

```mermaid
graph TD
    main[main.py] --> argsCheck{--gui?}
    argsCheck -- yes --> gui[gui_main.py]
    argsCheck -- no --> cli[cli_main.py]

    cli --> logger
    gui --> logger

    cli --> transferManager
    gui --> transferManager

    transferManager --> cloud[Nextcloud Uploader]
    transferManager --> fs[Filesystem Handler]
    transferManager --> verifier[Hash Verifier]

    cli --> reportGen[Program Scanner]
