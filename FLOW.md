
# WinMigrate – User Interaction Flow

This document describes the expected flow of user interaction in both CLI and GUI modes.

---

## 🖥️ CLI Mode Flow

1. **Startup:** User launches `winmigrate.exe` or `python main.py`
2. **Mode Detection:** CLI is used by default unless `--gui` is passed
3. **User Prompts:**
   - Select transfer method: USB / Network / Nextcloud
   - Select source/destination directory
   - Confirm file size estimate vs available space
4. **Transfer Begins:**
   - Progress is logged to screen and file
   - Hash verifier checks integrity
5. **Completion:**
   - Summary printed to CLI
   - Optional program report generated

---

## 🪟 GUI Mode Flow

1. **Launch:** User runs with `--gui` or separate GUI executable
2. **Initial Screen:**
   - Transfer method selection
3. **Setup Phase:**
   - File picker dialog
   - Nextcloud linking (if chosen)
4. **Transfer Execution:**
   - Progress bars update in real-time
   - Pause / resume / cancel available
5. **Post-Transfer:**
   - Hash verification summary
   - Viewable report of actions

---

## 🗺️ Visual Interaction Flow (Mermaid)

```mermaid
flowchart TD
    A[Start WinMigrate] --> B{GUI or CLI?}
    B -- CLI --> C1[Prompt for method]
    C1 --> C2[Select files/folders]
    C2 --> C3[Check space and confirm]
    C3 --> C4[Begin transfer]
    C4 --> C5[Show progress + logs]
    C5 --> C6[Verify with hashes]
    C6 --> D[Done]

    B -- GUI --> G1[Open method selector]
    G1 --> G2[File picker / Nextcloud link]
    G2 --> G3[Check space and confirm]
    G3 --> G4[Transfer with GUI updates]
    G4 --> G5[Progress bar + logs panel]
    G5 --> G6[Hash verify + summary]
    G6 --> D
```